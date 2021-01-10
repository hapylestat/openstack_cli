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

from openstack_cli.modules.apputils.terminal.colors import Colors

from openstack_cli.commands.list import print_cluster
from openstack_cli.core.output import StatusOutput, Console, TableOutput, TableColumn
from openstack_cli.modules.openstack import OpenStack, OpenStackVMInfo
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo
from openstack_cli.modules.openstack.objects import ServerState


__module__ = CommandMetaInfo("up", "Deploys new cluster")
__args__ = __module__.arg_builder\
  .add_default_argument("name", str, "Name of the cluster")\
  .add_default_argument("count", int, "Amount of nodes")\
  .add_argument("flavor", str, "Host flavor", default="m1.large")\
  .add_argument("image", str, "VM OS to spin up", default="centos-761810")\
  .add_argument("key", str, "Key to use for login", default="")\
  .add_argument("password", str, "Password to use for login", default="")


def __init__(conf: Configuration, name: str, count: int, flavor: str, image: str, key: str, password: str):
  ostack = OpenStack(conf)

  def __filter(vm: OpenStackVMInfo) -> bool:
    return not str(vm.name).startswith(name)

  servers = ostack.get_server_by_cluster(name, True, filter_func=__filter)
  if servers:
    Console.print_warning(f"Cluster with name '{Colors.BRIGHT_WHITE.wrap(name)}' already exists, instance would be not be created")
    print_cluster(servers)
    return

  def __work_unit(x: OpenStackVMInfo) -> bool:
    while True:
      if x.status == ServerState.active:
        return True

      if x.status not in [ServerState.building, ServerState.build, ServerState.active]:
        return False

      sleep(2)
      #  ToDo: short term cache data by reservation_id
      x = ostack.get_server_by_id(x)

  with Console.status_context("Resolving cluster configuration"):
    image = list(ostack.get_image_by_alias(image))
    if not image:
      raise RuntimeError("Cannot resolve image name for the request")

    image = image[0]
    img_flavor = ostack.get_flavor(image, flavor)
    _default_key = ostack.get_keypairs()[0] if ostack.get_keypairs() else None
    _key = _default_key if not key else ostack.get_keypair(key, _default_key)
    _pass = conf.default_vm_password if not password else password

  # == create nodes

  so = StatusOutput(__work_unit, pool_size=2, additional_errors=ostack.last_errors)

  with Console.status_context("Asking for node creation"):
    servers = ostack.create_instances(
      cluster_name=name,
      image=image,
      flavor=img_flavor,
      password=_pass,
      count=count,
      ssh_key=_key
    )
    if not servers:
      so.check_issues()
      return

  so.start("Creating nodes ", objects=servers)

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

  so = StatusOutput(__work_unit_waiter, pool_size=5, additional_errors=ostack.last_errors)
  so.start("Configure nodes", servers)

  console = ostack.get_server_console_log(servers[0], grep_by="cloud-init")

  to = TableOutput(
    TableColumn("Name", 15),
    TableColumn("Value", 30)
  )

  to.print_header(custom_header="SUMMARY")

  for line in console:
    if "@users@" in line:
      users = line.split("@users@:")[1].strip().split(" ")
      to.print_row("Accounts", ",".join(users))

  to.print_row("Key", _key.name if _key else "Not used")
  to.print_row("Password", _pass)

