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

from enum import Enum
from typing import Dict, List

from openstack_cli.modules.apputils.terminal import TableOutput, TableColumn

from openstack_cli.modules.openstack.objects import ServerPowerState, OpenStackVMInfo
from openstack_cli.modules.apputils.terminal.colors import Colors, Symbols
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo
from openstack_cli.modules.openstack import OpenStack
from openstack_cli.modules.utils import ValueHolder


__module__ = CommandMetaInfo("info", "Shows the detailed information about requested VMs")
__args__ = __module__.arg_builder\
  .add_default_argument("search_pattern", str, "Search query", default="") \
  .add_argument("own", bool, "Display only owned by user items", default=False) \
  .add_argument("showid", bool, "Display instances ID", default=False)


class WidthConst(Enum):
  max_fqdn_len = 0
  max_key_len = 1
  max_net_len = 2


def print_cluster(servers: Dict[str, List[OpenStackVMInfo]], vh: ValueHolder = None, ostack: OpenStack = None,
                  showid:bool = False):

  __run_ico = Symbols.PLAY.green()
  __pause_ico = Symbols.PAUSE.yellow()
  __stop_ico = Symbols.STOP.red()
  __state = {
    ServerPowerState.running: __run_ico,
    ServerPowerState.paused: __pause_ico
  }

  if vh is None:
    vh = ValueHolder(3, [50, 30, 15])

  columns = [
    TableColumn("", 1, inv_ch=Colors.GREEN.wrap_len()),
    TableColumn("Host name", vh.get(WidthConst.max_fqdn_len)),
    TableColumn("Host IP", 16),
    TableColumn("SSH Key", vh.get(WidthConst.max_key_len)),
    TableColumn("Network name", length=vh.get(WidthConst.max_net_len))
  ]
  if showid:
    columns.append(TableColumn("ID"))

  to = TableOutput(*columns)
  to.print_header()
  for cluster_name, servers in servers.items():
    servers = sorted(servers, key=lambda x: x.fqdn)
    for server in servers:
      _row = [
        __state[server.state] if server.state in __state else __stop_ico,
        server.fqdn,
        server.ip_address if server.ip_address else "0.0.0.0",
        server.key_name,
        server.net_name
      ]
      if showid:
        _row.append(server.id)
      to.print_row(*_row)

def __init__(conf: Configuration, search_pattern: str, debug: bool, own: bool, showid: bool):
  vh: ValueHolder = ValueHolder(3)
  def __fake_filter(s: OpenStackVMInfo):
    vh.set_if_bigger(WidthConst.max_fqdn_len, len(s.fqdn))
    vh.set_if_bigger(WidthConst.max_key_len, len(s.key_name))
    vh.set_if_bigger(WidthConst.max_net_len, len(s.net_name))
    return False

  ostack = OpenStack(conf, debug=debug)
  clusters = ostack.get_server_by_cluster(search_pattern=search_pattern, sort=True, only_owned=own,
                                          filter_func=__fake_filter)

  print_cluster(clusters, vh, ostack, showid=showid)


