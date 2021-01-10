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

from typing import List

from openstack_cli.core.output import TableOutput, TableColumn, TableStyle
from openstack_cli.modules.openstack import OpenStack
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo


__module__ = CommandMetaInfo("networks", "Shows available networks")

from openstack_cli.modules.openstack.objects import OSNetworkItem


def get_default_network(conf: Configuration, ostack: OpenStack, force: bool = False) -> OSNetworkItem:
  net: OSNetworkItem or None = conf.default_network

  if not net or force:
    net = print_networks(ostack, True)
    if net:
      conf.default_network = net

  return net


def print_networks(ostack: OpenStack, select: bool = False) -> OSNetworkItem or None:
  tbl = TableOutput(
    TableColumn("N.", 3),
    TableColumn("ID", 36),
    TableColumn("Zone", 10),
    TableColumn("Name", 20),
    TableColumn("CIDR", 15),
    TableColumn("Domain name", 30),
    TableColumn("DNS", 15),
    TableColumn("Active", 6),
    style=TableStyle.line_highlight
  )
  nets: List[OSNetworkItem] = sorted(ostack.networks, key=lambda x: x.name)

  tbl.print_header()
  counter: int = 0
  for net in nets:
    if len(net.dns_nameservers) > 1:
      dns_servers = net.dns_nameservers[:-1]
      for dns_ip in dns_servers:
        tbl.print_row("", "", "", "", "", "", dns_ip, "")

    tbl.print_row(
      str(counter),
      net.network_id,
      ",".join(net.orig_network.availability_zones),
      net.name,
      net.cidr,
      net.domain_name,
      ",".join(net.dns_nameservers[-1:]) if len(net.dns_nameservers) > 1 else ",".join(net.dns_nameservers),
      net.orig_network.status
    )
    counter += 1

  if select:
    a = input("Please select item:")
    try:
      return nets[int(a)]
    except ValueError:
      pass

  return None


def __init__(conf: Configuration):
  ostack = OpenStack(conf)
  print_networks(ostack)
