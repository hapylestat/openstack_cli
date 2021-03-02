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

import sys
import time
from enum import Enum
from typing import  Dict, List

from .ext import DataCacheExtension, OptionsExtension
from .storages import StorageType
from .storages.base_storage import BaseStorage, StorageProperty, StoragePropertyType


class BaseConfiguration(object):
  __cache_invalidation: float = time.mktime(time.gmtime(8 * 3600))  # 8 hours
  _options_flags_name_old = "options"
  _options_flags_name = "config_options"
  _options_table = "general"

  class ConfigOptions(Enum):
    CONF_INITIALIZED = 0
    CREDENTIALS_CACHED = 1
    USE_MASTER_PASSWORD = 2

  def __init__(self, storage: StorageType = StorageType.SQL,
               app_name: str = 'apputils', lazy_init: bool = False, upgrade_manager=None):
    """
    :type upgrade_manager .upgrades.UpgradeManager
    """
    from .upgrades import UpgradeManager

    self.__upgrade_manager = upgrade_manager if upgrade_manager else UpgradeManager()
    self.__storage: BaseStorage = storage.value(app_name=app_name, lazy=lazy_init)
    self.__options = OptionsExtension(self.__storage, self._options_table, self._options_flags_name, self.ConfigOptions)
    self.__caches: Dict = {}

  def initialize(self):
    """
    :rtype BaseConfiguration
    """
    if self.is_conf_initialized:
      self._storage.initialize_key()
      try:
        assert self._test_encrypted_property == "test"
      except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(-1)

      self.__upgrade_manager.upgrade(self, self._storage)
    else:
      self.__upgrade_manager.init_config(self, self._storage)

    return self

  def add_cache_ext(self, name: str, cache_lifetime: float = __cache_invalidation):
    if name not in self.__caches:
      self.__caches[name] = DataCacheExtension(self.__storage, name, cache_lifetime)

  def get_cache_ext(self, name: str) -> DataCacheExtension:
    if name not in self.__caches:
      self.add_cache_ext(name)

    return self.__caches[name]

  @property
  def list_cache_ext(self) -> List[str]:
    return list(self.__caches.keys())

  @property
  def _storage(self) -> BaseStorage:
    return self.__storage

  @property
  def is_conf_initialized(self):
    return self.__options.get(self.ConfigOptions.CONF_INITIALIZED)

  @is_conf_initialized.setter
  def is_conf_initialized(self, value):
    self.__options.set(self.ConfigOptions.CONF_INITIALIZED, True)

  @property
  def __credentials_cached(self) -> bool:
    return self.__options.get(self.ConfigOptions.CREDENTIALS_CACHED)

  @__credentials_cached.setter
  def __credentials_cached(self, value: bool):
    self.__options.set(self.ConfigOptions.CREDENTIALS_CACHED, value)

  @property
  def __use_master_password(self):
    self.__options.get(self.ConfigOptions.USE_MASTER_PASSWORD)

  @__use_master_password.setter
  def __use_master_password(self, value: bool):
    self.__options.set(self.ConfigOptions.USE_MASTER_PASSWORD, value)

  @property
  def _test_encrypted_property(self):
    return self._storage.get_property(self._options_table, "enctest", StorageProperty()).value

  @_test_encrypted_property.setter
  def _test_encrypted_property(self, value):
    self._storage.set_text_property(self._options_table, "enctest", value, encrypted=True)

  @property
  def version(self) -> float:
    p = self._storage.get_property("general", "db_version", StorageProperty(name="db_version", value="0.0"))
    try:
      return float(p.value)
    except ValueError:
      return 0.0

  @version.setter
  def version(self, version: float):
    self._storage.set_property("general", StorageProperty(name="db_version", value=str(version)))

  def reset(self):
    self._storage.reset()

