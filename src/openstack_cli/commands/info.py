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


from openstack_cli.core.output import TableOutput, TableColumn

from openstack_cli.core.colors import Colors, Symbols
from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo
from openstack_cli.modules.openstack import OpenStack


__module__ = CommandMetaInfo("info")
__args__ = __module__.get_arguments_builder() \
  .add_default_argument("search_pattern", str, "search query", default="")

from openstack_cli.modules.openstack.objects import ServerPowerState


def __init__(conf: Configuration, search_pattern: str, debug: bool):
  __run_ico = Symbols.PLAY.green()
  __pause_ico = Symbols.PAUSE.yellow()
  __stop_ico = Symbols.STOP.red()
  __state = {
    ServerPowerState.running: __run_ico,
    ServerPowerState.paused: __pause_ico
  }

  ostack = OpenStack(conf, debug=debug)
  clusters = ostack.get_server_by_cluster(search_pattern=search_pattern, sort=True)
  max_fqdn_len = ostack.servers.max_host_len + ostack.servers.max_domain_len + 5

  to = TableOutput(
    TableColumn("", 1, inv_ch=Colors.GREEN.wrap_len()),
    TableColumn("Host name", max_fqdn_len),
    TableColumn("Host IP", 16),
    TableColumn("SSH Key", 30),
    TableColumn("Network name", length=15)
  )

  to.print_header()
  for cluster_name, servers in clusters.items():
    servers = sorted(servers, key=lambda x: x.fqdn)
    for server in servers:
      to.print_row(
        __state[server.state] if server.state in __state else __stop_ico,
        server.fqdn,
        server.ip_address if server.ip_address else "0.0.0.0",
        server.key_name,
        server.net_name
      )
