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

from enum import Enum
from typing import Dict


from ..storages.base_storage import BaseStorage, StorageProperty, StoragePropertyType


class OptionsExtension(object):
  """
    Boolean options holder in the bitfield

    Example:

      class MyOptions(Enum):
         STARTING = 0  # bit number
         BOOTING = 1   # bit number

      opts = OptionsExtension(storage, "mytable", "myoption", MyOptions, false)
      opts.set(MyOptions.STARTING, False)
  """

  def __init__(self, storage: BaseStorage, table_name: str, holder_prop_name: str, properties: Enum,
               encrypted: bool = False):
    self._storage = storage
    self.__encrypted: bool = encrypted
    self.__table_name: str = table_name
    self.__property_name = holder_prop_name
    self.__props: Dict[str, Enum[str, int]] = dict(sorted(  # required to preserve properties order
      {v.name: int(v.value) for k, v in properties.__dict__.items() if isinstance(k, str) and isinstance(v, Enum)}.items(),
      key=lambda x: x[0]
    ))
    self.__bitfield: int = 0
    self.__bitmask_len = len(self.__props)
    self.__bitmask: int = self.__gen_bitmask(self.__bitmask_len)
    self.__loaded: bool = False

  def __load_value(self):
    p = self._storage.get_property(self.__table_name, self.__property_name)
    if p and p.value and p.value.isnumeric():
      self.__bitfield = int(p.value)
    else:
      self.__bitfield = 0
    self.__loaded = True

  def __save_value(self):
    self._storage.set_property(
      self.__table_name,
      StorageProperty(self.__property_name, StoragePropertyType.text, str(self.__bitfield)),
      encrypted=self.__encrypted
    )

  def __gen_bitmask(self, width: int) -> int:
    return (width << 1) - 1

  def _get_bit(self, _bitfield: int, n: int) -> bool:
    return (_bitfield >> n) & self.__bitmask == 1

  def _set_bit(self, _bitfield: int, n: int, v:bool) -> int:
    value = 1 if v else 0
    return _bitfield | (value << n)

  def get(self, prop: Enum) -> bool:
    if not self.__loaded:
      self.__load_value()

    return self._get_bit(self.__bitfield, int(prop.value))

  def set(self, prop: Enum, v: bool):
    if not self.__loaded:
      self.__load_value()

    self.__bitfield = self._set_bit(self.__bitmask, int(prop.value), 1 if v else 0)
    self.__save_value()
