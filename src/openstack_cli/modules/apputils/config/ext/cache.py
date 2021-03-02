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
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  Github: https://github.com/hapylestat/apputils
#
#

import time
from typing import ClassVar

from ..storages.base_storage import BaseStorage, StorageProperty


class DataCacheExtension(object):
  def __init__(self, _storage: BaseStorage,  table_name: str, cache_lifetime: float):  # seconds
    self._storage: BaseStorage = _storage
    self.__cache_table_name: str = table_name
    self.__cache_lifetime: float = cache_lifetime

  def invalidate_all(self):
    self._storage.reset_properties_update_time(self.__cache_table_name)

  def invalidate_property(self, name: StorageProperty or str):
    self._storage.reset_property_update_time(self.__cache_table_name, name)

  def exists(self, clazz: ClassVar or str) -> bool:
    if not isinstance(clazz, str):
      clazz = clazz.__name__

    p: StorageProperty = self._storage.get_property(self.__cache_table_name, clazz)

    if p.updated:
      time_delta: float = time.time() - p.updated
      if time_delta >= self.__cache_lifetime:
        return False
    return p.value not in ('', {})

  def get(self, clazz: ClassVar or str) -> str or dict or None:
    if not isinstance(clazz, str):
      clazz = clazz.__name__

    p: StorageProperty = self._storage.get_property(self.__cache_table_name, clazz)

    if p.updated:
      time_delta: float = time.time() - p.updated
      if time_delta >= self.__cache_lifetime:
        return None

    return p.value

  def set(self, clazz: ClassVar or str, v: str or dict, encrypted: bool = True):
    if not isinstance(clazz, str):
      clazz = clazz.__name__

    self._storage.set_text_property(self.__cache_table_name, clazz, v, encrypted=encrypted)
