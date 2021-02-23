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

import os

from openstack_cli.commands.conf.keys.list import _keys_list
from openstack_cli.modules.apputils.terminal import Console
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo
from openstack_cli.modules.openstack import VMKeypairItemValue, OpenStack


__module__ = CommandMetaInfo("export", "Export ssh keys to disk")
__args__ = __module__.arg_builder\
  .add_default_argument("name", str, "Name of the key to be exported", default="")


def _keys_export(conf: Configuration, ostack: OpenStack, name: str):
  if not name:
    _keys = _keys_list(conf, ostack, True)
    item = Console.ask("Select key to export", _type=int)
    if item is None or item > len(_keys) - 1:
      Console.print_warning("Invalid selection, aborting")
      return
    name = _keys[item].name

  _key: VMKeypairItemValue
  try:
    _key = conf.get_key(name)
  except KeyError as e:
    Console.print_error(str(e))
    return

  d = os.getcwd()
  _public_file_path = os.path.join(d, f"{_key.name}.public.key")
  _private_file_path = os.path.join(d, f"{_key.name}.private.key")

  if _key.public_key:
    try:
      with open(_public_file_path, "w+", encoding="UTF-8") as f:
        f.write(_key.public_key)

      Console.print(f"Public key: {_public_file_path}")
    except IOError as e:
      Console.print_error(f"{_key.name}(public): {str(e)}")

  if _key.private_key:
    try:
      with open(_private_file_path, "w+", encoding="UTF-8") as f:
        f.write(_key.private_key)
      Console.print(f"Private key: {_private_file_path}")
    except IOError as e:
      Console.print_error(f"{_key.name}(private): {str(e)}")


def __init__(conf: Configuration, name: str):
  ostack = OpenStack(conf)
  _keys_export(conf, ostack, name)
