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

from openstack_cli.core.output import StatusOutput
from openstack_cli.modules.apputils.terminal import Console
from openstack_cli.modules.openstack import OpenStack
from openstack_cli.modules.openstack.api_objects import VMKeyPairItemBuilder, VMNewKeyPairItemBuilder
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo


__module__ = CommandMetaInfo("create", "Create new ssh keys")
__args__ = __module__.arg_builder\
  .add_default_argument("name", str, "Name of the key")

def _create_key(conf:Configuration, ostack:OpenStack, keyBuilder: VMKeyPairItemBuilder):
  key = keyBuilder.build()

  try:
    conf.add_key(key)
    ostack.create_key(key)

    Console.print(f"Key with name '{key.name}' successfully added")
  except ValueError as e:
    if ostack.has_errors:
      so = StatusOutput(None, pool_size=0, additional_errors=ostack.last_errors)
      so.check_issues()
    else:
      Console.print_error(f"Configuration already have the key with name {key.name}, please remove it first")


def __init__(conf: Configuration, name: str):
  ostack = OpenStack(conf)
  keyBuilder = VMNewKeyPairItemBuilder().set_name(name)
  _create_key(conf, ostack, keyBuilder)


