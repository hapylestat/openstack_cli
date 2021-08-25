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

from enum import Enum
from typing import Dict, List, Optional

from openstack_cli.modules.apputils.terminal import Console, TableColumn, TableOutput

from openstack_cli.modules.openstack import OpenStack, OpenStackVMInfo


class ValueHolder(object):
  def __init__(self, v_amount: int = 0, values: list = ()):
    if values and len(values) == v_amount:
      self.__values = values
    else:
      self.__values = [0] * v_amount


  def set_if_bigger(self, n: int or Enum[int], v):
    if isinstance(n, Enum):
      n = n.value

    if  v > self.__values[n]:
      self.__values[n] = v

  def set(self, n: int or Enum[int], v):
    if isinstance(n, Enum):
      n = n.value

    self.__values[n] = v

  def get(self, n: int or Enum[int]):
    if isinstance(n, Enum):
      n = n.value
    return self.__values[n]


def cluster_selector(ostack: OpenStack, name: str, own: bool = False) -> List[OpenStackVMInfo]:
  pass


def host_selector(ostack: OpenStack, name: str, node_index: Optional[int] = None, own: bool = False) -> OpenStackVMInfo:
  if name == "None":
    name = ""

  if name and node_index == -1:
    _name, _, _node_index = name.rpartition("-")

    try:
      node_index = int(_node_index)
      name = _name
    except (ValueError, TypeError):
      pass

  if "." in name:
    name, _ = name.split(".")

  search_result: Dict[str, List[OpenStackVMInfo]] = ostack.get_server_by_cluster(name, sort=True, only_owned=own)
  to = TableOutput(
    TableColumn("Cluster name", 40),
    print_row_number=True
  )
  if len(search_result.keys()) > 1:
    to.print_header()
    for cluster_name in search_result.keys():
      to.print_row(cluster_name)

    selection: int = Console.ask("Choose cluster from the list", int)
    try:
      name = list(search_result.keys())[selection:][0]
    except IndexError:
      raise ValueError("Wrong selection, please select item within an provided range")
  elif search_result:
    name = list(search_result.keys())[0]
  else:
    raise ValueError(f"No matching cluster matching pattern'{name}' found")

  nodes: List[OpenStackVMInfo] = search_result[name]
  if node_index == -1:
    if len(nodes) > 1:
      to = TableOutput(
        TableColumn("IP", 18),
        TableColumn("Host name", 40),

        print_row_number=True
      )
      to.print_header()
      for node in nodes:
        to.print_row(node.ip_address, node.fqdn)
      node_index: int = Console.ask("Choose host from the list", int)
      if node_index > len(nodes):
        raise ValueError("Wrong selection, please select item within an provided range")
    else:
      node_index = 0
  else:
    node_index -= 1    # the node name starts for 1, while list from 0

  try:
    return nodes[node_index]
  except IndexError:
    raise ValueError("Unknown host name, please check the name")
