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

from typing import Dict, List

from openstack_cli.modules.config import Configuration
from openstack_cli.modules.curl import curl, CURLResponse, CurlRequestType
from openstack_cli.modules.openstack.api_objects import LoginResponse, ComputeLimits, VolumeV3Limits, DiskImages, \
  DiskImageInfo, ComputeServers, NetworkLimits
from openstack_cli.modules.openstack.objects import OpenStackEndpoints, EndpointTypes, OpenStackQuotas, ImageStatus


class OpenStack(object):
  def __init__(self, conf: Configuration):
    self.__login_api = conf.os_address
    self._conf = conf
    self.__endpoints__: OpenStackEndpoints or None = None

    if conf.auth_token and self.__check_token():
      pass
    else:
      self.__auth()

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

  def get_images(self,
                 status: ImageStatus or List[ImageStatus] or None = None,
                 tag: str or List[str] or None = None,
                 id: str or List[str] or None = None,
                 name: str or List[str] or None = None
                 ):
    pass

  @property
  def images(self) -> List[DiskImageInfo]:
    params = {
      "limit": "1000"
    }

    return DiskImages(
      serialized_obj=self.__request(
        EndpointTypes.image,
        "/v2/images",
        is_json=True,
        page_collection_name="images",
        params=params
      )
    ).images

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
    quotas.add("CPU", limits_obj.maxTotalCores, limits_obj.totalCoresUsed)
    quotas.add("RAM_GB", limits_obj.maxTotalRAMSize / 1024, limits_obj.totalRAMUsed / 1024)
    quotas.add("INSTANCES", limits_obj.maxTotalInstances, limits_obj.totalInstancesUsed)
    quotas.add("NET_PORTS", network_obj.port.limit, network_obj.port.used)
    quotas.add("KEYPAIRS", limits_obj.maxTotalKeypairs, 0)
    quotas.add("SERVER_GROUPS", limits_obj.maxServerGroups, limits_obj.totalServerGroupsUsed)
    quotas.add("RAM_MB", limits_obj.maxTotalRAMSize, limits_obj.totalRAMUsed)

    return quotas

  @property
  def servers(self):
    params = {
      "limit": "1000"
    }
    r = ComputeServers(serialized_obj=self.__request(
      EndpointTypes.compute,
      "/servers/detail",
      is_json=True,
      params=params,
      page_collection_name="servers"
    ))

    return r
