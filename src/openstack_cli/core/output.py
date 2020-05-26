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


class TableColumn(object):
  def __init__(self, name: str, length: int):
    self.name = name
    self.length = length


class TableSizeColumn(object):
  def __init__(self, value: int):
    self.__value = value

  @property
  def value(self):
    return str(self)

  def __str__(self):
    if self.__value is None:
      return "0 b"

    if self.__value < 1000:
      return f"{self.__value} b"

    val = self.__value / 1000.0
    if val < 1000:
      return f"{val:0.2f} kb"

    val = val / 1000.0
    if val < 1000:
      return f"{val:0.2f} mb"

    val = val / 1000.0
    if val < 1000:
      return f"{val:0.2f} gb"

    val = val / 1000.0
    return f"{val:0.2f} tb"


class TableOutput(object):
  def __init__(self, *columns: TableColumn):
    self.__columns = columns
    self.__column_pattern = "  ".join([f"{{:<{c.length}}}" for c in columns])
    self.__sep_columns = sep_header = ["-" * c.length for c in columns]

  def print_header(self):
    print(self.__column_pattern.format(*[c.name for c in self.__columns]))
    print(self.__column_pattern.format(*self.__sep_columns))

  def print_row(self, *values: str):
    print(self.__column_pattern.format(*values))
