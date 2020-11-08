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

from openstack_cli.core.colors import Colors
from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo
from openstack_cli.modules.openstack import OpenStack


__module__ = CommandMetaInfo("info")
__args__ = __module__.get_arguments_builder() \
  .add_default_argument("search_pattern", str, "search query", default="")

from openstack_cli.modules.openstack.objects import ServerPowerState


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


def __init__(conf: Configuration, search_pattern: str, debug: bool):
  ostack = OpenStack(conf, debug=debug)
  clusters = ostack.get_server_by_cluster(search_pattern=search_pattern, sort=True)
  max_host_len = ostack.servers.max_host_len + 5
  max_fqdn_len = ostack.servers.max_host_len + ostack.servers.max_domain_len + 5

  print("{:1} {:<{}s} {:<{}s} {:<16} {:<5}".format(
    " " * 2,
    "  Cluster name", max_host_len,
    "  Host name", max_fqdn_len,
    "  Host IP",
    "  Uptime"
  ))
  print("{:1} {:<{}s} {:<{}s} {:<16} {:<5}".format(
    " " * 2,
    "-" * max_host_len, max_host_len,
    "-" * max_fqdn_len, max_fqdn_len,
    "-" * 16,
    "-" * 10))

  for cluster_name, servers in clusters.items():
    for server in servers:
      lifetime = get_lifetime(server.created)
      run_state = f"{Colors.RED}■ {Colors.RESET}"
      if server.state == ServerPowerState.running:
        run_state = f"{Colors.GREEN}► {Colors.RESET}"
      elif server.state == ServerPowerState.paused:
        run_state = f"{Colors.YELLOW}❚❚ {Colors.RESET}"

      print(" {:1} {:<{}s} {:<{}s} {:<16} {:<5}".format(
        run_state,
        server.cluster_name, max_host_len,
        server.fqdn, max_fqdn_len,
        server.ip_address if server.ip_address else "0.0.0.0",
        lifetime
      ))
