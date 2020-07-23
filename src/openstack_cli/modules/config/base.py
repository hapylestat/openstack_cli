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

import sys
import os


SECRET_FILE_NAME = "user.key"
CONFIGURATION_STORAGE_FILE_NAME = "configuration.db"


class BaseStorage(object):
  def __init__(self):
    if sys.platform.startswith('java'):
      import platform
      os_name = platform.java_ver()[3][0]
      if os_name.startswith('Windows'):
        self.__system: str = 'win32'
      elif os_name.startswith('Mac'):
        self.__system: str = 'darwin'
      else:
        self.__system: str = 'linux2'
    else:
      self.__system: str = sys.platform

      from openstack_cli import __app_name__ as app_name, __app_version__ as app_version
      self.__config_dir: str = self.__user_data_dir(appname=app_name, version=app_version)

      if self.__config_dir and not os.path.exists(self.__config_dir):
        os.makedirs(self.__config_dir, exist_ok=True)

  def __user_data_dir(self, appname: str = None, version: str = None) -> str:
    if self.__system == "win32":
      path = os.path.normpath(os.getenv("LOCALAPPDATA", None))
    elif self.__system == 'darwin':
      path = os.path.expanduser('~/Library/Application Support/')
    else:
      path = os.getenv('XDG_DATA_HOME', os.path.expanduser("~/.local/share"))

    if appname:
      path = os.path.join(path, appname)

    if appname and version:
      path = os.path.join(path, version)

    return path

  @property
  def configuration_dir(self) -> str:
    return self.__config_dir

  @property
  def secret_file_path(self) -> str:
    return os.path.join(self.__config_dir, SECRET_FILE_NAME)

  @property
  def configuration_file_path(self) -> str:
    return os.path.join(self.__config_dir, CONFIGURATION_STORAGE_FILE_NAME)
