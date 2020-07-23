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

import base64
import re
from datetime import datetime
from enum import Enum
from io import RawIOBase
from time import strptime, mktime
from typing import List, Dict, Tuple

from openstack_cli.modules.json2obj import SerializableObject
from openstack_cli.modules.openstack import LoginResponse
from openstack_cli.modules.openstack.api_objects import EndpointCatalog, ComputeServerInfo, DiskImageInfo, \
  ComputeFlavorItem, NetworkItem, SubnetItem, VMCreateServer, VMCreateNetworksItem, VMCreateNewFileItem, \
  VMCreateServerItem


class EndpointTypes(Enum):
  dns = "dns"
  identity = "identity"
  placement = "placement"
  network = "network"
  volumev2 = "volumev2"
  orchestration = "orchestration"
  volumev3 = "volumev3"
  image = "image"
  compute = "compute"
  cloudformation = "cloudformation"
  load_balancer = "load-balancer"


class ImageStatus(Enum):
 """
 Doc: https://docs.openstack.org/api-ref/image/v2/?expanded=list-images-detail
 """
 queued = "queued"
 saving = "saving"
 active = "active"
 killed = "killed"
 deleted = "deleted"
 pending_delete = "pending_delete"
 deactivated = "deactivated"
 uploading = "uploading"
 importing = "importing"


class ServerPowerState(Enum):
  """
  https://docs.openstack.org/api-ref/compute/?expanded=list-servers-detailed-detail
  """
  nostate = 0
  running = 1
  paused = 3
  shutdown = 4
  crashed = 6
  suspended = 7

  @classmethod
  def stop_states(cls):
    """
    :rtype List[ServerPowerState]
    """
    return [cls.shutdown, cls.crashed, cls.suspended, cls.paused]

  @classmethod
  def from_int(cls, state: int = 0):
    """
    :rtype ServerPowerState
    """
    items = {v.value: v for k, v in cls.__dict__.items() if k[:1] != "_" and not isinstance(v, classmethod)}
    if state in items:
      return items[state]

    raise ValueError(f"Unknown '{state}' state")


class OpenStackEndpoints(object):
  def __init__(self, conf, login_response: LoginResponse):
    """
    :type conf openstack_cli.modules.config.Configuration
    """
    self._endpoints: List[EndpointCatalog] = login_response.token.catalog
    self.__interface = conf.interface
    self.__region = conf.region
    self.__endpoint_cache = {}
    self.__project_name = login_response.token.project.name
    self.__project_id = login_response.token.project.id

  def get_endpoint(self, endpoint_type: EndpointTypes) -> str or None:
    if endpoint_type in self.__endpoint_cache:
      return self.__endpoint_cache[endpoint_type]

    endpoints = [e for e in self._endpoints if e.type == endpoint_type.value]
    for el in endpoints:
      for e in el.endpoints:
        if e.region == self.__region and e.interface == self.__interface:
          if el.type == EndpointTypes.network.value:  # hack
            e.url += "/v2.0"
          elif el.type == EndpointTypes.identity.value:
            e.url += "/v3"

          self.__endpoint_cache[endpoint_type] = e.url
          return e.url
    return None

  @property
  def compute(self):
    return self.get_endpoint(EndpointTypes.compute)

  @property
  def image(self):
    return self.get_endpoint(EndpointTypes.image)

  @property
  def identity(self):
    return self.get_endpoint(EndpointTypes.identity)

  @property
  def network(self):
    return self.get_endpoint(EndpointTypes.network)

  @property
  def dns(self):
    return self.get_endpoint(EndpointTypes.dns)

  @property
  def project_name(self):
    return self.__project_name

  @property
  def project_id(self):
    return self.__project_id


class OpenStackQuotaItem(object):
  def __init__(self, name: str, max_count: int, used: int):
    self.__name = name
    self.__max_count = max_count
    self.__used = used

  @property
  def name(self):
    return self.__name

  @property
  def max_count(self):
    return self.__max_count

  @property
  def used(self):
    return self.__used

  @property
  def available(self):
    return self.max_count - self.used


class OpenStackQuotas(object):
  def __init__(self):
    # Max, Used, Available
    self.__metrics: Dict[str, Tuple[int or float, int or float]] = {}
    self.__max_metric_length = 0

  def add(self, metric_name: str, max_count: int or float, used: int or float):
    self.__metrics[metric_name] = (max_count, used)
    if self.__max_metric_length < len(metric_name):
      self.__max_metric_length = len(metric_name)

  @property
  def max_metric_len(self):
    return self.__max_metric_length

  def __iter__(self):
    self.__n = 0
    self.__keys = list(self.__metrics.keys())
    self.__values = list(self.__metrics.values())
    return self

  def __next__(self) -> OpenStackQuotaItem:
    if self.__n < len(self.__metrics.keys()):
      result = OpenStackQuotaItem(self.__keys[self.__n], *self.__values[self.__n])
      self.__n += 1
      return result
    else:
      raise StopIteration


class OpenStackUsers(object):
  def __init__(self, images: List[DiskImageInfo]):
    users_db = {}
    for image in images:
      if image.owner_user_name:
        users_db[image.user_id] = image.owner_user_name

    self.__users_db = users_db

  @property
  def users(self) -> Dict[str, str]:
    return dict(self.__users_db.items())

  def get_user(self, user_id: str) -> str or None:
    if user_id not in self.__users_db:
      return None

    return self.__users_db[user_id]


class OpenStackVMInfo(object):
  def __init__(self):
    self.name: str or None = None
    self.id: str or None = None
    self.status: str or None = None
    self.state: ServerPowerState = ServerPowerState.nostate
    self.created: datetime or None = None
    self.updated: datetime or None = None
    self.owner_id: str or None = None
    self.owner_name: str or None = None
    self.ip_address: str or None = None
    self.image_id: str or None = None
    self.image: DiskImageInfo or None = None
    self.key_name: str or None = None
    self.cluster_name: str or None = None
    self._flavor: ComputeFlavorItem or None = None
    self._original: ComputeServerInfo or None = None
    self._net: OSNetworkItem = OSNetworkItem()

  @property
  def flavor(self) -> ComputeFlavorItem:
    return self._flavor

  @property
  def original(self) -> ComputeServerInfo:
    return self._original

  @property
  def fqdn(self) -> str:
    return f"{self.name}.{self._net.domain_name}"

  @property
  def domain(self) -> str:
    return self._net.domain_name


class OSImageInfo(object):
  def __init__(self, name: str, ver: str, orig: DiskImageInfo):
    self.__name = name.strip()
    self.__ver = ver.strip()
    self.__orig = orig

  @property
  def name(self):
    return f"{self.__name} {self.__ver}"

  @property
  def size(self) -> int:
    return self.__orig.size

  @property
  def os_name(self):
    return self.__name

  @property
  def alias(self):
    return self.__name.lower() + "-" + self.__ver\
     .lower()\
     .replace(" ", "-")\
     .replace(".", "")\
     .replace("_", "")

  @property
  def version(self):
    return self.__ver

  @version.setter
  def version(self, value: str):
    self.__ver = value

  @property
  def base_image(self):
    return self.__orig

  @property
  def description(self):
    return f"Image {self.name}; ID: {self.__orig.id}"


class OSFlavor(SerializableObject):
  __orig: ComputeFlavorItem = None

  @classmethod
  def get(cls, orig: ComputeFlavorItem):
    """
    :rtype OSFlavor
    """
    return cls()._set_flavor(orig)

  def _set_flavor(self, orig: ComputeFlavorItem):
    """
    :rtype OSFlavor
    """
    self.__orig = orig
    return self

  def base_flavor(self) -> ComputeFlavorItem:
    return self.__orig

  @property
  def name(self):
    return self.__orig.name

  @property
  def ram(self):
    # originally provided in mb
    return self.__orig.ram * 1024 * 1024

  @property
  def vcpus(self):
    return self.__orig.vcpus

  @property
  def swap(self):
    return self.__orig.swap

  @property
  def disk(self):
    """
    :return Disk size in kilobytes
    """
    # this is provided in gb
    return self.__orig.disk * 1024 * 1024 * 1024

  @property
  def ephemeral_disk(self):
    """
    :return: ephemeral disk size in kilobytes
    """
    #  base value in GB, experimentally estimated
    return self.__orig.OS_FLV_EXT_DATA_ephemeral * 1024 * 1024 * 1024

  @property
  def sum_disk_size(self):
    return self.disk + self.ephemeral_disk

  @property
  def id(self):
    return self.__orig.id


class OSNetworkItem(SerializableObject):
  name: str = ""
  status: bool = False
  is_default: bool = False
  network_id: str = ""
  subnet_id: str = ""
  dns_nameservers: List[str] = []
  cidr: str = ""
  gateway_ip: str = ""
  enable_dhcp: bool = False
  domain_name: str = ""
  _orig_network: NetworkItem or None = None
  _orig_subnet: SubnetItem or None = None

  @property
  def orig_network(self) -> NetworkItem:
    return self._orig_network

  @property
  def orig_subnet(self) -> SubnetItem:
    return self._orig_subnet


class OSNetwork(SerializableObject):
  __networks: List[OSNetworkItem] = []
  __raw_subnets: Dict[str, SubnetItem] = {}
  __n: int = 0

  def parse(self, networks: List[NetworkItem], subnets: List[SubnetItem]):
    """
    :rtype  OSNetwork
    """
    self.__raw_subnets = {k.id: k for k in subnets}
    self.__n: int = 0
    for network in networks:
      n = OSNetworkItem()
      n.name = network.name
      n.status = network.status
      n.is_default = network.is_default
      n.network_id = network.id
      n.subnet_id = network.subnets[0] if network.subnets else None
      n.domain_name = network.dns_domain.strip(".") if network.dns_domain else network.dns_domain

      s: SubnetItem = self.__raw_subnets[n.subnet_id] if n.subnet_id in self.__raw_subnets else None

      if s:
        n.dns_nameservers = s.dns_nameservers
        n.cidr = s.cidr
        n.gateway_ip = s.gateway_ip
        n.enable_dhcp = s.enable_dhcp

      n._orig_subnet = s
      n._orig_network = network

      self.__networks.append(n)
    return self

  @property
  def items(self) -> List[OSNetworkItem]:
    return list(self.__networks)

  def __iter__(self):
    self.__n = 0
    return self

  def __next__(self) -> OSNetworkItem:
    if self.__n < len(self.__networks):
      result = self.__networks[self.__n]
      self.__n += 1
      return result
    else:
      raise StopIteration


class VMCreateBuilder(object):
  def __init__(self, name: str):
    self.__vm = VMCreateServerItem(name=name)
    self.__obj: VMCreateServer = VMCreateServer(server=self.__vm)

  def set_flavor(self, flavor: OSFlavor):
    self.__vm.flavorRef = flavor.id
    return self

  def set_image(self, image: DiskImageInfo):
    self.__vm.imageRef = image.id
    return self

  def set_admin_pass(self, admin_pass: str):
    self.__vm.adminPass = admin_pass
    return self

  def set_key_name(self, key_name: str):
    self.__vm.key_name = key_name
    return self

  def add_network(self, network: OSNetworkItem):
    self.__vm.networks.append(VMCreateNetworksItem(uuid=network.network_id))
    return self

  def add_binary_file(self, remote_path: str, stream: RawIOBase):
    f = VMCreateNewFileItem()
    f.path = remote_path
    f.contents = base64.b64encode(stream.read())
    self.__vm.personality.append(f)
    return self

  def add_text_file(self, remote_path: str, value: List[str] or str):
    f = VMCreateNewFileItem()
    f.path = remote_path
    f.contents = base64.b64encode(bytearray(
      value if isinstance(value, str) else "\n".join(value),
      encoding="UTF-8"
    )).decode("UTF-8")
    self.__vm.personality.append(f)
    return self

  def set_user_date(self, value: str):
    self.__vm.user_data = base64.b64encode(bytearray(value, encoding="UTF-8")).decode("UTF-8")
    return self

  def set_instances_count(self, count: int):
    self.__vm.min_count = self.__vm.max_count = str(count)
    return self

  def build(self):
    return self.__obj


class OpenStackVM(object):
  __CLUSTER_NAME__ = re.compile("(?P<name>.*)-\\d+$", flags=re.IGNORECASE | re.MULTILINE)

  def __init__(self,
               servers: List[ComputeServerInfo],
               users: OpenStackUsers,
               images: Dict[str, DiskImageInfo],
               flavors: Dict[str, ComputeFlavorItem],
               networks: OSNetwork
               ):
    self.__max_host_name_len = 0
    self.__items = []
    self.__n = 0
    # ToDo: do not hardcode net
    net: OSNetworkItem = [n for n in networks.items if n.name == "INTERNAL_NET"][0]

    for server in servers:
      vm = OpenStackVMInfo()

      if self.__max_host_name_len < len(server.name):
        self.__max_host_name_len = len(server.name)

      vm._net = net
      vm._original = server
      vm.name = server.name
      vm.id = server.id
      vm.status = server.status
      try:
        vm.created = datetime.utcfromtimestamp(mktime(strptime(server.created, "%Y-%m-%dT%H:%M:%SZ")))
      except ValueError:
        vm.created = None
      try:
        vm.updated = datetime.utcfromtimestamp(mktime(strptime(server.updated, "%Y-%m-%dT%H:%M:%SZ")))
      except ValueError:
        vm.updated = None
      vm.ip_address = server.addresses.INTERNAL_NET[0].addr if server.addresses.INTERNAL_NET else "0.0.0.0"
      vm.owner_id = server.user_id
      vm.owner_name = users.get_user(vm.owner_id)
      vm.image_id = server.image.id
      vm.image = images[vm.image_id] if vm.image_id in images else DiskImageInfo()
      vm.key_name = server.key_name
      vm.state = ServerPowerState.from_int(server.OS_EXT_STS_power_state)
      matches = re.match(self.__CLUSTER_NAME__, vm.name)
      if not matches:
        vm.cluster_name = vm.name
      else:
        try:
          vm.cluster_name = matches.group("name")
        except IndexError:
          vm.cluster_name = vm.name
      if server.flavor and server.flavor.id in flavors:
        vm._flavor = flavors[server.flavor.id]

      self.__items.append(vm)

  @property
  def items(self) -> List[OpenStackVMInfo]:
    return list(self.__items)

  @property
  def max_host_len(self):
    return self.__max_host_name_len

  def __iter__(self):
    self.__n = 0
    return self

  def __next__(self) -> OpenStackVMInfo:
    if self.__n < len(self.__items):
      result = self.__items[self.__n]
      self.__n += 1
      return result
    else:
      raise StopIteration

  def __str__(self):
    s = []
    for vm in self.__items:
      owner = vm.owner_name if vm.owner_name else vm.owner_id
      s.append(f"Cluster: {vm.cluster_name}, vm name: {vm.name},"
               f" image: {vm.image.name}, ip: {vm.ip_address}, owner: {owner}, status: {vm.status}")

    return "\n".join(s)
