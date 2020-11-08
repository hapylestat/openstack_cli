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

import json
import sys
import time
from getpass import getpass
from typing import List, ClassVar

from openstack_cli.modules.config.storage import SQLStorage, StorageProperty, StoragePropertyType


class Configuration(object):
  __cache_invalidation: float = time.mktime(time.gmtime(8 * 3600))  # 8 hours
  __options_table = "general"
  __cache_table = "cache"
  __keys_table = "keys"

  __options_amount = 3
  __options_flags_name = "options"
  __option_conf_initialized = 0
  __option_credentials_cached = 1
  __option_use_master_password = 2

  def __init__(self):
    self.__storage = SQLStorage(lazy=True)
    self.__options = [0] * self.__options_amount

  def initialize(self):
    self.__read_options()
    if self.is_conf_initialized:
      self.__storage.initialize_key()
      try:
        assert self.__test_encrypted_property == "test"
      except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(-1)
    else:
      self.__initial_configuration()

  def __read_options(self):
    if self.__options_table in self.__storage.tables:
      opts = self.__storage.get_property(self.__options_table, self.__options_flags_name)
      if opts.value:
        self.__options = [int(ch) for ch in opts.value]

  def __save_options(self):
    val = ''.join([str(ch) for ch in self.__options])
    self.__storage.set_text_property(self.__options_table, self.__options_flags_name, val)

  def __ask_text_question(self, prompt: str, encrypted: bool = False) -> str:
    f = getpass if encrypted else input
    answer = f(prompt)
    return answer

  def __ask_question(self, prompt: str, encrypted: bool = False) -> bool:
    answer = self.__ask_text_question(prompt, encrypted).lower()
    return answer == "y" or answer == "yes"

  @property
  def is_conf_initialized(self):
    return self.__options[self.__option_conf_initialized] == 1

  @is_conf_initialized.setter
  def is_conf_initialized(self, value):
    self.__options[self.__option_conf_initialized] = 1  # only True could be
    self.__save_options()

  @property
  def __credentials_cached(self) -> bool:
    return self.__options[self.__options_amount] == 1

  @__credentials_cached.setter
  def __credentials_cached(self, value: bool):
    self.__options[self.__option_credentials_cached] = 1 if value else 0
    self.__save_options()

  @property
  def __use_master_password(self):
    return self.__options[self.__option_use_master_password] == 1

  @__use_master_password.setter
  def __use_master_password(self, value: bool):
    self.__options[self.__option_use_master_password] = 1 if value else 0
    self.__save_options()

  @property
  def os_address(self) -> str:
    return self.__storage.get_property(self.__options_table, "os_address", StorageProperty()).value

  @os_address.setter
  def os_address(self, value: str):
    self.__storage.set_text_property(self.__options_table, "os_address", value)

  @property
  def os_login(self) -> str:
    return self.__storage.get_property(self.__options_table, "os_login", StorageProperty()).value

  @os_login.setter
  def os_login(self, value: str):
    self.__storage.set_text_property(self.__options_table, "os_login", value, encrypted=True)

  @property
  def os_password(self) -> str:
    return self.__storage.get_property(self.__options_table, "os_password", StorageProperty()).value

  @os_password.setter
  def os_password(self, value: str):
    self.__storage.set_text_property(self.__options_table, "os_password", value, encrypted=True)

  @property
  def key_names(self) -> List[str]:
    return self.__storage.get_property_list(self.__keys_table)

  def add_key(self, key):
    """
    :type key: openstack_cli.modules.openstack.VMKeypairItemValue
    """
    if key.name in self.key_names:
      raise ValueError(f"Key with name '{key.name}' already exists")

    self.__storage.set_text_property(self.__keys_table, key.name, key.to_json(), True)

  def delete_key(self, name: str) -> bool:
    if name in self.key_names:
      return self.__storage.delete_property(self.__keys_table, name)
    return True

  def get_key(self, name: str):
    """
    :rtype openstack_cli.modules.openstack.VMKeypairItemValue
    :raises KeyError
    """
    from openstack_cli.modules.openstack import VMKeypairItemValue

    k = self.__storage.get_property(self.__keys_table, name)
    if not k.name:
      raise KeyError(f"Key with name '{name}' ot found")

    return VMKeypairItemValue(serialized_obj=k.value)

  def get_keys(self):
    """
    :rtype List[openstack_cli.modules.openstack.VMKeypairItemValue]
    """
    from openstack_cli.modules.openstack import VMKeypairItemValue

    items = self.__storage.get_properties(self.__keys_table)
    if not items:
      return []

    return [VMKeypairItemValue(serialized_obj=k.value) for k in items if k.value]

  @property
  def default_network(self):
    """
    To get default network please use networks#get_default_network

    :rtype openstack_cli.modules.openstack.objects.OSNetworkItem or None
    """
    from openstack_cli.modules.openstack.objects import OSNetworkItem
    raw = self.__storage.get_property(self.__options_table, "default_network", StorageProperty()).value

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
    self.__storage.set_text_property(self.__options_table, "default_network", raw, encrypted=True)

  @property
  def __test_encrypted_property(self):
    return self.__storage.get_property(self.__options_table, "enctest", StorageProperty()).value

  @property
  def auth_token(self):
    return self.__storage.get_property(self.__options_table, "auth_token").value

  @auth_token.setter
  def auth_token(self, value: str):
    self.__storage.set_text_property(self.__options_table, "auth_token", value, True)

  def invalidate_cache(self):
    self.__storage.reset_properties_update_time(self.__cache_table)

  def is_cached(self, clazz: ClassVar) -> bool:
    p: StorageProperty = self.__storage.get_property(self.__cache_table, clazz.__name__)

    if p.updated:
      time_delta: float = time.time() - p.updated
      if time_delta >= self.__cache_invalidation:
        return False
    return p.value not in ('', {})

  @property
  def default_vm_password(self):
    _pass = self.__storage.get_property(self.__options_table, "default_vm_password").value
    return _pass if _pass else "qwerty"

  @default_vm_password.setter
  def default_vm_password(self, value: str):
    self.__storage.set_text_property(self.__options_table, "default_vm_password", value, True)

  def get_cache(self, clazz: ClassVar) -> str or dict or None:
    p: StorageProperty = self.__storage.get_property(self.__cache_table, clazz.__name__)

    if p.updated:
      time_delta: float = time.time() - p.updated
      if time_delta >= self.__cache_invalidation:
        return None

    return p.value

  def set_cache(self, clazz: ClassVar, v: str or dict):
    self.__storage.set_text_property(self.__cache_table, clazz.__name__, v, encrypted=True)

  @__test_encrypted_property.setter
  def __test_encrypted_property(self, value):
    self.__storage.set_text_property(self.__options_table, "enctest", value, encrypted=True)

  @property
  def interface(self):
    return "public"

  @property
  def region(self):
    return "RegionOne"

  @property
  def supported_os_names(self) -> List[str]:
    return ["sles", "rhel", "debian", "ubuntu", "centos", "opensuse"]

  def __initial_configuration(self):
    print("""
    ..#######...######..##.....##.##.....##
    .##.....##.##....##.##.....##.###...###
    .##.....##.##.......##.....##.####.####
    .##.....##..######..##.....##.##.###.##
    .##.....##.......##..##...##..##.....##
    .##.....##.##....##...##.##...##.....##
    ..#######...######.....###....##.....##

    OpenStack tool need to be configured first before it could be used.
    Please answer several questions below to personalize your experience:

    """)

    use_master_password: bool = self.__ask_question("Secure configuration with master password (y/n): ")
    if use_master_password:
      store_encryption_key: bool = self.__ask_question("Cache encryption key on disk (y/n): ")
    else:  # if not master key is used, default one would be generated anyway
      store_encryption_key: bool = True

    self.__storage.create_key(store_encryption_key, None if use_master_password else "")
    self.__storage.initialize_key()

    self.__credentials_cached = store_encryption_key
    self.__use_master_password = use_master_password

    from openstack_cli.modules.openstack import OpenStack

    self.os_address = self.__ask_text_question("OpenStack address: ")
    self.os_login = self.__ask_text_question("OpenStack login: ")
    self.os_password = self.__ask_text_question("OpenStack password", encrypted=True)

    osvm = OpenStack(self)

    self.__test_encrypted_property = "test"

    _p = getpass("Default VM password: ")
    if not _p:  # ToDo: add more strict check
      _p = "qwerty"
    self.default_vm_password = _p

    self.is_conf_initialized = True
    print("Tool configuration is done, thanks!")

  def reset(self):
    self.__storage.reset()

