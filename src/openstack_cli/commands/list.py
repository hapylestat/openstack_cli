# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
from typing import List, Dict

from openstack_cli.core.output import TableOutput, TableColumn

from openstack_cli.core.colors import Colors
from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo

from openstack_cli.modules.openstack import OpenStack
from openstack_cli.modules.openstack.objects import ServerPowerState, OpenStackVMInfo

__module__ = CommandMetaInfo("list")
__args__ = __module__.get_arguments_builder()\
  .add_default_argument("search_pattern", str, "search query", default="")


def get_lifetime(timestamp: datetime):
  now = datetime.utcnow()
  d = now - timestamp
  if 5 < d.days < 31:
    days = f"{Colors.YELLOW}{d.days}{Colors.RESET}"
  elif d.days > 31:
    days = f"{Colors.RED}{d.days}{Colors.RESET}"
  else:
    days = d.days
  hours = d.seconds / 3600
  minutes = (d.seconds / 60) - (hours * 60)

  return f"{int(hours)}h {int(minutes)}m" if days == 0 else f"{days} day(s)"


def print_cluster(servers: Dict[str, List[OpenStackVMInfo]]):
  __run_ico = f"{Colors.GREEN}► {Colors.RESET}"
  __pause_ico = f"{Colors.YELLOW}❚❚ {Colors.RESET}"
  __stop_ico = f"{Colors.RED}■ {Colors.RESET}"

  to = TableOutput(
    TableColumn("Cluster", length=40),
    TableColumn("VmType", length=20),
    TableColumn("Status", length=20, inv_ch=len(Colors.GREEN)*3+len(Colors.RESET)*3),
    TableColumn("Network name", length=15),
    TableColumn("Lifetime", length=10)
  )

  to.print_header()

  for cluster_name, _servers in servers.items():
    server = _servers[0]
    num_running: int = len([s for s in _servers if s.state == ServerPowerState.running])
    num_paused: int = len([s for s in _servers if s.state == ServerPowerState.paused])
    num_stopped: int = len(_servers) - num_running - num_paused

    to.print_row(
      cluster_name,
      server.flavor.name,
      f"{__run_ico}{num_running:<3}{__pause_ico}{num_paused:<3}{__stop_ico}{num_stopped:<3}",
      server.net_name,
      get_lifetime(server.created)
    )


def __init__(conf: Configuration, search_pattern: str):
  ostack = OpenStack(conf)
  clusters = ostack.get_server_by_cluster(search_pattern=search_pattern, sort=True)

  if search_pattern and len(clusters) == 0:
    print(f"Query '{search_pattern}' returned no match")
    return

  print_cluster(clusters)

