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
from typing import Tuple

from openstack_cli.core import dialogs
from openstack_cli.modules.openstack.api_objects import VMKeyPairItemBuilder
from openstack_cli.commands.conf.keys.rm import _keys_del
from openstack_cli.commands.conf.keys.create import _create_key
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo

__module__ = CommandMetaInfo("import", "import ssh fyes from disk")
__args__ = __module__.arg_builder \
  .add_default_argument("name", str, "Name of the key to be exported")\
  .add_argument("private", str, "Path to private key", default="")\
  .add_argument("public", str, "Path to public key", default="")

from openstack_cli.modules.openstack import OpenStack

def _check_keys(private: str, public: str, private_required: bool, public_required: bool) -> Tuple[str, str]:
  if not private and private_required:
    private = dialogs.ask_open_file("Select PRIVATE key")

  if not public and public_required:
    public = dialogs.ask_open_file("Select PUBLIC key")

  if private_required and not os.path.exists(private):
    raise FileExistsError(f"File '{private}' not exists")

  if public_required and not os.path.exists(public):
    raise FileExistsError(f"File '{public}' not exists")

  return private, public

def _get_file(path) -> str:
  with open(path, "r", encoding="UTF-8") as f:
    return f.read()

def __init__(conf: Configuration, name: str, private: str, public: str):
  if private == "@": private = ""
  if public == "@": public = ""

  ostack = OpenStack(conf)  # server keys are imported on object initialization

  if name not in conf.key_names:
    private, public = _check_keys(private, public, True, True)
    _create_key(conf, ostack,
      VMKeyPairItemBuilder()\
                .set_name(name)\
                .set_public_key(_get_file(public))\
                .set_private_key(_get_file(private))
    )
  else:
    _key = conf.get_key(name)
    if private and not public:
      public = _key.public_key
      private, _ = _check_keys(private, None, True, False)
      conf.delete_key(name)
      conf.add_key(VMKeyPairItemBuilder()\
                   .set_name(name)\
                   .set_private_key(_get_file(private))\
                   .set_public_key(public)\
                   .build()
      )
      print("Private key imported")
      return

    _keys_del(conf, ostack, name, True)
    private, public = _check_keys(private, public, True, True)
    _create_key(conf, ostack,
                VMKeyPairItemBuilder() \
                .set_name(name) \
                .set_public_key(_get_file(public)) \
                .set_private_key(_get_file(private))
                )
