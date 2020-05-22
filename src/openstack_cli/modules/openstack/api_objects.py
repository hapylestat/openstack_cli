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

from typing import List
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
  addresses: ComputeServerAddress = None
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
