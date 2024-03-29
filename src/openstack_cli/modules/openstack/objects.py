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
from calendar import timegm
from datetime import datetime
from enum import Enum
from io import RawIOBase
from time import strptime
from typing import List, Dict, Tuple, Union, Optional

from openstack_cli.modules.apputils.json2obj import SerializableObject
from openstack_cli.modules.openstack.api_objects import EndpointCatalog, ComputeServerInfo, DiskImageInfo, \
  ComputeFlavorItem, NetworkItem, SubnetItem, VMCreateServer, VMCreateNetworksItem, VMCreateNewFileItem, \
  VMCreateServerItem, LoginResponse


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


EndpointVersions = {
  EndpointTypes.network.value: "/v2.0",
  EndpointTypes.identity.value: "/v3",
  EndpointTypes.image.value: "/v2"
}

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


class ServerState(Enum):
  active = "ACTIVE"
  building = "BUILDING"
  build = "BUILD"
  deleted = "DELETED"
  error = "ERROR"
  paused = "PAUSED"
  rescued = "RESCUED"
  resized = "RESIZED"
  shelved = "SHELVED"
  shelved_offloaded = "SHELVED_OFFLOADED"
  soft_deleted = "SOFT_DELETED"
  stopped = "STOPPED"
  suspended = "SUSPENDED"
  shutoff = "SHUTOFF"

  @classmethod
  def from_str(cls, state: str = "ERROR"):
    """
    :rtype ServerState
    """
    items = {v.value: v for k, v in cls.__dict__.items() if k[:1] != "_" and not isinstance(v, classmethod)}
    if state in items:
      return items[state]

    raise ValueError(f"Unknown '{state}' state")


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
    self.__project_name = conf.project.name if login_response.token.project is None else login_response.token.project.name
    self.__project_id = conf.project.id if login_response.token.project is None else login_response.token.project.id

  def get_endpoint(self, endpoint_type: EndpointTypes) -> str or None:
    if endpoint_type in self.__endpoint_cache:
      return self.__endpoint_cache[endpoint_type]

    endpoints = [e for e in self._endpoints if e.type == endpoint_type.value]
    for el in endpoints:
      for e in el.endpoints:
        if e.region == self.__region and e.interface == self.__interface:
          if el.type in EndpointVersions:
            e.url += EndpointVersions[el.type]

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

  @property
  def raw(self) -> ComputeFlavorItem:
    return self.__orig

  @property
  def name(self):
    return self.__orig.name

  @property
  def ram(self):  # bytes
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


class OpenStackVMInfo(object):
  def __init__(self):
    self.name: Optional[str] = None
    self.id: Optional[str] = None
    self.status: ServerState = ServerState.error
    self.state: ServerPowerState = ServerPowerState.nostate
    self.created: Optional[datetime] = None
    self.updated: Optional[datetime] = None
    self.owner_id: Optional[str] = None
    self.net_name: Optional[str] = None
    self.ip_address: Optional[str] = None
    self.image_id: Optional[str] = None
    self.image: Optional[DiskImageInfo] = None
    self.key_name: Optional[str] = None
    self.cluster_name: Optional[str] = None
    self._flavor: Optional[OSFlavor] = None
    self._original: Optional[ComputeServerInfo] = None
    self._net: OSNetworkItem = OSNetworkItem()

  @property
  def flavor(self) -> OSFlavor:
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


class OpenStackQuotaType(Enum):
  CPU_CORES = "CPU_CORES"
  RAM_GB = "RAM_GB"
  INSTANCES = "INSTANCES"
  NET_PORTS = "NET_PORTS"
  KEYPAIRS = "KEYPAIRS"
  SERVER_GROUPS = "SERVER_GROUPS"
  RAM_MB = "RAM_MB"


class OpenStackQuotaItem(object):
  def __init__(self, name: OpenStackQuotaType, max_count: int, used: int):
    self.__name = name
    self.__max_count = max_count
    self.__used = used

  @property
  def name(self) -> str:
    return self.__name.value

  @property
  def type(self) -> OpenStackQuotaType:
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
    self.__metrics: Dict[OpenStackQuotaType, Tuple[Union[int,float], Union[int,float]]] = {}
    self.__max_metric_length = 0

  def add(self, metric_name: OpenStackQuotaType, max_count: int or float, used: int or float):
    self.__metrics[metric_name] = max_count, used,
    if self.__max_metric_length < len(metric_name.value):
      self.__max_metric_length = len(metric_name.value)

  @property
  def max_metric_len(self):
    return self.__max_metric_length

  def get_quota(self, _t: OpenStackQuotaType) -> Tuple[Union[int,float], Union[int, float]]:
    if _t in self.__metrics:
      return self.__metrics[_t]

    return None

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
    self.__servers_updated: bool = False

  def update_from_servers(self, servers: List[OpenStackVMInfo]):
    if self.__servers_updated:
      return

    for server in servers:
      self.update_from_server(server)

    self.__servers_updated = True

  def update_from_server(self, server: OpenStackVMInfo):
    if server.owner_id in self.__users_db:
      return

    if server.name:
      uname, _, _ = server.name.partition('-')
      self.__users_db[server.owner_id] = uname

  @property
  def users(self) -> Dict[str, str]:
    return dict(self.__users_db.items())

  def add_user(self, user_id: str, user_name: str):
    if user_id not in self.__users_db:
      self.__users_db[user_id] = user_name

  def get_user(self, user_id: str) -> Optional[str]:
    if user_id not in self.__users_db:
      return None

    return self.__users_db[user_id]

  def exists(self, user_id: str) -> bool:
    return user_id in self.__users_db

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

class OSNetworkItem(SerializableObject):
  name: str = ""
  status: str = False
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

  def enable_reservation_id(self):
    self.__vm.return_reservation_id = "True"
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

  def add_text_file(self, remote_path: str, value: Union[List[str],str]):
    f = VMCreateNewFileItem()
    f.path = remote_path
    f.contents = base64.b64encode(bytearray(
      value if isinstance(value, str) else "\n".join(value),
      encoding="UTF-8"
    )).decode("UTF-8")
    self.__vm.personality.append(f)
    return self

  def set_user_data(self, value: str):
    self.__vm.user_data = base64.b64encode(bytearray(value, encoding="UTF-8")).decode("UTF-8")
    return self

  def set_instances_count(self, count: int):
    self.__vm.min_count = self.__vm.max_count = str(count)
    return self

  def build(self):
    return VMCreateServer(server=self.__vm)


class OpenStackVM(object):
  __CLUSTER_NAME__ = re.compile("(?P<name>.*)-\\d+$", flags=re.IGNORECASE | re.MULTILINE)

  def __init__(self,
               servers: List[ComputeServerInfo],
               images: Dict[str, DiskImageInfo],
               flavors: Dict[str, OSFlavor],
               networks: OSNetwork,
               users: Optional[OpenStackUsers] = None
               ):
    self.__max_host_name_len = 0
    self.__max_domain_name_len = 0
    self.__items = []
    self.__n = 0
    # ToDo: do not hardcode net
    net: OSNetworkItem = [n for n in networks.items if n.name == "INTERNAL_NET"][0]

    if net and net.domain_name:
      self.__max_domain_name_len = len(net.domain_name)

    for server in servers:
      vm = OpenStackVMInfo()

      if self.__max_host_name_len < len(server.name):
        self.__max_host_name_len = len(server.name)

      vm._net = net
      vm._original = server
      vm.name = server.name
      vm.id = server.id
      vm.status = ServerState.from_str(server.status)
      try:
        vm.created = datetime.utcfromtimestamp(timegm(strptime(server.created, "%Y-%m-%dT%H:%M:%SZ")))
      except ValueError:
        vm.created = None
      try:
        vm.updated = datetime.utcfromtimestamp(timegm(strptime(server.updated, "%Y-%m-%dT%H:%M:%SZ")))
      except ValueError:
        vm.updated = None

      if server.addresses.keys():
        vm.net_name = list(server.addresses.keys())[0]
        vm.ip_address = server.addresses[vm.net_name][0].addr if server.addresses[vm.net_name] else "0.0.0.0"
      else:
        vm.net_name = "NOT SET"
        vm.ip_address = "0.0.0.0"

      vm.owner_id = server.user_id
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

      if users:
        users.update_from_server(vm)

  @property
  def items(self) -> List[OpenStackVMInfo]:
    return list(self.__items)

  @property
  def max_host_len(self):
    return self.__max_host_name_len

  @property
  def max_domain_len(self):
    return self.__max_domain_name_len

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
      s.append(f"Cluster: {vm.cluster_name}, vm name: {vm.name},"
               f" image: {vm.image.name}, ip: {vm.ip_address}, status: {vm.status}")

    return "\n".join(s)


class VMProject(SerializableObject):
  id: str = ""
  name: str = ""
  domain: str = ""


class AuthRequestType(Enum):
  SCOPED = 0
  UNSCOPED = 1


class AuthRequestBuilder(object):
  @classmethod
  def normal_login(cls, user: str, password: str) -> dict:
    return {
      "auth": {
        "identity": {
          "methods": ["password"],
          "password": {
            "user": {
              "name": user,
              "domain": {
                "id": "default"
              },
              "password": password
            }
          }
        }
      }
    }

  @classmethod
  def unscoped_login(cls, user: str, password: str) -> dict:
    return {
      "auth": {
        "identity": {
          "methods": ["password"],
          "password": {
            "user": {
              "name": user,
              "domain": {
                "id": "default"
              },
              "password": password
            }
          }
        },
        "scope": "unscoped"
      }
    }

  @classmethod
  def scoped_login(cls, user: str, password: str, project: VMProject) -> dict:
    return {
      "auth": {
        "identity": {
          "methods": ["password"],
          "password": {
            "user": {
              "name": user,
              "domain": {
                "id": project.domain
              },
              "password": password
            }
          }
        },
        "scope": {
          "project": {
            "id": project.id
          }
        }
      }
    }
