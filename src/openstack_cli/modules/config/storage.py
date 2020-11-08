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

# =========================================================================
# The library is a part of AppUtils library
# GitHub: https://github.com/hapylestat/apputils
# Contacts: hapy.lestat@gmail.com
# =========================================================================

import sqlite3
import os
import json

import time
from enum import Enum
from getpass import getpass
from typing import List, Callable, Tuple, Iterable
from openstack_cli.modules.config.base import BaseStorage
from cryptography.fernet import Fernet, InvalidToken


class StoragePropertyType(Enum):
  text = "text"
  encrypted = "encrypted"
  json = "json"

  @classmethod
  def from_string(cls, property_type: str):
    """
    :rtype StoragePropertyType
    """
    if property_type == "text":
      return cls.text
    elif property_type == "encrypted":
      return cls.encrypted
    elif property_type == "json":
      return cls.json

    return cls.text


class StorageProperty(object):
  def __init__(self, name: str = "", property_type: StoragePropertyType = StoragePropertyType.text or str,
               value: str or dict = "", updated: float or None = None):
    self.__name: str = name
    if isinstance(property_type, StoragePropertyType):
      self.__property_type: StoragePropertyType = property_type
    elif isinstance(property_type, str):
      self.__property_type: StoragePropertyType = StoragePropertyType.from_string(property_type)
    else:
      self.__property_type: StoragePropertyType = StoragePropertyType.text
    self.__value: str or dict = value
    self.__updated: float = updated if updated else time.time()

  @property
  def name(self):
    return self.__name

  @property
  def property_type(self):
    return self.__property_type

  @property_type.setter
  def property_type(self, value: StoragePropertyType):
    self.__property_type = value

  @property
  def value(self):
    return self.__value

  @property
  def updated(self) -> float:
    return self.__updated

  @property
  def str_value(self):
    if isinstance(self.__value, dict):
      return json.dumps(self.__value)
    elif isinstance(self.__value, str):
      return self.__value
    else:
      return str(self.__value)


class SQLStorage(BaseStorage):
  __tables: List[str] = None
  __key_encoding = "UTF-8"

  def __init__(self, lazy: bool = False):
    super(SQLStorage, self).__init__()

    self.__fernet: Fernet or None = None
    self._db_connection: sqlite3.Connection = sqlite3.connect(self.configuration_file_path, check_same_thread=False)
    self.__tables: List[str] = self.__get_table_list()

    if not lazy:
      self.initialize_key()

  def initialize_key(self):
    persist = os.path.exists(self.secret_file_path)
    key = self._load_secret_key(persist=persist)
    self.__fernet: Fernet or None = Fernet(key) if key else None

  def reset(self):
    if self._db_connection:
      self._db_connection.close()

    if os.path.exists(self.secret_file_path):
      os.remove(self.secret_file_path)

    if os.path.exists(self.configuration_file_path):
      os.remove(self.configuration_file_path)

    self._db_connection = sqlite3.connect(self.configuration_file_path, check_same_thread=False)

  def create_key(self, persist: bool, master_password: str):
    if persist and master_password is None:
      print("Notice: With no password set would be generated default PC-depended encryption key")
      pw1 = getpass("Set master password (leave blank for no password): ")
      pw2 = getpass("Verify password: ")
      if pw1 != pw2:
        raise RuntimeError("Passwords didn't match!")
      master_password = pw1

    if os.path.exists(self.secret_file_path):
      print("Resetting already existing encryption key")
      self.reset()

    if master_password is not None and not master_password:  # i.e. pass = ""
      persist = True

    if persist:
      print("Generating key, please wait...")
      key = self._generate_key(master_password)
      with open(self.secret_file_path, "wb") as f:
        f.write(key)

      print(f"Key saved to {self.secret_file_path}, keep it save")

  def _load_secret_key(self, persist: bool = False) -> str or None:
    if persist and not os.path.exists(self.secret_file_path):
      raise RuntimeError("Master key is not found, please re-configure tool")

    if not persist:
      pw1 = getpass("Master password: ")
      return self._generate_key(pw1)
    else:
      with open(self.secret_file_path, "r") as f:
        return f.readline().strip(os.linesep)

  def _generate_key(self, password: str) -> bytes:
    import platform
    import base64
    import hashlib
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    sha512_hash = hashlib.sha512()
    sha512_hash.update(f"{platform.processor()}".encode(encoding=self.__key_encoding))
    salt = sha512_hash.digest()
    kdf = PBKDF2HMAC(
      algorithm=hashes.SHA3_256(),
      length=32,
      salt=salt,
      iterations=300000,
      backend=default_backend()
    )

    return base64.urlsafe_b64encode(kdf.derive(password.encode(self.__key_encoding)))

  def _encrypt(self, value: str) -> str:
    if self.__fernet:
      return self.__fernet.encrypt(value.encode(self.__key_encoding))
    return value

  def _decrypt(self, value: str) -> str:
    if self.__fernet:
      try:
        return self.__fernet.decrypt(value).decode("utf-8")
      except InvalidToken:
        raise ValueError("Provided key is invalid, unable to decrypt encrypted data")
    return value

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
    self.__tables.append(table)

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
    if table not in self.__tables:
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
    result_set = self._query(f"select store from {table} where name=?;", [name])
    return True if result_set else False
