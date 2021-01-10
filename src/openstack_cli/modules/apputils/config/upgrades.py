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

from collections import defaultdict, OrderedDict
from getpass import getpass
from typing import List, Dict

from . import BaseConfiguration
from .sql_storage import SQLStorage


class NoUpgradeNeeded(BaseException):
  """
  Required to signal that further upgrade is not required
  """
  pass


class UpgradeCatalog(object):
  def __init__(self, conf: BaseConfiguration, storage: SQLStorage = None, catalog_version: float = None):
    self._storage = storage if storage else conf._storage
    self._conf = conf
    self._catalog_version = catalog_version

  def ask_text_question(self, prompt: str, encrypted: bool = False) -> str:
    f = getpass if encrypted else input
    answer = f(prompt)
    return answer

  def ask_question(self, prompt: str, encrypted: bool = False) -> bool:
    answer = self.ask_text_question(prompt, encrypted).lower()
    return answer == "y" or answer == "yes"

  def __call__(self, *args, **kwargs):
    raise NotImplementedError()


UPGRADE_CATALOGS: Dict[float, List[UpgradeCatalog]] = defaultdict(lambda: [])


def upgrade(version: float = 0.0):
  def wrapper(cls: UpgradeCatalog):
    global UPGRADE_CATALOGS
    UPGRADE_CATALOGS[version].append(cls)

  return wrapper


class UpgradeManager(object):
  def __ask_text_question(self, prompt: str, encrypted: bool = False) -> str:
    f = getpass if encrypted else input
    answer = f(prompt)
    return answer

  def __ask_question(self, prompt: str, encrypted: bool = False) -> bool:
    answer = self.__ask_text_question(prompt, encrypted).lower()
    return answer == "y" or answer == "yes"

  def init_config(self, conf: BaseConfiguration, storage: SQLStorage):
    use_master_password: bool =  self.__ask_question("Secure configuration with master password (y/n): ")
    if use_master_password:
      store_encryption_key: bool = self.__ask_question("Cache encryption key on disk (y/n): ")
    else:  # if not master key is used, default one would be generated anyway
      store_encryption_key: bool = True

    storage.create_key(store_encryption_key, None if use_master_password else "")
    storage.initialize_key()

    conf.credentials_cached = store_encryption_key
    conf.use_master_password = use_master_password

    conf._test_encrypted_property = "test"

    self.upgrade(conf, storage)

    conf.is_conf_initialized = True

  def upgrade_required(self, conf: BaseConfiguration):
    global UPGRADE_CATALOGS
    if 0.0 not in UPGRADE_CATALOGS or not UPGRADE_CATALOGS[0.0]:
      return False

    try:
      catalog = UPGRADE_CATALOGS[0.0][0]
      catalog(conf)()
    except NoUpgradeNeeded:
      return False

    return True

  def upgrade(self, conf: BaseConfiguration, storage: SQLStorage):
    global UPGRADE_CATALOGS
    if not isinstance(UPGRADE_CATALOGS, OrderedDict):
      UPGRADE_CATALOGS = OrderedDict(sorted(UPGRADE_CATALOGS.items()))

    for version, catalogs in UPGRADE_CATALOGS.items():
      for catalog in catalogs:
        try:
          catalog(conf, storage, version)()
        except NoUpgradeNeeded:
          return
        except Exception as e:
          print(f"Problem occur with upgrade catalog version: {version}")
          raise e
