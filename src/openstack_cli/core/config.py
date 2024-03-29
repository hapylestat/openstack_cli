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

import os
import json
import time
from typing import List

from openstack_cli.modules.apputils.config import BaseConfiguration, StorageProperty, StorageType, DataCacheExtension
from openstack_cli.modules.openstack.objects import VMProject


class Configuration(BaseConfiguration):
  __OBJECTS_CACHE_TABLE = "cache"
  __cache_invalidation: float = time.mktime(time.gmtime(8 * 3600))  # 8 hours
  _keys_table = "keys"

  def __init__(self, storage: StorageType = StorageType.SQL,
               app_name: str = 'apputils', lazy_init: bool = False, upgrade_manager=None):
    super(Configuration, self).__init__(
      storage=storage,
      app_name=app_name,
      lazy_init=lazy_init,
      upgrade_manager=upgrade_manager
    )

    self.add_cache_ext(self.__OBJECTS_CACHE_TABLE, self.__cache_invalidation)

    self.__migrate_if_needed()

  def __migrate_if_needed(self):
    if self._options_flags_name_old not in self._storage.get_property_list(self._options_table):
      return

    val = list(self._storage.get_property(self._options_table,self._options_flags_name_old).value)
    if len(val) != 3:
      return

    new_val: int = 0

    for i in range(0, len(val)-1):
      _v = 1 if val[i] == "1" else 0
      new_val = new_val | (_v << i)

    self._storage.set_text_property(self._options_table, self._options_flags_name, str(new_val))
    self._storage.delete_property(self._options_table, self._options_flags_name_old)

  @property
  def cache(self) -> DataCacheExtension:
    return self.get_cache_ext(self.__OBJECTS_CACHE_TABLE)

  @property
  def os_address(self) -> str:
    return self._storage.get_property(self._options_table, "os_address", StorageProperty()).value

  @os_address.setter
  def os_address(self, value: str):
    self._storage.set_text_property(self._options_table, "os_address", value)

  @property
  def os_login(self) -> str:
    return self._storage.get_property(self._options_table, "os_login", StorageProperty()).value

  @os_login.setter
  def os_login(self, value: str):
    self._storage.set_text_property(self._options_table, "os_login", value, encrypted=True)

  @property
  def os_password(self) -> str:
    return self._storage.get_property(self._options_table, "os_password", StorageProperty()).value

  @os_password.setter
  def os_password(self, value: str):
    self._storage.set_text_property(self._options_table, "os_password", value, encrypted=True)

  @property
  def key_names(self) -> List[str]:
    return self._storage.get_property_list(self._keys_table)

  def add_key(self, key):
    """
    :type key: openstack_cli.modules.openstack.VMKeypairItemValue
    """
    if key.name in self.key_names:
      raise ValueError(f"Key with name '{key.name}' already exists")

    self._storage.set_text_property(self._keys_table, key.name, key.to_json(), True)

  def delete_key(self, name: str) -> bool:
    if name in self.key_names:
      return self._storage.delete_property(self._keys_table, name)
    return True

  def get_key(self, name: str):
    """
    :rtype openstack_cli.modules.openstack.VMKeypairItemValue
    :raises KeyError
    """
    from openstack_cli.modules.openstack import VMKeypairItemValue

    k = self._storage.get_property(self._keys_table, name)
    if not k.name:
      raise KeyError(f"Key with name '{name}' not found")

    return VMKeypairItemValue(serialized_obj=k.value)

  def get_keys(self):
    """
    :rtype List[openstack_cli.modules.openstack.VMKeypairItemValue]
    """
    from openstack_cli.modules.openstack import VMKeypairItemValue

    items = self._storage.get_properties(self._keys_table)
    if not items:
      return []

    return [VMKeypairItemValue(serialized_obj=k.value) for k in items if k.value]

  @property
  def project(self) -> VMProject:
    p = self._storage.get_property(self._options_table, "project_data").value
    if p:
      return VMProject(serialized_obj=p)

    return VMProject()

  @project.setter
  def project(self, value: VMProject):
    self._storage.set_text_property(self._options_table, "project_data", value.serialize(), encrypted=True)

  @property
  def default_network(self):
    """
    To get default network please use networks#get_default_network

    :rtype openstack_cli.modules.openstack.objects.OSNetworkItem or None
    """
    from openstack_cli.modules.openstack.objects import OSNetworkItem
    raw = self._storage.get_property(self._options_table, "default_network", StorageProperty()).value

    try:
      return OSNetworkItem(serialized_obj=raw)
    except ValueError:
      pass

    return None

  @default_network.setter
  def default_network(self, value):
    """
    :type value openstack_cli.modules.openstack.objects.OSNetworkItem
    """
    raw = json.dumps(value.serialize())
    self._storage.set_text_property(self._options_table, "default_network", raw, encrypted=True)

  @property
  def auth_token(self):
    return self._storage.get_property(self._options_table, "auth_token").value

  @auth_token.setter
  def auth_token(self, value: str):
    self._storage.set_text_property(self._options_table, "auth_token", value, True)

  @property
  def user_id(self):
    return self._storage.get_property(self._options_table, "user_id").value

  @user_id.setter
  def user_id(self, value: str):
    self._storage.set_text_property(self._options_table, "user_id", value, encrypted=True)

  @property
  def default_vm_password(self):
    _pass = self._storage.get_property(self._options_table, "default_vm_password").value
    return _pass if _pass else "qwerty"

  @property
  def check_for_update(self) -> bool:
    if not self.cache.exists("UpdateClass"):
      self.cache.set("UpdateClass", "Aha-ha, here we are!")
      return True

    return False

  @default_vm_password.setter
  def default_vm_password(self, value: str):
    self._storage.set_text_property(self._options_table, "default_vm_password", value, True)

  @property
  def interface(self):
    return "public"

  @property
  def region(self):
    return self._storage.get_property(self._options_table, "region").value

  @region.setter
  def region(self, value):
    self._storage.set_text_property(self._options_table, "region", value, encrypted=True)

  @property
  def supported_os_names(self) -> List[str]:
    return ["sles", "rhel", "debian", "ubuntu", "centos", "opensuse"]

  @property
  def local_key_dir(self):
    return os.path.join(self._storage.configuration_dir, "keys")
