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
#  Github: https://github.com/hapylestat/apputils
#
#

import sqlite3
import os
import json
import time

from typing import List, Callable
from .base_storage import BaseStorage, StoragePropertyType, StorageProperty


class SQLStorage(BaseStorage):
  __tables: List[str] = None

  def __init__(self, app_name: str = "apputils", lazy: bool = False):
    super(SQLStorage, self).__init__(app_name, lazy)

    self._db_connection: sqlite3.Connection = sqlite3.connect(self.configuration_file_path, check_same_thread=False)
    self.__tables: List[str] = self.__get_table_list()

  def reset(self):
    if self._db_connection:
      self._db_connection.close()

    if os.path.exists(self.secret_file_path):
      os.remove(self.secret_file_path)

    if os.path.exists(self.configuration_file_path):
      os.remove(self.configuration_file_path)

    self._db_connection = sqlite3.connect(self.configuration_file_path, check_same_thread=False)

  def _query(self,
             sql: str = None,
             args: list = None,
             f: Callable[[sqlite3.Cursor], List[list] or List[str] or None] = None,
             commit: bool = False):
    """
    Usage example:

    func: Callable[[sqlite3.Cursor], List[str] or None] = lambda x: x.fetchone()
    result_set: List[str] or None = self._query(f"select store from {table} where name=?;", [name], func)
    """

    cur = self._db_connection.cursor()
    try:
      if sql:
        if args:
          cur.execute(sql, args)
        else:
          cur.execute(sql)

      if f:
        return f(cur)
      else:
        return cur.fetchall()
    finally:
      if commit:
        self._db_connection.commit()
      cur.close()

  def __get_table_list(self) -> List[str] or None:
    result_set = self._query("select name from sqlite_master where type = 'table';")
    return list(map(lambda x: '' if x is None or len(x) == 0 else x[0], result_set))

  @property
  def tables(self):
    return self.__tables

  @property
  def connection(self) -> sqlite3.Connection:
    return self._db_connection

  def execute_script(self, ddl: str) -> None:
    self._query(f=lambda cur: cur.executescript(ddl))

  def _create_property_table(self, table: str):
    sql = f"""
    DROP TABLE IF EXISTS {table};
    create table {table}(name TEXT UNIQUE, type TEXT, updated REAL DEFAULT 0, store CLOB);
    """
    self.execute_script(sql)
    self._db_connection.commit()
    self.__tables.append(table)

  def reset_property_update_time(self, table: str, name: str or StorageProperty):
    if isinstance(name, StorageProperty):
      name = name.name
    self._query(f"update {table} set updated=0.1 where name='{name}'", commit=True)

  def reset_properties_update_time(self, table: str):
    self._query(f"update {table} set updated=0.1", commit=True)

  def get_property_list(self, table: str) -> List[str]:
    if table not in self.__tables:
      return []

    result_set = self._query(f"select name from {table}")
    if not result_set:
      return []

    return [item[0] for item in result_set]

  def __transform_property_value(self, name: str, p_type: str, p_updated: str, p_value: str) -> StorageProperty:
    pt_type = StoragePropertyType.from_string(p_type)

    if pt_type == StoragePropertyType.encrypted:
      p_value = self._decrypt(p_value)

    if pt_type == StoragePropertyType.json:
      p_value = json.loads(p_value)

    return StorageProperty(name, StoragePropertyType.from_string(p_type), p_value, p_updated)

  def get_properties(self, table: str) -> List[StorageProperty]:
    """
    Return array of properties in form of:
    ...
    key_name, key_value
    ...
    """
    if table not in self.__tables:
      return []

    result_set = self._query(f"select name, type, updated, store from {table}")
    return [self.__transform_property_value(*item) for item in result_set]

  def get_property(self, table: str, name: str, default=StorageProperty()) -> StorageProperty:
    if table not in self.__tables:
      return default

    func: Callable[[sqlite3.Cursor], List[str] or None] = lambda x: x.fetchone()

    result_set = self._query(f"select type, updated, store from {table} where name=?;", [name], func)
    if not result_set:
      return default

    p_type, p_updated, p_value = result_set

    return self.__transform_property_value(name, p_type, p_updated, p_value)

  def set_property(self, table: str, prop: StorageProperty, encrypted: bool = False):
    if table not in self.__get_table_list():
      self._create_property_table(table)

    if not encrypted and prop.property_type == StoragePropertyType.encrypted:
      encrypted = True

    if encrypted:
      prop.property_type = StoragePropertyType.encrypted

    args = [
      self._encrypt(prop.str_value) if encrypted else prop.str_value,
      prop.property_type.value,
      time.time(),
      prop.name
    ]
    if self.property_existed(table, prop.name):
      self._query(f"update {table} set store=?, type=?, updated=? where name=?;", args, commit=True)
    else:
      self._query(f"insert into {table} (store, type, updated, name) values (?,?,?,?);", args, commit=True)

  def delete_property(self, table: str, name: str) -> bool:
    if table not in self.__tables:
      return True

    if not self.property_existed(table, name):
      return True

    self._query(f"delete from {table} where name=?", [name], commit=True)
    return True

  def set_text_property(self, table: str, name: str, value, encrypted: bool = False):
    p = StorageProperty(name, StoragePropertyType.text, value)
    self.set_property(table, p, encrypted)

  def property_existed(self, table: str, name: str) -> bool:
    if table not in self.__get_table_list():
      return False

    result_set = self._query(f"select store from {table} where name=?;", [name])
    return True if result_set else False
