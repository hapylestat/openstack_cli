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

import asyncio
import os
import sys
from typing import List

from openstack_cli.modules.discovery.arguments import CommandLineOptions
from openstack_cli.modules.discovery.commands import CommandMetaInfo, NoCommandException, CommandArgumentException, \
  CommandModules, CommandModule


class CommandsDiscovery(object):
  def __init__(self,
               discovery_location_path: str,
               module_class_path: str,
               file_pattern: str = "",
               module_main_fname: str = "__init__"):

    self._discovery_location_path = discovery_location_path
    self._module_main_fname = module_main_fname
    self._file_pattern = file_pattern
    self._options: CommandLineOptions = CommandLineOptions()

    if os.path.isfile(self._discovery_location_path):
      self._search_dir = os.path.dirname(os.path.abspath(self._discovery_location_path))
    else:
      self._search_dir = self._discovery_location_path

    self._module_class_path = module_class_path
    self._modules = CommandModules(entry_point=module_main_fname)

  @property
  def search_dir(self) -> str:
    return self._search_dir

  def collect(self):
    """
    :rtype CommandsDiscovery
    """
    exclude_list = ["pyc", "__init__.py", "__pycache__"]

    for name in os.listdir(self._search_dir):
      if name in exclude_list:
        continue

      command_filename = name.partition(".")[0]
      if command_filename not in self._modules and (
        (self._file_pattern and self._file_pattern in name) or not self._file_pattern
      ):
        self._modules.add(self._module_class_path, command_filename)
      else:
        continue  # ignoring any non-matched file

    return self

  def generate_help(self, filename: str = "", command: str = ""):
    help_str = "{} [{}]\n\n".format(filename, "|".join(self._modules.commands))
    help_str += """\n\nAvailable commands:

    """
    command_list = self._modules.commands if command == "" else [command]

    for command in command_list:
      cmd_meta: CommandMetaInfo = self._modules[command].meta_info

      if not cmd_meta:
        continue

      args = {}
      args.update(cmd_meta.get_arguments_builder().arguments)
      args.update(cmd_meta.get_arguments_builder().default_arguments)

      cmd_arguments_help = {name: value.item_help for name, value in args.items() if value.item_help}

      if len(cmd_arguments_help) > 0:
        help_str += """
        {cmd} [{args}] - {cmd_help}

        Argument details:
        {arg_details}


        """.format(
          cmd=command,
          args=" | ".join(cmd_arguments_help.keys()),
          cmd_help=cmd_meta.help,
          arg_details="\n".join(["{} - {}".format(k, v) for k, v in cmd_arguments_help.items()])
        )

      else:
        help_str += """
        {cmd} - {cmd_help}""".format(
          cmd=command,
          cmd_help=cmd_meta.help
        )
    return help_str

  @property
  def command_name(self) -> str or None:
    return self._options.args[0] if self._options.args else None

  @property
  def command_arguments(self) -> List[str]:
    return self._options.args[1:] if self._options.args else []

  @property
  def kwargs_name(self) -> List[str]:
    return list(self._options.kwargs.keys())

  def _get_command(self, injected_args: dict = None, fail_on_unknown: bool = False) -> CommandModule:
    if not self._options.args:
      raise NoCommandException(None, "No command passed, unable to continue")

    command_name = self._options.args[0]
    command: CommandModule = self._modules[command_name]
    inj_args = set(injected_args.keys()) if injected_args else set()
    command.set_argument(self._options.args[1:], self._options.kwargs, inj_args, fail_on_unknown)

    return command

  def execute_command(self, injected_args: dict = None):
    try:
      command = self._get_command(injected_args)
      command.execute(injected_args)
    except CommandArgumentException as e:
      raise NoCommandException(None, f"Application arguments exception: {str(e)}\n")

  @asyncio.coroutine
  def execute_command_async(self, injected_args: dict = None):
    try:
      command = self._get_command()
      yield from command.execute_async(injected_args)
    except CommandArgumentException as e:
      raise NoCommandException(None, f"Application arguments exception: {str(e)}\n")

  def start_application(self, kwargs: dict = None):
    try:
      command = self._get_command(injected_args=kwargs, fail_on_unknown=True)
      command.execute(injected_args=kwargs)
    except NoCommandException as e:
      if e.command_name:
        sys.stdout.write(self.generate_help(filename=self._options.filename))
      return
    except CommandArgumentException as e:
      sys.stdout.write(f"Application arguments exception: {str(e)}\n")
      return
