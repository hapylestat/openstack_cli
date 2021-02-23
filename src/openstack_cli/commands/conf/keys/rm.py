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
from openstack_cli.commands.conf.keys.list import _keys_list
from openstack_cli.modules.openstack import OpenStack
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo

__module__ = CommandMetaInfo("rm", "Remove ssh key")
__args__ = __module__.arg_builder\
  .add_default_argument("name", str, "Name of the key to be removed", default="")\
  .add_argument("force", bool, "Force key removal", default=False)


def _keys_del(conf: Configuration, ostack: OpenStack, name: str, force: bool = False):
  if not name:
    _keys = _keys_list(conf, ostack, True)
    item = Console.ask("Select key to remove", _type=int)
    if item is None or item > len(_keys)-1:
      Console.print_warning("Invalid selection, aborting")
      return
    name = _keys[item].name

  if Console.ask_confirmation(f"Confirm removing key '{name}'", force=force):
    ostack.delete_keypair(name)
    if ostack.has_errors:
      so = StatusOutput(additional_errors=ostack.last_errors)
      so.check_issues()
    else:
      Console.print("Removed from the server")

    if not conf.delete_key(name):
      Console.print_error(f"Failed to remove key '{name}' from the configuration")
    else:
      Console.print("Removed from the configuration")

def __init__(conf: Configuration, name: str, force: bool):
  ostack = OpenStack(conf)
  _keys_del(conf, ostack, name, force)
