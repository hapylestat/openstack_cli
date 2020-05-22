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
import collections
from typing import Dict, List

from openstack_cli.modules.config import Configuration
from openstack_cli.modules.curl import curl, CurlRequestType
from openstack_cli.modules.openstack.api_objects import LoginResponse, ComputeLimits, VolumeV3Limits, DiskImages, \
  DiskImageInfo, ComputeServers, NetworkLimits, ComputeFlavors, ComputeFlavorItem
from openstack_cli.modules.openstack.objects import OpenStackEndpoints, EndpointTypes, OpenStackQuotas, ImageStatus, \
  OpenStackUsers, OpenStackVM, OpenStackVMInfo


class OpenStack(object):
  def __init__(self, conf: Configuration):
    self.__login_api = conf.os_address
    self._conf = conf
    self.__endpoints__: OpenStackEndpoints or None = None
    self.__cache_images: Dict[str, DiskImageInfo] = {}
    self.__users_cache: OpenStackUsers or None = None
    self.__flavors_cache: Dict[str, ComputeFlavorItem] or None = None

    if conf.auth_token and self.__check_token():
      pass
    else:
      self.__auth()

    # getting initial data / ToDo: cache them permanently in db-cache
    a = self.images
    a = self.flavors

  def __check_token(self) -> bool:
    headers = {
      "X-Auth-Token": self._conf.auth_token,
      "X-Subject-Token": self._conf.auth_token
    }
    r = curl(f"{self.__login_api}/v3/auth/tokens", req_type=CurlRequestType.GET, headers=headers)

    if r.code not in [200, 201]:
      return False

    l_resp = LoginResponse(serialized_obj=r.content)
    self.__endpoints__ = OpenStackEndpoints(self._conf, l_resp)
    return True

  def __auth(self) -> bool:
    data = {
      "auth": {
        "identity": {
          "methods": ["password"],
          "password": {
            "user": {
              "name": self._conf.os_login,
              "domain": {
                "id": "default"
              },
              "password": self._conf.os_password
            }
          }
        }
      }
    }

    r = curl(f"{self.__login_api}/v3/auth/tokens", req_type=CurlRequestType.POST, data=data)
    if r.code not in [200, 201]:
      return False

    auth_token = r.headers["X-Subject-Token"] if "X-Subject-Token" in r.headers else None
    self._conf.auth_token = auth_token

    l_resp = LoginResponse(serialized_obj=r.from_json())
    self.__endpoints__ = OpenStackEndpoints(self._conf, l_resp)

    return True

  @property
  def __endpoints(self) -> OpenStackEndpoints:
    return self.__endpoints__

  @property
  def endpoints(self):
    return self.__endpoints

  def __request(self,
                endpoint: EndpointTypes,
                relative_uri: str,
                params: Dict[str, str] = None,
                req_type: CurlRequestType = CurlRequestType.GET,
                is_json: bool = False,
                page_collection_name: str = None
                ) -> str or dict or None:
    url = f"{self.__endpoints.get_endpoint(endpoint)}{relative_uri}"
    headers = {
      "X-Auth-Token": self._conf.auth_token
    }
    r = curl(url, req_type=req_type, params=params, headers=headers)
    if r.code not in [200, 201]:
      return None

    content = r.from_json() if is_json else r.content

    if is_json and page_collection_name and isinstance(content, dict) and "next" in content:
      uri, _, args = content["next"].partition("?")
      params = dict([i.split("=") for i in args.split("&")])
      next_page = self.__request(
        endpoint,
        uri,
        params=params,
        req_type=req_type,
        is_json=is_json,
        page_collection_name=page_collection_name
      )
      content[page_collection_name].extend(next_page[page_collection_name])

    return content

  @property
  def users(self) -> OpenStackUsers:
    if self.__users_cache:
      return self.__users_cache

    self.__users_cache = OpenStackUsers(self.images)
    return self.__users_cache

  @property
  def images(self) -> List[DiskImageInfo]:
    if self.__cache_images:
      return list(self.__cache_images.values())

    params = {
      "limit": "1000"
    }

    images = DiskImages(
      serialized_obj=self.__request(
        EndpointTypes.image,
        "/v2/images",
        is_json=True,
        page_collection_name="images",
        params=params
      )
    ).images

    self.__cache_images = {img.id: img for img in images}

    return list(self.__cache_images.values())

  def get_image(self, image_id: str) -> DiskImageInfo or None:
    if not self.__cache_images:
      a = self.images

    if image_id in self.__cache_images:
      return self.__cache_images[image_id]

    return None

  @property
  def quotas(self) -> OpenStackQuotas:
    limits_obj = ComputeLimits(self.__request(EndpointTypes.compute, "/limits")).limits.absolute

    network_obj = NetworkLimits(serialized_obj=self.__request(
      EndpointTypes.network,
      f"/quotas/{self.__endpoints.project_id}/details.json",
      is_json=True
    )).quota
    # volume = VolumeV3Limits(
    #   serialized_obj=self.__request(
    #     EndpointTypes.volumev3,
    #     f"/os-quota-sets/{self.__endpoints.project_id}", params={"usage": "True"}, is_json=True
    #   )
    # )
    quotas = OpenStackQuotas()
    quotas.add("CPU_CORES", limits_obj.maxTotalCores, limits_obj.totalCoresUsed)
    quotas.add("RAM_GB", limits_obj.maxTotalRAMSize / 1024, limits_obj.totalRAMUsed / 1024)
    quotas.add("INSTANCES", limits_obj.maxTotalInstances, limits_obj.totalInstancesUsed)
    quotas.add("NET_PORTS", network_obj.port.limit, network_obj.port.used)
    quotas.add("KEYPAIRS", limits_obj.maxTotalKeypairs, 0)
    quotas.add("SERVER_GROUPS", limits_obj.maxServerGroups, limits_obj.totalServerGroupsUsed)
    quotas.add("RAM_MB", limits_obj.maxTotalRAMSize, limits_obj.totalRAMUsed)

    return quotas

  @property
  def flavors(self) -> List[ComputeFlavorItem]:
    if self.__flavors_cache:
      return list(self.__flavors_cache.values())

    params = {
      "limit": "1000"
    }
    flavors_raw = self.__request(
      EndpointTypes.compute,
      "/flavors/detail",
      is_json=True,
      params=params,
      page_collection_name="flavors"
    )
    self.__flavors_cache = {flavor.id: flavor for flavor in ComputeFlavors(serialized_obj=flavors_raw).flavors}
    return list(self.__flavors_cache.values())

  @property
  def servers(self) -> OpenStackVM:
    params = {
      "limit": "1000"
    }
    servers_raw = self.__request(
      EndpointTypes.compute,
      "/servers/detail",
      is_json=True,
      params=params,
      page_collection_name="servers"
    )
    servers = ComputeServers(serialized_obj=servers_raw).servers

    return OpenStackVM(servers, self.users, self.__cache_images, self.__flavors_cache)

  def get_server_by_cluster(self, search_pattern: str = "", sort: bool = False) -> Dict[str, List[OpenStackVMInfo]]:
    _servers: Dict[str, List[OpenStackVMInfo]] = {}
    for server in self.servers:
      if search_pattern and search_pattern not in server.cluster_name:
        continue

      if server.cluster_name not in _servers:
        _servers[server.cluster_name] = []

      _servers[server.cluster_name].append(server)

    if sort:
      _servers = collections.OrderedDict(sorted(_servers.items()))
    return _servers

