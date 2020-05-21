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
from typing import List, Dict, Tuple

from openstack_cli.modules.config import Configuration
from openstack_cli.modules.openstack import LoginResponse
from openstack_cli.modules.openstack.api_objects import EndpointCatalog


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
  nostate: int = 0
  running: int = 1
  paused: int = 3
  shutdown: int = 4
  crashed: int = 6
  suspended: int = 7

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
