#  Licensed to the Apache Software Foundation (ASF) under one or more
#  contributor license agreements.  See the NOTICE file distributed with
#  this work for additional information regarding copyright ownership.
#  The ASF licenses this file to You under the Apache License, Version 2.0
#  (the "License"); you may not use this file except in compliance with
#  the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from time import sleep

from openstack_cli.commands.list import print_cluster
from openstack_cli.core.output import StatusOutput, Console, TableOutput, TableColumn
from openstack_cli.modules.openstack import OpenStack, OpenStackVMInfo
from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo
from openstack_cli.modules.openstack.objects import ServerState


__module__ = CommandMetaInfo("up")
__args__ = __module__.get_arguments_builder() \
  .add_default_argument("name", str, "name of the cluster")\
  .add_default_argument("count", int, "amount of nodes")\
  .add_argument("flavor", str, "Host flavor", default="m1.large")\
  .add_argument("image", str, "VM OS to spin up", default="centos-761810")\
  .add_argument("key", str, "Key to use for login", default="")\
  .add_argument("password", str, "Password to use for login", default="")


def __init__(conf: Configuration, name: str, count: int, flavor: str, image: str, key: str, password: str):
  ostack = OpenStack(conf)

  def __filter(vm: OpenStackVMInfo) -> bool:
    __name, _, _ = str(vm.name).rpartition('-')
    return __name != name

  servers = ostack.get_server_by_cluster(name, True, filter_func=__filter)
  if servers:
    Console.print_warning(f"Cluster with name {name} already exists, instance would be not created")
    print_cluster(servers)
    return

  def __work_unit(x: OpenStackVMInfo) -> bool:
    while True:
      if x.status == ServerState.active:
        return True

      if x.status not in [ServerState.building, ServerState.build, ServerState.active]:
        return False

      sleep(1)
      x = ostack.get_server_by_id(x)

  image = list(ostack.get_image_by_alias(image))
  img_flavor = None
  if image:
    flavors = ostack.get_flavors(image[0])
    for fl in flavors:
      if fl.name == flavor:
        img_flavor = fl
        break

  _default_key = ostack.get_keypairs()[0] if ostack.get_keypairs() else None
  _key = _default_key if not key else ostack.get_keypair(name, _default_key)
  _pass = conf.default_vm_password if not password else password

  # == create nodes
  so = StatusOutput(__work_unit, pool_size=2)

  print("Asking for node creation....", end='')
  servers = ostack.create_instances(
    cluster_name=name,
    image=image[0],
    flavor=img_flavor,
    password=_pass,
    count=count,
    ssh_key=_key
  )

  if not servers:
    print('fail')
    so.check_issues(ostack.last_errors)
    return

  print("ok")
  so.start("Creating nodes ", objects=servers)
  if ostack.has_errors:
    so.check_issues(ostack.last_errors)
    return

  # == Configure nodes
  def __work_unit_waiter(x: OpenStackVMInfo) -> bool:
    tries: int = 0
    while tries < 200:
      log = ostack.get_server_console_log(x.id)
      for l in log:
        if "finished" in l or "login:" in l:
          return True

      sleep(2)
      tries += 1
    return False

  so = StatusOutput(__work_unit_waiter, pool_size=5)
  so.start("Configure nodes", servers)
  if ostack.has_errors:
    so.check_issues(ostack.last_errors)

  console = ostack.get_server_console_log(servers[0], grep_by="cloud-init")

  to = TableOutput(
    TableColumn("Name", 15),
    TableColumn("Value", 30)
  )

  to.print_header()

  for line in console:
    if "@users@" in line:
      users = line.split("@users@:")[1].strip().split(" ")
      to.print_row("User accounts", ",".join(users))

  to.print_row("Used key", _key.name if _key else "Not used")
  to.print_row("Used password", _pass)

