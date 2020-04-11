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

import sqlite3
import os
import json

from enum import Enum
from getpass import getpass
from typing import List, Callable
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
  def __init__(self, name: str, property_type: str, value: str or dict):
    self.__name: str = name
    self.__property_type: StoragePropertyType = StoragePropertyType.from_string(property_type)
    self.__value: str or dict = value

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
    self._db_connection: sqlite3.Connection = sqlite3.connect(self.configuration_file_path)
    self.__tables: List[str] = self.__get_table_list()

    if not lazy:
      self.initialize_key()

  def initialize_key(self):
    key = self._load_secret_key()
    self.__fernet: Fernet or None = Fernet(key) if key else None

  def _load_secret_key(self, persist: bool = False) -> str or None:
    def store_key(_key: bytes):
      with open(self.secret_file_path, "wb") as f:
        f.write(key)

    key_persisted = os.path.exists(self.secret_file_path)
    if not persist and not key_persisted:
      pw1 = getpass("Master password: ")
      key = self._generate_key(pw1)
      if not pw1:  # persist password-less key
        print("[I] Password-less mode selected, the key would be persisted and password not asked again")
        store_key(key)
      return key
    elif not persist and key_persisted:
      pass
    elif persist and not key_persisted:
      print("[W] No master password is set, creating new encryption key...")
      pw1 = getpass("Set master password (leave blank for no password): ")
      pw2 = getpass("Verify password: ")
      if pw1 != pw2:
        raise RuntimeError("Passwords didn't match!")

      print("Generating key, please wait...")
      key = self._generate_key(pw1)

      store_key(key)
      print(f"Key saved to {self.secret_file_path}, keep it save")
      return key

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
        raise RuntimeError("User key is invalid, unable to decrypt configuration data")
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
    create table {table}(name TEXT UNIQUE, type TEXT, store CLOB);
    """
    self.execute_script(sql)
    self.__tables.append(table)

  def get_property(self, table: str, name: str) -> StorageProperty or None:
    if table not in self.__tables:
      return None

    func: Callable[[sqlite3.Cursor], List[str] or None] = lambda x: x.fetchone()

    result_set = self._query(f"select type, store from {table} where name=?;", [name], func)
    if not result_set:
      return None

    p_type, p_value = result_set
    pt_type = StoragePropertyType.from_string(p_type)

    if pt_type == StoragePropertyType.encrypted:
      p_value = self._decrypt(p_value)

    if pt_type == StoragePropertyType.json:
      p_value = json.loads(p_value)

    return StorageProperty(name, p_type, p_value)

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
      prop.name
    ]
    if self.property_existed(table, prop.name):
      self._query(f"update {table} set store=?, type=? where name=?;", args, commit=True)
    else:
      self._query(f"insert into {table} (store, type, name) values (?,?,?);", args, commit=True)

  def property_existed(self, table: str, name: str):
    result_set = self._query(f"select store from {table} where name=?;", [table])
    return True if result_set else False
