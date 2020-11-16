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

from openstack_cli.core.output import StatusOutput, Console
from openstack_cli.modules.openstack import OpenStack, OpenStackVMInfo, ServerPowerState
from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo


__module__ = CommandMetaInfo("reboot")
__args__ = __module__.get_arguments_builder() \
  .add_default_argument("name", str, "name of the cluster or vm")\
  .add_argument("hard", bool, "hard reset the VM", default=False)


def __init__(conf: Configuration, name: str, hard: bool):
  ostack = OpenStack(conf)

  def __work_unit(value: OpenStackVMInfo) -> bool:
    return ostack.start_instance(value)

  so = StatusOutput(__work_unit, pool_size=5, additional_errors=ostack.last_errors)
  servers = ostack.get_server_by_cluster(
    name,
    sort=True,
    filter_func=lambda x: x.state in ServerPowerState.stop_states()
  )

  if not servers:
    print("No matches or already started")
    return

  if Console.confirm_operation("reboot", servers):
    flatten_servers = [server for server_pair in servers.values() for server in server_pair]

    so.start("Rebooting nodes", objects=flatten_servers)
  else:
    print("Aborted....")
