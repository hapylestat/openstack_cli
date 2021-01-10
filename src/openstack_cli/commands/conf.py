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

import os
from typing import Dict, List

from openstack_cli.modules.apputils.terminal.colors import Colors, Symbols
from openstack_cli.core.output import Console, TableOutput, TableColumn, TableColumnPosition, StatusOutput
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo, CommandArgumentException
from openstack_cli.modules.openstack import OpenStack, VMKeypairItemValue
from openstack_cli.modules.openstack.api_objects import VMKeyPairItemBuilder
from openstack_cli.modules.openstack.objects import OSNetworkItem

command_help = [
  "Name of the command",
  "",
  "Available commands:  reset, reset-cache, network, keys",
  "",
  "reset                               - Completely reset application configuration",
  "reset-cache                         - Reset cached entities",
  "network                             - Reconfigure default network interface for the new VM",
  "keys [list|del|export|create] [arg] - Manage ssh keys for the VM"
]

subcommand_help = [
  "Subcommands for 'keys' command: ",
  "",
  "list                                - list available ssh keys",
  "del [name]                          - Delete ssh key, if no name provided the selection list would be provided",
  "export [name]                       - Export public and private keys to current directory",
  "create [name]                       - Create new pair of public/private keys"
]

__module__ = CommandMetaInfo("conf")
__args__ = __module__.arg_builder\
  .add_default_argument("command", str, "\n".join(command_help), default="help")\
  .add_default_argument("sub_command", str, "\n".join(subcommand_help), default="-")\
  .add_default_argument("arg", str, "sub command argument", default="")


CHECK_ICON = Symbols.CHECK.color(Colors.GREEN)
UNCHECK_ICON = Symbols.CROSS.color(Colors.RED)
KEY_ICON = Symbols.KEY.color(Colors.BRIGHT_YELLOW)


def configure_network(conf: Configuration):
  from openstack_cli.modules.openstack import OpenStack
  from openstack_cli.commands.networks import get_default_network

  old_network = conf.default_network

  if old_network:
    Console.print_warning(f"Previous network name: {old_network.name}")
    Console.print_warning("!!! THIS WILL CHANGE DEFAULT NETWORK !!!")

  net: OSNetworkItem = get_default_network(conf, OpenStack(conf), force=True)

  if net:
    print(f"\nSelected network: {net.name}")
    return

  Console.print_error("Network not set")


def _keys_create(conf: Configuration, ostack: OpenStack, name: str):
  from cryptography.hazmat.primitives import serialization as crypto_serialization
  from cryptography.hazmat.primitives.asymmetric import rsa
  from cryptography.hazmat.backends import default_backend as crypto_default_backend

  key = rsa.generate_private_key(
    backend=crypto_default_backend(),
    public_exponent=65537,
    key_size=2048
  )
  private_key = key.private_bytes(
    crypto_serialization.Encoding.PEM,
    crypto_serialization.PrivateFormat.PKCS8,
    crypto_serialization.NoEncryption())
  public_key = key.public_key().public_bytes(
    crypto_serialization.Encoding.OpenSSH,
    crypto_serialization.PublicFormat.OpenSSH
  )

  key = VMKeyPairItemBuilder()\
    .set_name(name)\
    .set_private_key(private_key)\
    .set_public_key(public_key)\
    .build()

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


def _keys_list(conf: Configuration, ostack: OpenStack, show_row_nums: bool = False) -> List[VMKeypairItemValue]:
  server_keypairs: Dict[int, VMKeypairItemValue] = {hash(key): key for key in ostack.get_keypairs()}
  conf_keys = conf.get_keys()
  if not conf_keys:
    Console.print_warning("No keys found, add new ones")
    return []

  max_key_len = len(max(conf.key_names))
  to = TableOutput(
    TableColumn("Key Name", max_key_len + len(KEY_ICON), inv_ch=len(KEY_ICON)-2, pos=TableColumnPosition.left),
    TableColumn("Priv.Key", 3, inv_ch=len(CHECK_ICON)-2, pos=TableColumnPosition.center),
    TableColumn("Pub.Key", 3, inv_ch=len(CHECK_ICON)-2, pos=TableColumnPosition.center),
    TableColumn("Rem.Sync", 3, inv_ch=len(CHECK_ICON), pos=TableColumnPosition.center),
    TableColumn("Fingerprint", 48, pos=TableColumnPosition.left),
    print_row_number=show_row_nums
  )

  to.print_header()

  for kp in conf_keys:
    to.print_row(
      f"{KEY_ICON}{kp.name}",
      CHECK_ICON if kp.private_key else UNCHECK_ICON,
      CHECK_ICON if kp.public_key else UNCHECK_ICON,
      CHECK_ICON if hash(kp) in server_keypairs else UNCHECK_ICON,
      server_keypairs[hash(kp)].fingerprint
    )

  return conf_keys


def _keys_del(conf: Configuration, ostack: OpenStack, name: str, force: bool = False):
  if not name:
    _keys = _keys_list(conf, ostack, True)
    item = Console.ask("Select key to remove", _type=int)
    if item is None:
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


def _keys_export(conf: Configuration, ostack: OpenStack, name: str):
  if not name:
    _keys = _keys_list(conf, ostack, True)
    item = Console.ask("Select key to export", _type=int)
    if item is None:
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


def keys(conf: Configuration, command: str, arg: str):
  supported_commands = ["list", "del", "export", "create"]

  if command == "-":
    command = "list"

  if command not in supported_commands:
    raise CommandArgumentException(f"conf keys command does not support the '{command}' sub-command")

  ostack = OpenStack(conf)

  if command == "list":
   _keys_list(conf, ostack)
  elif command == "del":
    _keys_del(conf, ostack, arg)
  elif command == "export":
    _keys_export(conf, ostack, arg)
  elif command == "create":
    _keys_create(conf, ostack, arg)
  else:
    raise NotImplementedError(f"Not implemented '{command}' sub-command")


def __init__(conf: Configuration, command: str, sub_command: str, arg: str):
  if command == "reset":
    conf.reset()
    print("Configuration reset completed")
  elif command == "reset-cache":
    conf.invalidate_cache()
    print("Cached data flushed")
  elif command == "network":
    configure_network(conf)
  elif command == "keys":
    keys(conf, sub_command, arg)
  else:
    raise CommandArgumentException(f"Command {command} is not supported")
