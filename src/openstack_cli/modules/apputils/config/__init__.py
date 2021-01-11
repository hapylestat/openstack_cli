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
from typing import ClassVar

from .sql_storage import SQLStorage, StorageProperty, StoragePropertyType


class BaseConfiguration(object):
  __cache_invalidation: float = time.mktime(time.gmtime(8 * 3600))  # 8 hours
  _options_table = "general"
  __cache_table = "cache"

  __options_amount = 3
  __options_flags_name = "options"
  __option_conf_initialized = 0
  __option_credentials_cached = 1
  __option_use_master_password = 2

  def __init__(self, upgrade_manager=None):
    """
    :type upgrade_manager .upgrades.UpgradeManager
    """
    from .upgrades import UpgradeManager

    self.__upgrade_manager = upgrade_manager if upgrade_manager else UpgradeManager()
    self.__storage = SQLStorage(lazy=True)
    self.__options = [0] * self.__options_amount

  def initialize(self):
    """
    :rtype BaseConfiguration
    """
    self.__read_options()
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

  def __read_options(self):
    if self._options_table in self._storage.tables:
      opts = self._storage.get_property(self._options_table, self.__options_flags_name)
      if opts.value:
        self.__options = [int(ch) for ch in opts.value]

  def __save_options(self):
    val = ''.join([str(ch) for ch in self.__options])
    self._storage.set_text_property(self._options_table, self.__options_flags_name, val)

  @property
  def _storage(self) -> SQLStorage:
    return self.__storage

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
  def _test_encrypted_property(self):
    return self._storage.get_property(self._options_table, "enctest", StorageProperty()).value

  @_test_encrypted_property.setter
  def _test_encrypted_property(self, value):
    self._storage.set_text_property(self._options_table, "enctest", value, encrypted=True)

  def invalidate_cache(self):
    self._storage.reset_properties_update_time(self.__cache_table)

  def is_cached(self, clazz: ClassVar) -> bool:
    p: StorageProperty = self._storage.get_property(self.__cache_table, clazz.__name__)

    if p.updated:
      time_delta: float = time.time() - p.updated
      if time_delta >= self.__cache_invalidation:
        return False
    return p.value not in ('', {})

  def get_cache(self, clazz: ClassVar) -> str or dict or None:
    p: StorageProperty = self._storage.get_property(self.__cache_table, clazz.__name__)

    if p.updated:
      time_delta: float = time.time() - p.updated
      if time_delta >= self.__cache_invalidation:
        return None

    return p.value

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

  def set_cache(self, clazz: ClassVar, v: str or dict):
    self._storage.set_text_property(self.__cache_table, clazz.__name__, v, encrypted=True)

  def reset(self):
    self._storage.reset()

