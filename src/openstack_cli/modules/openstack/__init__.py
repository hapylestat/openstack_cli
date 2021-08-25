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
import json
import os
import re
import sys
import time
from enum import Enum
from inspect import FrameInfo
from json import JSONDecodeError
from typing import Callable, Dict, Iterable, List, Optional, TypeVar, Union

from openstack_cli.modules.apputils.curl import CURLResponse, CurlRequestType, curl
from openstack_cli.modules.apputils.progressbar import CharacterStyles, ProgressBar, ProgressBarFormat, \
  ProgressBarOptions
from openstack_cli.modules.apputils.terminal.colors import Colors
from openstack_cli.modules.openstack.api_objects import APIProjects, ComputeFlavorItem, ComputeFlavors, ComputeLimits, \
  ComputeServerActionRebootType, ComputeServerActions, ComputeServerInfo, ComputeServers, DiskImageInfo, DiskImages, \
  LoginResponse, NetworkItem, NetworkLimits, Networks, Region, RegionItem, Subnets, Token, VMCreateResponse, \
  VMKeypairItem, \
  VMKeypairItemValue, VMKeypairs, VolumeV3Limits
from openstack_cli.modules.openstack.objects import AuthRequestBuilder, AuthRequestType, EndpointTypes, ImageStatus, \
  OSFlavor, OSImageInfo, OSNetwork, OpenStackEndpoints, OpenStackQuotaType, OpenStackQuotas, OpenStackUsers, \
  OpenStackVM, OpenStackVMInfo, ServerPowerState, ServerState, VMCreateBuilder

T = TypeVar('T')


class JSONValueError(ValueError):
  KEY: str = "{@json@}:"

  def __init__(self, data: str):
    self.__data = None
    try:
      json.loads(data)
      self.__data = data
    except (TypeError, JSONDecodeError):
     super(JSONValueError, self).__init__(data)

  def __str__(self):
    return f"{self.KEY}{self.__data}" if self.__data else super(JSONValueError, self).__str__()


class LocalCacheType(Enum):
  SERVERS = 0
  KEYPAIR = 1


class OpenStack(object):

  def __init__(self, conf, debug: bool = False):
    """
    :type conf openstack_cli.core.config.Configuration
    """
    self.__last_errors: List[str] = []
    self.__login_api = f"{conf.os_address}/v3"
    self._conf = conf
    self.__endpoints__: Optional[OpenStackEndpoints] = None
    self.__cache_images: Dict[str, DiskImageInfo] = {}

    # initializes in 2 steps: scanning images and server list when it is requested
    self.__users_cache: Optional[OpenStackUsers] = None

    self.__flavors_cache: Optional[Dict[str, OSFlavor]] = {}
    self.__networks_cache: Optional[OSNetwork] = None
    self.__debug = debug or os.getenv("API_DEBUG", False) == "True"
    self.__local_cache: Dict[LocalCacheType, object] = {}

    pattern_str = f"[\\W\\s]*(?P<name>{'|'.join(conf.supported_os_names)})(\\s|\\-|\\_)(?P<ver>[\\d\\.]+\\s*[\\w]*).*$"
    self.__os_image_pattern = re.compile(pattern_str, re.IGNORECASE)

    self.__is_auth: bool = False

  def __invalidate_local_cache(self, cache_type: LocalCacheType):
    self.__local_cache[cache_type.value] = None

  def __set_local_cache(self, cache_type: LocalCacheType, value: T) -> T:
    self.__local_cache[cache_type.value] = value

    return value

  def __get_local_cache(self, cache_type: LocalCacheType) -> T:
    if cache_type.value not in self.__local_cache:
      return None

    return self.__local_cache[cache_type.value]

  def __init_after_auth__(self):
    def __cache_ssh_keys():
      conf_keys_hashes = [hash(k) for k in self._conf.get_keys()]
      server_keys = self.get_keypairs()
      for server_key in server_keys:
        if hash(server_key) not in conf_keys_hashes:
          try:
            self._conf.add_key(server_key)
          except ValueError:
            print(f"Key {server_key.name} is present locally but have wrong hash, replacing with server key")
            self._conf.delete_key(server_key.name)
            self._conf.add_key(server_key)

      self._conf.cache.set(VMKeypairItemValue, "this super cache")

    def __cached_network():
      self.__networks_cache = OSNetwork(serialized_obj=self._conf.cache.get(OSNetwork))

    def __cached_images():
      self.__cache_images = {k: DiskImageInfo(serialized_obj=v) for k, v in json.loads(self._conf.cache.get(DiskImageInfo)).items()}

    def __cached_flavors():
      self.__flavors_cache = {k: OSFlavor(serialized_obj=v) for k, v in json.loads(self._conf.cache.get(OSFlavor)).items()}

    def __cached_ssh_keys():
      return True

    _cached_objects = {
      DiskImageInfo: {
       False: lambda: self.images,
       True: lambda: __cached_images()
      },
      OSFlavor: {
        False: lambda: self.flavors,
        True: lambda: __cached_flavors()
      },
      OSNetwork: {
       False: lambda: self.networks,
       True: lambda: __cached_network()
      },
      VMKeypairItemValue: {
       False: lambda: __cache_ssh_keys(),
       True: lambda: __cached_ssh_keys()
      }
    }

    need_recache: bool = False in [self._conf.cache.exists(obj) for obj in _cached_objects]
    if need_recache and not self.__debug:
      p = ProgressBar("Syncing to the server data",20,
        ProgressBarOptions(CharacterStyles.simple, ProgressBarFormat.PROGRESS_FORMAT_STATUS)
      )
      p.start(len(_cached_objects))
      for cache_item, funcs in _cached_objects.items():
        p.progress_inc(1, cache_item.__name__)
        funcs[self._conf.cache.exists(cache_item)]()
      p.stop(hide_progress=True)
    else:
      for cache_item, funcs in _cached_objects.items():
        funcs[self._conf.cache.exists(cache_item)]()

    if not self.__users_cache:
      self.users

  def __check_token(self) -> bool:
    headers = {
      "X-Auth-Token": self._conf.auth_token,
      "X-Subject-Token": self._conf.auth_token
    }

    r = self._request_simple(
      EndpointTypes.identity,
      "/auth/tokens",
      req_type=CurlRequestType.GET,
      headers=headers
    )

    if not r:
      from openstack_cli.core.output import Console
      Console.print_error("Authentication server is not accessible")
      return False

    if r.code not in [200, 201]:
      return False

    l_resp = LoginResponse(serialized_obj=r.content)
    self.__endpoints__ = OpenStackEndpoints(self._conf, l_resp)
    self._conf.user_id = l_resp.token.user.id
    return True

  def __auth(self, _type: AuthRequestType = AuthRequestType.SCOPED) -> bool:
    if self._conf.auth_token and self.__check_token():
      return True

    if _type == AuthRequestType.UNSCOPED:
      data = AuthRequestBuilder.unscoped_login(self._conf.os_login, self._conf.os_password)
    elif _type == AuthRequestType.SCOPED and self._conf.project.id:
      data = AuthRequestBuilder.scoped_login(self._conf.os_login, self._conf.os_password, self._conf.project)
    else:
      data = AuthRequestBuilder.normal_login(self._conf.os_login, self._conf.os_password)

    r = self._request_simple(
      EndpointTypes.identity,
      "/auth/tokens",
      req_type=CurlRequestType.POST,
      data=data
    )

    if not r:
      from openstack_cli.core.output import Console
      data = r.raw if r else "none"
      Console.print_error(f"Authentication server is not accessible: {data}")
      return False

    if r.code not in [200, 201]:
      return False

    auth_token = r.headers["X-Subject-Token"] if "X-Subject-Token" in r.headers else None
    self._conf.auth_token = auth_token

    l_resp = LoginResponse(serialized_obj=r.from_json())
    if _type == AuthRequestType.UNSCOPED:
      l_resp.token = Token(catalog=[])
      self.__endpoints__ = None
    else:
      self._conf.user_id = l_resp.token.user.id
      self.__endpoints__ = OpenStackEndpoints(self._conf, l_resp)

    return True

  def last_errors(self) -> List[str]:
    """
    Returning list of last errors with cleaning the results
    """
    return self.__last_errors

  def clear_errors(self):
    self.__last_errors = []

  @property
  def has_errors(self) -> bool:
    return len(self.__last_errors) > 0

  @property
  def __endpoints(self) -> OpenStackEndpoints:
    return self.__endpoints__

  @property
  def endpoints(self):
    return self.__endpoints

  def logout(self):
    self._conf.auth_token = ""

  def login(self, _type: AuthRequestType = AuthRequestType.SCOPED) -> bool:
    if self.__auth(_type):
      self.__is_auth = True
      if _type != AuthRequestType.UNSCOPED and self._conf.region:
        self.__init_after_auth__()
      return True
    else:
      self.__last_errors.append("Login failed, some exception happen")
      return False

  def __get_origin_frame(self, base_f_name: str) -> List[FrameInfo]:
    import inspect
    _frames = inspect.stack()
    for i in range(0, len(_frames)):
      if _frames[i].function == base_f_name:
        return [_frames[i+3], _frames[i+2], _frames[i+1]]

  def _request_simple(self,
                      endpoint: EndpointTypes,
                      relative_uri: str,
                      params: Dict[str, str] = None,
                      headers: Dict[str, str] = None,
                      req_type: CurlRequestType = CurlRequestType.GET,
                      data: str or dict = None
                      ) -> CURLResponse or None:

    if endpoint == EndpointTypes.identity:
      _endpoint: str = f"{self.__login_api}"
    else:
      _endpoint: str = self.__endpoints.get_endpoint(endpoint)

    url = f"{_endpoint}{relative_uri}"

    _t_start = 0
    if self.__debug:
      _t_start = time.time_ns()

    r = None
    try:
      return curl(url, req_type=req_type, params=params, headers=headers, data=data)
    except TimeoutError:
      self.__last_errors.append("Timeout exception on API request")
      return None
    finally:
      if self.__debug:
        from openstack_cli.core.output import Console
        _t_delta = time.time_ns() - _t_start
        _t_sec = _t_delta / 1000000000
        _params = ",".join([f"{k}={v}" for k, v in params.items()]) if params else "None"
        _f_caller = self.__get_origin_frame(self._request_simple.__name__)

        _chunks = [
          f"[{_t_sec:.2f}s]",
          f"[{req_type.value}]",
          f"[{endpoint.value}]",
          f" {relative_uri}; ",
          str(Colors.RESET),
          f"{Colors.BRIGHT_BLACK}{os.path.basename(_f_caller[0].filename)}{Colors.RESET}: ",
          f"{Colors.BRIGHT_BLACK}->{Colors.RESET}".join([f"{f.function}:{f.lineno}" for f in _f_caller])
        ]
        Console.print_debug("".join(_chunks))

  def _request(self,
               endpoint: EndpointTypes,
               relative_uri: str,
               params: Dict[str, str] = None,
               req_type: CurlRequestType = CurlRequestType.GET,
               is_json: bool = False,
               page_collection_name: str = None,
               data: str or dict = None
               ) -> str or dict or None:

    if not self.__is_auth and not self.login():
      raise RuntimeError("Not Authorised")

    _endpoint = self.__login_api if endpoint == EndpointTypes.identity else self.__endpoints.get_endpoint(endpoint)

    _t_start = 0
    if self.__debug:
      _t_start = time.time_ns()

    url = f"{_endpoint}{relative_uri}"
    headers = {
      "X-Auth-Token": self._conf.auth_token
    }

    r = None
    try:
      r = curl(url, req_type=req_type, params=params, headers=headers, data=data)
    except TimeoutError:
      self.__last_errors.append("Timeout exception on API request")
      return
    finally:
      if self.__debug:
        from openstack_cli.core.output import Console
        _t_delta = time.time_ns() - _t_start
        _t_sec = _t_delta / 1000000000
        _params = ",".join([f"{k}={v}" for k, v in params.items()]) if params else "None"
        _f_caller = self.__get_origin_frame(self._request.__name__)

        _chunks = [
          f"[{_t_sec:.2f}s]",
          f"[{req_type.value}]",
          f"[{endpoint.value}]",
          f" {relative_uri}; ",
          str(Colors.RESET),
          f"{Colors.BRIGHT_BLACK}{os.path.basename(_f_caller[0].filename)}{Colors.RESET}: ",
          f"{Colors.BRIGHT_BLACK}->{Colors.RESET}".join([f"{f.function}:{f.lineno}" for f in _f_caller])
        ]
        Console.print_debug("".join(_chunks))

    if r.code not in [200, 201, 202, 204]:
      # if not data:
      #   return None
      raise JSONValueError(r.content)

    if r.code in [204]:
      return ""

    content = r.from_json() if is_json else r.content

    if is_json and page_collection_name and isinstance(content, dict):
      if "next" in content and content["next"]:
        uri, _, args = content["next"].partition("?")
      elif "links" in content and "next" in content["links"] and content["links"]["next"]:
        uri, _, args = content["links"]["next"].partition("?")
      else:
        return content

      params = dict([i.split("=") for i in args.split("&")])
      next_page = self._request(
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
  def regions(self) -> List[RegionItem]:
    r = self._request(EndpointTypes.identity, "/regions", is_json=True, page_collection_name="regions")
    return Region(serialized_obj=r).regions


  @property
  def projects(self):
    d = self._request(
      EndpointTypes.identity,
      "/auth/projects",
      is_json=True,
      req_type=CurlRequestType.GET,
    )
    return APIProjects(serialized_obj=d).projects

  @property
  def users(self) -> OpenStackUsers:
    if self.__users_cache:
      return self.__users_cache

    self.__users_cache = OpenStackUsers(self.images)

    self.__users_cache.add_user(self._conf.user_id, self._conf.os_login)
    return self.__users_cache

  @property
  def images(self) -> List[DiskImageInfo]:
    if self.__cache_images:
      return list(self.__cache_images.values())

    params = {
      "limit": "1000"
    }

    images = DiskImages(
      serialized_obj=self._request(
        EndpointTypes.image,
        "/images",
        is_json=True,
        page_collection_name="images",
        params=params
      )
    ).images

    _cached_images = {}
    _cached = {}
    for img in images:
      _cached_images[img.id] = img
      _cached[img.id] = img.serialize()
    self._conf.cache.set(DiskImageInfo, _cached)
    self.__cache_images = _cached_images

    return list(self.__cache_images.values())

  def get_os_image(self, image: DiskImageInfo) -> Optional[OSImageInfo]:
    if image.image_type:  # process only base images
      return None

    match = re.match(self.__os_image_pattern, image.name)

    if not match:
      return None

    os_img = OSImageInfo(
      match.group("name"),
      match.group("ver"),
      image
    )
    # === here is some lame way to filter out image forks or non-base images by analyzing image name
    # ToDo: Is here a better way to distinguish the image os?

    # try to handle situations like "x yyyy" in versions and treat them like "x.yyyy"
    ver = os_img.version.split(" ") if " " in os_img.version else None
    if ver:
      try:
        ver = ".".join([str(int(n)) for n in ver])
      except ValueError:
        ver = None
    if ver:
      os_img.version = ver

    if "SP" not in os_img.version and " " in os_img.version:
      return None

    return os_img

  @property
  def os_images(self) -> List[OSImageInfo]:
    img = []
    known_versions = {}
    for image in self.images:
      os_img: OSImageInfo = self.get_os_image(image)

      if os_img is None:
        continue

      if os_img.os_name.lower() not in known_versions:
        known_versions[os_img.os_name.lower()] = []

      if os_img.version in known_versions[os_img.os_name.lower()]:
        continue

      known_versions[os_img.os_name.lower()].append(os_img.version)
      # == /end
      img.append(os_img)

    img = sorted(img, key=lambda x: x.name)
    return img

  def get_image(self, image_id: str) -> DiskImageInfo or None:
    if not self.__cache_images:
      a = self.images

    if image_id in self.__cache_images:
      return self.__cache_images[image_id]

    return None

  @property
  def quotas(self) -> OpenStackQuotas:
    limits_obj = ComputeLimits(self._request(EndpointTypes.compute, "/limits")).limits.absolute

    network_obj = NetworkLimits(serialized_obj=self._request(
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
    quotas.add(OpenStackQuotaType.CPU_CORES, limits_obj.maxTotalCores, limits_obj.totalCoresUsed)
    quotas.add(OpenStackQuotaType.RAM_GB, limits_obj.maxTotalRAMSize / 1024, limits_obj.totalRAMUsed / 1024)
    quotas.add(OpenStackQuotaType.INSTANCES, limits_obj.maxTotalInstances, limits_obj.totalInstancesUsed)
    quotas.add(OpenStackQuotaType.NET_PORTS, network_obj.port.limit, network_obj.port.used)
    quotas.add(OpenStackQuotaType.KEYPAIRS, limits_obj.maxTotalKeypairs, 0)
    quotas.add(OpenStackQuotaType.SERVER_GROUPS, limits_obj.maxServerGroups, limits_obj.totalServerGroupsUsed)
    quotas.add(OpenStackQuotaType.RAM_MB, limits_obj.maxTotalRAMSize, limits_obj.totalRAMUsed)

    return quotas

  @property
  def flavors(self) -> List[OSFlavor]:
    if self.__flavors_cache:
      return list(self.__flavors_cache.values())

    params = {
      "limit": "1000"
    }
    flavors_raw = self._request(
      EndpointTypes.compute,
      "/flavors/detail",
      is_json=True,
      params=params,
      page_collection_name="flavors"
    )

    __flavors_cache = {}
    _cache = {}
    for flavor in ComputeFlavors(serialized_obj=flavors_raw).flavors:
      _flavor = OSFlavor.get(flavor)
      self.__flavors_cache[_flavor.id] = _flavor
      _cache[_flavor.id] = _flavor.serialize()

    self._conf.cache.set(OSFlavor, _cache)

    return list(self.__flavors_cache.values())

  def get_flavors(self, image: OSImageInfo = None) -> Iterable[OSFlavor]:
    """
    Returns acceptable flavors for image
    """
    for fl in sorted(self.flavors, key=lambda x: x.disk):
      if image and fl.disk > image.size and fl.ephemeral_disk > 0:
        yield fl

  def get_flavor(self, image: OSImageInfo = None, name: str = "") -> OSFlavor or None:
    if not name:
      flavors = list(self.get_flavors(image))
      if flavors:
        return flavors[0]
    else:
      for fl in self.flavors:
        if fl.name == name:
          return fl

    return None

  def get_image_by_alias(self, alias: str) -> Iterable[OSImageInfo]:
    """
    Return image object by given alias name
    """
    for img in self.os_images:
      if img.alias == alias:
        yield img

  def get_servers(self, arguments: dict = None, invalidate_cache: bool = False) -> OpenStackVM or None:
    if arguments is None:
      arguments = {}

    if invalidate_cache:
      self.__invalidate_local_cache(LocalCacheType.SERVERS)

    __cached_value = self.__get_local_cache(LocalCacheType.SERVERS)
    if __cached_value is not None and not arguments:
      return __cached_value

    params = {
      "limit": "1000"
    }

    params.update(arguments)
    servers_raw = self._request(
      EndpointTypes.compute,
      "/servers/detail",
      is_json=True,
      params=params,
      page_collection_name="servers"
    )
    servers = ComputeServers(serialized_obj=servers_raw).servers
    obj = OpenStackVM(servers, self.__cache_images, self.__flavors_cache, self.__networks_cache, self.__users_cache)
    if arguments:  # do no cache custom requests
      return obj
    else:
      return self.__set_local_cache(LocalCacheType.SERVERS, obj)

  def get_server_by_id(self, _id: str or OpenStackVMInfo) -> OpenStackVMInfo:
    if isinstance(_id, OpenStackVMInfo):
      _id = _id.id

    r = self._request(
      EndpointTypes.compute,
      f"/servers/{_id}",
      req_type=CurlRequestType.GET,
      is_json=True
    )

    servers = [ComputeServerInfo(serialized_obj=r["server"])]
    osvm = OpenStackVM(servers, self.__cache_images, self.__flavors_cache, self.__networks_cache)
    return osvm.items[0]

  @property
  def servers(self) -> OpenStackVM:
    return self.get_servers()

  @property
  def networks(self) -> OSNetwork:
    if self.__networks_cache:
      return self.__networks_cache

    params = {
      "limit": "1000"
    }
    networks = Networks(serialized_obj=self._request(
      EndpointTypes.network,
      "/networks",
      is_json=True,
      params=params,
      page_collection_name="networks"
    )).networks
    subnets = Subnets(serialized_obj=self._request(
      EndpointTypes.network,
      "/subnets",
      is_json=True,
      params=params,
      page_collection_name="subnets"
    )).subnets
    self.__networks_cache = OSNetwork().parse(networks, subnets)
    self._conf.cache.set(OSNetwork, self.__networks_cache.serialize())
    return self.__networks_cache

  def get_server_by_cluster(self,
                            search_pattern: str = "",
                            sort: bool = False,
                            filter_func: Callable[[OpenStackVMInfo], bool] = None,
                            no_cache: bool = False,
                            only_owned: bool = False,
                            ) -> Dict[str, List[OpenStackVMInfo]]:
    """
    :param search_pattern: vm search pattern list
    :param sort: sort resulting list
    :param no_cache: force real server query, do not try to use cache
    :param filter_func: if return true - item would be filtered, false not
    """
    _servers: Dict[str, List[OpenStackVMInfo]] = {}
    user_id = self._conf.user_id
    # if no cached queries available, execute limited query
    if no_cache or self.__get_local_cache(LocalCacheType.SERVERS) is None:
      servers = self.get_servers(arguments={
        "name": f"^{search_pattern}.*"
      }).items

      for server in servers:
        if only_owned and server.owner_id != user_id:
          continue

        if filter_func and filter_func(server): # need to be last in the filtering chain
          continue

        if server.cluster_name not in _servers:
          _servers[server.cluster_name] = []

        _servers[server.cluster_name].append(server)
    else:  # if we already requested the full list, no need for another call
      for server in self.servers:
        _sname = server.cluster_name.lower()[:len(search_pattern)]
        if search_pattern and search_pattern.lower() != _sname:
          continue

        if only_owned and server.owner_id != user_id:
          continue

        if filter_func and filter_func(server): # need to be last in the filtering chain
          continue

        if server.cluster_name not in _servers:
          _servers[server.cluster_name] = []

        _servers[server.cluster_name].append(server)

    if sort:
      for key in _servers:
        _servers[key] = sorted(_servers[key], key=lambda x: x.name)
      _servers = dict(sorted(_servers.items(), key=lambda x: x[0]))
    return _servers

  def get_server_console_log(self,
                             server_id: str or OpenStackVMInfo,
                             grep_by: str = None,
                             last_lines: int = 0
                             ) -> List[str]:
    if isinstance(server_id, OpenStackVMInfo):
      server_id = server_id.id

    params = None
    if last_lines:
      params = {
        "length": last_lines
      }

    r = self._request(
      EndpointTypes.compute,
      f"/servers/{server_id}/action",
      req_type=CurlRequestType.POST,
      params=params,
      data={
        "os-getConsoleOutput": {
          "length": None
        }
      },
      is_json=True
    )

    lines: List[str] = r["output"].split("\n")

    if grep_by:
      lines = [line for line in lines if grep_by in line]

    return lines

  def _to_base64(self, s: str) -> str:
    return str(base64.b64encode(s.encode("utf-8")), "utf-8")

  def delete_image(self, image: DiskImageInfo) -> bool:
    disk_id: str = image.id
    try:
      r = self._request(
        EndpointTypes.image,
        f"/images/{disk_id}",
        req_type=CurlRequestType.DELETE
      )
      return True
    except ValueError as e:
      return False

  def delete_instance(self, server: OpenStackVMInfo or ComputeServerInfo) -> bool:
    server_id: str = server.id
    try:
      r = self._request(
        EndpointTypes.compute,
        f"/servers/{server_id}",
        req_type=CurlRequestType.DELETE
      )
      return r is not None
    except ValueError as e:
      return False

  def get_keypairs(self, no_cache: bool = False) -> List[VMKeypairItemValue]:
    if no_cache:
      self.__invalidate_local_cache(LocalCacheType.KEYPAIR)

    _cache = self.__get_local_cache(LocalCacheType.KEYPAIR)
    if _cache:
      return list(_cache.values())

    try:
      r = self._request(
        EndpointTypes.compute,
        "/os-keypairs",
        req_type=CurlRequestType.GET,
        is_json=True
      )

      return list(self.__set_local_cache(
        LocalCacheType.KEYPAIR,
        {kp.keypair.name: kp.keypair for kp in VMKeypairs(serialized_obj=r).keypairs}
      ).values())
    except ValueError as e:
      self.__last_errors.append(str(e))

    return []

  def get_keypair(self, name: str, default: VMKeypairItemValue = None, no_cache: bool = False) -> VMKeypairItemValue or None:
    _cache = self.__get_local_cache(LocalCacheType.KEYPAIR)
    if not no_cache and _cache and name in _cache:
      return _cache[name]

    try:
      r = self._request(
        EndpointTypes.compute,
        f"/os-keypairs/{name}",
        req_type=CurlRequestType.GET,
        is_json=True
      )
      return VMKeypairItem(serialized_obj=r).keypair
    except ValueError as e:
      self.__last_errors.append(str(e))

    return default

  def delete_keypair(self, name: str) -> bool:
    try:
      r = self._request(
        EndpointTypes.compute,
        f"/os-keypairs/{name}",
        req_type=CurlRequestType.DELETE
      )
      return True
    except ValueError as e:
      self.__last_errors.append(str(e))

    return False

  def create_keypair(self, name: str, public_key: str) -> bool:
    try:
      data = {
        "keypair": {
          "name": name,
          "public_key": public_key
        }
      }
      r = self._request(
        EndpointTypes.compute,
        "/os-keypairs",
        req_type=CurlRequestType.POST,
        is_json=True,
        data=data
      )
      return VMKeypairItem(serialized_obj=r).keypair.name == name
    except ValueError as e:
      self.__last_errors.append(str(e))

    return False

  def create_key(self, key: VMKeypairItemValue) -> bool:
    return self.create_keypair(key.name, key.public_key)

  def __server_action(self, server: OpenStackVMInfo or ComputeServerInfo, action: ComputeServerActions,
                      action_data: dict = None) -> bool:
    server_id: str = server.id
    try:
      action_raw = {
        action.value: action_data
      }
      r = self._request(
        EndpointTypes.compute,
        f"/servers/{server_id}/action",
        req_type=CurlRequestType.POST,
        is_json=True,
        data=action_raw
      )
      return True
    except ValueError as e:
      self.__last_errors.append(str(e))
    except Exception as e:
      print(str(e), file=sys.stderr)

    return False

  def stop_instance(self, server: OpenStackVMInfo or ComputeServerInfo) -> bool:
    return self.__server_action(server, ComputeServerActions.stop)

  def start_instance(self, server: OpenStackVMInfo or ComputeServerInfo) -> bool:
    return self.__server_action(server, ComputeServerActions.start)

  def reboot_instance(self, server: OpenStackVMInfo or ComputeServerInfo,
                      how: ComputeServerActionRebootType = ComputeServerActionRebootType.hard) -> bool:

    return self.__server_action(server, ComputeServerActions.reboot, {"type": how.value})

  def get_server_status(self, servers_id: str or OpenStackVMInfo) -> ServerState:
    return self.get_server_by_id(servers_id).status

  def create_instances(self, cluster_names: Union[List[str], str], image: OSImageInfo, flavor: OSFlavor,
                       password: str, ssh_key: VMKeypairItemValue = None, count: int = 1) -> List[OpenStackVMInfo]:
    custom_user = "openstack"
    init_script = f"""#!/bin/bash
echo 'PermitRootLogin yes'| cat - /etc/ssh/sshd_config > /tmp/sshd_config
echo 'PasswordAuthentication yes'| cat - /tmp/sshd_config > /etc/ssh/sshd_config && rm -f /tmp/sshd_config
useradd {custom_user}; echo -e "{password}\n{password}"|passwd {custom_user}
echo -e "{password}\n{password}"|passwd root
systemctl restart ssh.service
systemctl restart sshd.service
"""

    if ssh_key:
      init_script += f"""
KEY='{ssh_key.public_key}'
echo ${{KEY}} >/root/.ssh/authorized_keys
mkdir -p /home/{custom_user}/.ssh; echo '${{KEY}}' >/home/{custom_user}/.ssh/authorized_keys
"""

    init_script += f"""
UID_MIN=$(grep -E '^UID_MIN' /etc/login.defs | tr -d -c 0-9)
USERS=$(awk -v uid_min="${{UID_MIN}}" -F: '$3 >= uid_min && $1 != "nobody" {{printf "%s ",$1}}'  /etc/passwd)
echo "@users@: ${{USERS}}"
"""
    if isinstance(cluster_names, str):
      cluster_names: List[str] = [cluster_names]

    if len(cluster_names) > 1:  # we can create eighter bulk of cluster with one request or with different request
      count: int = 1

    created_servers: List[OpenStackVMInfo] = []

    for cluster_name in cluster_names:
      builder = VMCreateBuilder(cluster_name) \
        .set_admin_pass(password) \
        .set_image(image.base_image) \
        .set_flavor(flavor) \
        .add_network(self._conf.default_network) \
        .set_user_data(init_script) \
        .set_instances_count(count) \
        .enable_reservation_id()

      if ssh_key:
        builder.set_key_name(ssh_key.name)

      r = None
      try:
        r = self._request(
          EndpointTypes.compute,
          "/servers",
          req_type=CurlRequestType.POST,
          is_json=True,
          data=builder.build().serialize()
        )
      except ValueError as e:
        self.__last_errors.append(str(e))
        return []

      if (response := VMCreateResponse(serialized_obj=r)) and response.reservation_id:
        servers = self.get_servers({"reservation_id": response.reservation_id})
        created_servers.extend(list(servers.items))
      else:
        created_servers.append(self.get_server_by_id(response.server.id))

    return created_servers
