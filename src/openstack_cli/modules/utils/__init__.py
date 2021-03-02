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


class ValueHolder(object):
  def __init__(self, v_amount: int = 0, values: list = ()):
    if values and len(values) == v_amount:
      self.__values = values
    else:
      self.__values = [0] * v_amount


  def set_if_bigger(self, n: int or Enum[int], v):
    if isinstance(n, Enum):
      n = n.value

    if  v > self.__values[n]:
      self.__values[n] = v

  def set(self, n: int or Enum[int], v):
    if isinstance(n, Enum):
      n = n.value

    self.__values[n] = v

  def get(self, n: int or Enum[int]):
    if isinstance(n, Enum):
      n = n.value
    return self.__values[n]
