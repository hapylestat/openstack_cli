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
import asyncio
from collections import OrderedDict
from types import FunctionType

from openstack_cli.modules.discovery import CommandLineOptions


class CommandArgumentException(Exception):
  pass


class NoCommandException(Exception):
  def __init__(self, command_name: str or None, message: str):
    super(NoCommandException, self).__init__(message)
    self.__command_name = command_name

  @property
  def command_name(self):
    return self.__command_name


class CommandArgumentItem(object):
  name = None
  value_type = None
  item_help = None
  default = None

  def __init__(self, name: str, value_type: type, item_help: str, default: object = None):
    self.name = name
    self.value_type = value_type
    self.item_help = item_help
    self.default = default


class CommandArgumentsBuilder:
  def __init__(self):
    self._args = {}
    self._default_args = []
    self.__allowed_default_types = [int, str, float, list]
    self.__allowed_types = self.__allowed_default_types + [bool]
    self.__is_default_arg_flag_used = False

  def add_argument(self, name: str, value_type: type, item_help: str, default: object = None):
    """
    :rtype CommandArgumentsBuilder
    """
    if value_type and value_type not in self.__allowed_types:
      raise CommandArgumentException(f"Named argument couldn't have {value_type.__name__} type")

    if default is not None and not isinstance(default, value_type):
      raise CommandArgumentException(f"Invalid default type for argument ({name})")

    if value_type is bool and default is None:
      default = False

    self._args.update({
      name: CommandArgumentItem(name, value_type, item_help, default)
    })
    return self

  @property
  def arguments(self) -> dict:
    return self._args

  @property
  def default_arguments(self) -> dict:
    d = OrderedDict()

    for arg in self._default_args:
      d.update({arg.name: arg})

    return d

  def add_default_argument(self, name: str, value_type: type, item_help: str, default: object = None):
    """
    :rtype CommandArgumentsBuilder
    """
    if value_type not in self.__allowed_default_types:
      raise CommandArgumentException(f"Positional(default) argument could not have {value_type.__name__} type")

    if self.__is_default_arg_flag_used and default is None:
      raise CommandArgumentException(
        f"After defining first default Positional argument, rest should have default value too ({value_type.__name__})")
    elif default is not None:
      self.__is_default_arg_flag_used = True

      if not isinstance(default, value_type):
        raise CommandArgumentException("Invalid default type for argument".format(name))

    self._default_args.append(CommandArgumentItem(name, value_type, item_help, default=default))
    return self

  @property
  def has_optional_default_argument(self) -> bool:
    return self.__is_default_arg_flag_used

  def get_default_argument(self, index: int) -> CommandArgumentItem:
    return self._default_args[index]


class CommandMetaInfo(object):
  def __init__(self, name: str, item_help: str = "", **kwargs: dict):
    self._name = name
    self._arguments = CommandArgumentsBuilder()
    self._help = item_help
    self._kwargs = kwargs

  @property
  def options(self) -> dict:
    return self._kwargs

  @property
  def name(self) -> str:
    return self._name

  @property
  def help(self) -> str:
    return self._help

  def get_arguments_builder(self) -> CommandArgumentsBuilder:
    return self._arguments

  def __convert_value_to_type(self, value: str, _type: type):
    if _type is list and isinstance(value, str):
      return value.split(",")
    elif _type is bool and len(value) == 0:
      return True
    else:
      return _type(value)

  def transform_default_arguments(self, argv: list, fail_on_unknown: bool = False) -> dict:
    parsed_arguments_dict = {}
    default_arguments = list(self._arguments.default_arguments.values())
    expected_length = len(default_arguments)
    real_length = len(argv)

    default_args_count = len([item for item in default_arguments if item.default])

    if real_length == 0 and expected_length == 0:
      return parsed_arguments_dict
    elif not self._arguments.has_optional_default_argument \
      and (not argv or expected_length != real_length) \
      or (fail_on_unknown and real_length > expected_length):

      raise CommandArgumentException(f"Command require {expected_length} positional argument(s), found {real_length}")
    elif self._arguments.has_optional_default_argument and argv \
      and real_length < expected_length - default_args_count \
      or (fail_on_unknown and real_length > expected_length):

      raise CommandArgumentException(
        f"Command require {expected_length} or {expected_length - default_args_count} positional argument(s), found {real_length}")

    for index in range(0, expected_length):
      arg_meta: CommandArgumentItem = default_arguments[index]
      try:
        arg = argv[index]
      except IndexError:
        arg = arg_meta.default

      try:
        if arg_meta.value_type:
          arg = self.__convert_value_to_type(arg, arg_meta.value_type)

        parsed_arguments_dict[arg_meta.name] = arg
      except (TypeError, ValueError):
        raise CommandArgumentException(
          f"Invalid argument type - expected {arg_meta.value_type.__name__}, got {type(arg).__name__}")

    return parsed_arguments_dict

  def transform_arguments(self, kwargs: dict, fail_on_unknown: bool = False):
    parsed_arguments_dict = {}
    arguments = self._arguments.arguments

    if fail_on_unknown:
      unknown_commands = set(kwargs.keys()) - set(arguments.keys())
      if unknown_commands:
        raise CommandArgumentException(f"Command contains unknown arguments  \"{', '.join(unknown_commands)}\"")

    for arg_name in arguments:
      arg_meta: CommandArgumentItem = arguments[arg_name]
      try:
        if arg_meta.value_type:
          arg = self.__convert_value_to_type(kwargs[arg_name], arg_meta.value_type)
        else:
          arg = kwargs[arg_name]
      except KeyError:
        if arg_meta.default is None:
          raise CommandArgumentException(f"Command require \"{arg_name}\" argument to be set")

        arg = arg_meta.default

      parsed_arguments_dict[arg_name] = arg
    return parsed_arguments_dict


class CommandModule(object):
  def __init__(self, meta_info: CommandMetaInfo, classpath: str, entry_point: FunctionType):
    self.__name = meta_info.name
    self.__classpath = classpath
    self.__meta_info = meta_info
    self.__entry_point: FunctionType = entry_point
    self.__args = None

  def set_argument(self, args: list, kwargs: dict, injected_args: set = None, fail_on_unknown=False):
    if not injected_args:
      injected_args = set()

    args = self.__meta_info.transform_default_arguments(args, fail_on_unknown=fail_on_unknown)
    args.update(self.__meta_info.transform_arguments(kwargs, fail_on_unknown=fail_on_unknown))

    f_args = self.entry_point_args

    if len(f_args) - len(set(f_args) & injected_args) != len(set(args.keys()) & set(f_args)):
      raise CommandArgumentException("Function \"{}\" from module {} doesn't implement all arguments in the signature".format(
        self.__entry_point.__name__, self.__classpath
      ))

    self.__args = args

  @property
  def name(self) -> str:
    return self.__name

  @property
  def classpath(self) -> str:
    return self.__classpath

  @property
  def meta_info(self) -> CommandMetaInfo:
    return self.__meta_info

  @property
  def entry_point_args(self) -> tuple:
    return self.__entry_point.__code__.co_varnames[:self.__entry_point.__code__.co_argcount]

  def filter_injected_arguments(self, injected_arguments: dict = None) -> dict or None:
    if not injected_arguments:
      return None

    args = set(self.entry_point_args) & set(injected_arguments.keys())

    return {k: v for k, v in injected_arguments.items() if k in args}

  def __get_args(self, args: dict, injected_args: dict = None) -> dict:
    injected_args = self.filter_injected_arguments(injected_args)
    all_args = dict()
    if injected_args:
      all_args.update(injected_args)
    all_args.update(args)

    return all_args

  def execute(self,  injected_args: dict = None):
    self.__entry_point(**self.__get_args(self.__args, injected_args))

  @asyncio.coroutine
  def execute_async(self, injected_args: dict = None):
    yield from self.__entry_point(**self.__get_args(self.__args, injected_args))


class CommandModules(object):
  def __init__(self, entry_point: str):
    self.__modules = {}
    self.__entry_point = entry_point
    self.__required_module_fields = {"__module__", entry_point}
    self.__req_module_fields_count = len(self.__required_module_fields)

  def __getitem__(self, item: str) -> CommandModule:
    try:
      return self.__modules[item]
    except KeyError:
      raise NoCommandException(item, f"No such command '{item}' found, unable to continue")

  def __len__(self):
    return len(self.__modules)

  def __contains__(self, item: str):
    return item in self.__modules

  def __iter__(self):
    return self.__modules.items()

  @property
  def commands(self):
    return self.__modules.keys()

  def add(self, classpath: str, command_filename: str):
    m = __import__(f"{classpath}.{command_filename}", fromlist=classpath)
    m_dict = m.__dict__
    meta_info = m_dict["__module__"]
    if not isinstance(meta_info, CommandMetaInfo):
      return

    if self.__req_module_fields_count == len(self.__required_module_fields & set(m_dict.keys())):
      self.__modules[meta_info.name] = CommandModule(
        classpath=m.__name__,
        meta_info=meta_info,
        entry_point=m_dict[self.__entry_point]
      )
