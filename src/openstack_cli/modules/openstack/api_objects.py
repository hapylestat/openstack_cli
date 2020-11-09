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
from typing import List, Dict
from openstack_cli.modules.json2obj import SerializableObject


class Links(SerializableObject):
  href: str = None
  rel: str = None


class OpenStackRelation(SerializableObject):
  id: str = None
  links: List[Links] = []


class Role(SerializableObject):
  id: str = None
  name: str = None


class UserDomain(SerializableObject):
  id: str = None
  name: str = None


class Endpoints(SerializableObject):
  region_id: str = None
  url: str = None
  region: str = None
  interface: str = None
  id: str = None


class EndpointCatalog(SerializableObject):
  type: str = None
  id: str = None
  name: str = None
  endpoints: List[Endpoints] = []


class User(SerializableObject):
  password_expires_at: str = None
  id: str = None
  name: str = None
  domain: UserDomain = None


class Token(SerializableObject):
  is_domain: bool = False
  methods: List[str] = []
  roles: List[Role] = []
  expires_at: str = None
  issued_at: str = None
  audit_ids: List[str] = []
  catalog: List[EndpointCatalog] = []
  user: User = None
  project: User = None


class LoginResponse(SerializableObject):
  token: Token = None


# /network/quotas/{project_id}/details.json
class NetworkLimitItem(SerializableObject):
  reserved: int = 0
  used: int = 0
  limit: int = 0


class NetworkLimitsQuota(SerializableObject):
  subnet: NetworkLimitItem = None
  network: NetworkLimitItem = None
  floatingip: NetworkLimitItem = None
  subnetpool: NetworkLimitItem = None
  security_group_rule: NetworkLimitItem = None
  security_group: NetworkLimitItem = None
  router: NetworkLimitItem = None
  rbac_policy: NetworkLimitItem = None
  port: NetworkLimitItem = None


class NetworkLimits(SerializableObject):
  quota: NetworkLimitsQuota = None


# /compute/limits


class ComputeAbsoluteLimits(SerializableObject):
  maxServerMeta: int = 0
  maxPersonality: int = 0
  totalServerGroupsUsed: int = 0
  maxImageMeta: int = 0
  maxPersonalitySize: int = 0
  maxTotalKeypairs: int = 0
  maxSecurityGroupRules: int = 0
  maxServerGroups: int = 0
  totalCoresUsed: int = 0
  totalRAMUsed: int = 0
  totalInstancesUsed: int = 0
  maxSecurityGroups: int = 0
  totalFloatingIpsUsed: int = 0
  maxTotalCores: int = 0
  maxServerGroupMembers: int = 0
  maxTotalFloatingIps: int = 0
  totalSecurityGroupsUsed: int = 0
  maxTotalInstances: int = 0
  maxTotalRAMSize: int = 0


class ComputeLimitsObj(SerializableObject):
  rate: List[object] = []
  absolute: ComputeAbsoluteLimits = None


class ComputeLimits(SerializableObject):
  limits: ComputeLimitsObj = ComputeLimitsObj()

# /volumev3/limits


class VolumeLimitItem(SerializableObject):
  reserved: int = 0
  allocated: int = 0
  limit: int = 0
  in_use: int = 0


class VolumeQuotaSet(SerializableObject):
  id: str = ""
  snapshots_lvm: VolumeLimitItem = None
  per_volume_gigabytes: VolumeLimitItem = None
  groups: VolumeLimitItem = None
  gigabytes: VolumeLimitItem = None
  backup_gigabytes: VolumeLimitItem = None
  volumes_lvm: VolumeLimitItem = None
  snapshots: VolumeLimitItem = None
  volumes: VolumeLimitItem = None
  backups: VolumeLimitItem = None
  gigabytes_lvm: VolumeLimitItem = None


class VolumeV3Limits(SerializableObject):
  quota_set: VolumeQuotaSet = None


# /image/images
class DiskImageLocation(SerializableObject):
  url: str = None
  metadata: dict = None


class DiskImageInfo(SerializableObject):
  status: str = None
  name: str = None
  tags: List[str] = []
  container_format: str = None
  created_at: str = None
  disk_format: str = None
  updated_at: str = None
  visibility: str = None
  self: str = None
  min_disk: int = 0
  protected: bool = False
  id: str = None
  file: str = None
  checksum: str = None
  os_hash_algo: str = None
  os_hash_value: str = None
  os_hidden: bool = False
  owner: str = None
  size: int = None
  min_ram: int = 0
  schema: str = None
  virtual_size: int = 0
  image_state: str = None
  boot_roles: str = None
  user_id: str = None
  image_type: str = None
  base_image_ref: str = None
  owner_project_name: str = None
  owner_id: str = None
  image_location: str = None
  locations: List[DiskImageLocation] = []
  owner_user_name: str = None
  instance_uuid: str = None
  hypervisor_type: str = None
  description: str = None
  owner_specified_shade_sha256: str = None
  owner_specified_shade_object: str = None
  owner_specified_shade_md5: str = None
  architecture: str = None
  hw_scsi_model: str = None
  hw_vif_multiqueue_enabled: str = None
  hw_disk_bus: str = None
  hw_qemu_guest_agent: str = None
  img_config_drive: str = None
  os_require_quiesce: str = None


class DiskImages(SerializableObject):
  images: List[DiskImageInfo] = []
  schema: str = None
  first: str = None
  next: str = None


#  /compute/servers
class SecurityGroupItem(SerializableObject):
  name: str = None


class ComputeServerAddressInfo(SerializableObject):
  OS_EXT_IPS_MAC_mac_addr: str = None
  version: int = 0
  addr: str = None
  OS_EXT_IPS_type: str = None


class ComputeServerAddress(SerializableObject):
  INTERNAL_NET: List[ComputeServerAddressInfo] = []
  INTERNAL_NET2: List[ComputeServerAddressInfo] = []
  PROVIDER_NET: List[ComputeServerAddressInfo] = []


class ComputeServerFault(SerializableObject):
  message: str = None
  code: int = None
  created: str = None


class ComputeServerInfo(SerializableObject):
  OS_EXT_STS_task_state: str = None
  OS_EXT_STS_vm_state: str = None
  OS_SRV_USG_launched_at: str = None
  OS_DCF_diskConfig: str = None
  OS_EXT_STS_power_state: int = None
  OS_EXT_AZ_availability_zone: str = None
  OS_SRV_USG_terminated_at: str = None
  metadata: dict = {}
  os_extended_volumes_volumes_attached: List[object] = []
  tenant_id: str = None
  created: str = None
  name: str = None
  key_name: str = None
  hostId: str = None
  updated: str = None
  status: str = None
  config_drive: str = None
  progress: int = 0
  accessIPv6: str = None
  accessIPv4: str = None
  user_id: str = None
  id: str = None
  security_groups: List[SecurityGroupItem] = []
  flavor: OpenStackRelation = None
  links: List[Links] = []
  image: OpenStackRelation = None
  #addresses: ComputeServerAddress = None
  addresses: Dict[str, List[ComputeServerAddressInfo]] = {}
  fault: ComputeServerFault = None


class ComputeServers(SerializableObject):
  servers: List[ComputeServerInfo] = []
  schema: str = None
  first: str = None
  next: str = None


class ComputeFlavorItem(SerializableObject):
  name: str = None
  ram: int = 0
  vcpus: int = 0
  swap: int = 0
  rxtx_factor: float = 0.0
  disk: int = 0
  id: str = None
  links: List[Links] = []
  OS_FLV_DISABLED_disabled: bool = False
  os_flavor_access_is_public: bool = False
  OS_FLV_EXT_DATA_ephemeral: int = 4


class ComputeFlavors(SerializableObject):
  flavors: List[ComputeFlavorItem] = []
  schema: str = None
  first: str = None
  next: str = None


class AllocationPoolItem(SerializableObject):
  start: str = None
  end: str = None


class SubnetItem(SerializableObject):
  service_types: List[object] = None
  description: str = None
  enable_dhcp: bool = False
  tags: List[str] = []
  network_id: str = None
  tenant_id: str = None
  created_at: str = None
  dns_nameservers: List[str] = []
  updated_at: str = None
  ipv6_ra_mode: object = None
  allocation_pools: List[AllocationPoolItem] = []
  gateway_ip: str = None
  revision_number: int = 0
  ipv6_address_mode: object = None
  ip_version: int = 0
  host_routes: List[object] = []
  cidr: str = None
  project_id: str = None
  id: str = None
  subnetpool_id: str = None
  name: str = None


class Subnets(SerializableObject):
  subnets: List[SubnetItem] = []
  subnets_links: List[Links] = []
  schema: str = None
  first: str = None
  next: str = None


class NetworkItem(SerializableObject):
  status: str = None
  router_external: bool = False
  availability_zone_hints: List[object] = []
  availability_zones: List[str] = []
  ipv4_address_scope: object = None
  description: str = None
  port_security_enabled: bool = False
  subnets: List[str] = []
  updated_at: str = None
  tenant_id: str = None
  created_at: str = None
  tags: List[str] = []
  ipv6_address_scope: object = None
  dns_domain: str = None
  mtu: int = 0
  revision_number: int = 0
  admin_state_up: bool = False
  shared: bool = False
  project_id: str = None
  id: str = None
  name: str = None
  is_default: bool = False


class Networks(SerializableObject):
  networks: List[NetworkItem] = []
  networks_links: List[Links] = []
  schema: str = None
  first: str = None
  next: str = None


# POST OBJECTS

class VMCreateNewFileItem(SerializableObject):
  path: str = None
  contents: str = None  # base64 encoded


class VMCreateNetworksItem(SerializableObject):
  uuid: str = None


class VMCreateServerItem(SerializableObject):
  name: str = None
  flavorRef: str = None
  imageRef: str = None
  adminPass: str = None
  key_name: str = None
  networks: List[VMCreateNetworksItem] = []
  personality: List[VMCreateNewFileItem] = []
  user_data: str = None
  min_count: str = None
  max_count: str = None
  return_reservation_id: str = None


class VMCreateServer(SerializableObject):
  server: VMCreateServerItem = None


class VMCreateResponseItem(SerializableObject):
  security_groups: List[Role] = []
  OS_DCF_diskConfig: str = None
  id: str = None
  links: List[Links] = []
  adminPass: str = None


class VMCreateResponse(SerializableObject):
  server: VMCreateResponseItem = None
  reservation_id: str = None


class ComputeServerActions(Enum):
  """
  https://docs.openstack.org/api-ref/compute/?expanded=stop-server-os-stop-action-detail,change-administrative-password-changepassword-action-detail
  """
  changePassword = "changePassword"
  confirmResize = "confirmResize"
  """
  {
    "pause": null
  }
  """
  pause = "pause"
  """
  {
    "reboot" : {
        "type" : "HARD"
    }
  }
  """
  reboot = "reboot"  # type = HARD, SOFT
  """
  {
    "os-start" : null
  }
  """
  start = "os-start"
  """
  {
    "os-stop" : null
  }
  """
  stop = "os-stop"
  """
  {
    "os-getConsoleOutput": {
        "length": 50
    }
  }
  """
  console = "os-getConsoleOutput"   # length


class ComputeServerActionRebootType(Enum):
  soft = "SOFT"
  hard = "HARD"


class ApiErrorMessage(SerializableObject):
  message: str = ""
  code: int = 0


class ApiErrorResponse(SerializableObject):
  conflictingRequest: ApiErrorMessage = ApiErrorMessage()
  badRequest: ApiErrorMessage = ApiErrorMessage()
  itemNotFound: ApiErrorMessage = ApiErrorMessage()

  @property
  def message(self) -> str:
    if self.conflictingRequest.code != 0:
      return self.conflictingRequest.message

    if self.badRequest.code != 0:
      return self.badRequest.message

    if self.itemNotFound.code != 0:
      return self.itemNotFound.message

    raise RuntimeError("No exception")

  @property
  def code(self) -> int:
    if self.conflictingRequest.code != 0:
      return self.conflictingRequest.code

    if self.badRequest.code != 0:
      return self.badRequest.code

    if self.itemNotFound.code != 0:
      return self.itemNotFound.code

    raise RuntimeError("No exception")


class VMKeypairItemValue(SerializableObject):
  public_key: str = ""
  private_key: str = ""   # this is custom field to store internally private key as well
  user_id: str = ""
  name: str = ""
  deleted: bool = False
  created_at: str = ""
  updated_at: str = ""
  fingerprint: str = ""
  deleted_at: str = ""
  type: str = ""
  id: int = 0

  def __hash__(self):
    return hash((self.name, self.public_key))


class VMKeyPairItemBuilder(object):
  def __init__(self):
    self.__key = VMKeypairItemValue()

  def set_name(self, name: str):
    self.__key.name = name
    return self

  def set_public_key(self, key: str or bytes):
    if isinstance(key, bytes):
      key = key.decode("UTF-8")
    self.__key.public_key = key
    return self

  def set_private_key(self, key: str or bytes):
    if isinstance(key, bytes):
      key = key.decode("UTF-8")
    self.__key.private_key = key
    return self

  def build(self):
    return self.__key

class VMKeypairItem(SerializableObject):
  keypair: VMKeypairItemValue = None


class VMKeypairs(SerializableObject):
  keypairs: List[VMKeypairItem] = []
  keypairs_links: List[Links] = []

