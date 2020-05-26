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

import re
from datetime import datetime
from enum import Enum
from time import strptime, mktime
from typing import List, Dict, Tuple, Iterable

from openstack_cli.modules.config import Configuration
from openstack_cli.modules.openstack import LoginResponse
from openstack_cli.modules.openstack.api_objects import EndpointCatalog, ComputeServerInfo, DiskImageInfo, \
  ComputeFlavorItem


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
  def from_int(cls, state: int = 0):
    """
    :rtype ServerPowerState
    """
    items = {v.value: v for k, v in cls.__dict__.items() if k[:1] != "_" and not isinstance(v, classmethod)}
    if state in items:
      return items[state]

    raise ValueError(f"Unknown '{state}' state")


class OpenStackEndpoints(object):
  def __init__(self, conf: Configuration, login_response: LoginResponse):
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
          self.__endpoint_cache[endpoint_type] = e.url
          if el.type == EndpointTypes.network.value:  # hack
            e.url += "/v2.0"
          elif el.type == EndpointTypes.identity.value:
            e.url += "/v3"
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

  @property
  def flavor(self) -> ComputeFlavorItem:
    return self._flavor


class OpenStackVM(object):
  __CLUSTER_NAME__ = re.compile("(?P<name>.*)-\\d+$", flags=re.IGNORECASE | re.MULTILINE)

  def __init__(self,
               servers: List[ComputeServerInfo],
               users: OpenStackUsers,
               images: Dict[str, DiskImageInfo],
               flavors: Dict[str, ComputeFlavorItem]
               ):
    self.__max_host_name_len = 0
    self.__items = []
    self.__n = 0

    for server in servers:
      vm = OpenStackVMInfo()

      if self.__max_host_name_len < len(server.name):
        self.__max_host_name_len = len(server.name)

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
