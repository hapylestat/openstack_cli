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
import sys

from io import StringIO
from concurrent.futures._base import Future, CancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import ContextDecorator
from getpass import getpass
from typing import Callable, List, Dict, TypeVar

from openstack_cli.modules.apputils.terminal.colors import Colors, Symbols
from openstack_cli.modules.openstack import OpenStackVMInfo, JSONValueError
from openstack_cli.modules.openstack.api_objects import ApiErrorResponse
from openstack_cli.modules.apputils.progressbar import ProgressBar, ProgressBarOptions, CharacterStyles, get_terminal_size


T = TypeVar('T')


class StatusOutput(object):
  def __init__(self, f: Callable[[], bool] or None = None, pool_size: int = 5, additional_errors: Callable = None):
    """
    :param f: function to execute
    :param pool_size: size of pool wor executing f
    :param additional_errors: ref to function with no args and return type List[str]
    """
    self.__callable: Callable[[None], bool] = f
    self.__pool_size = pool_size
    self.__additional_errors: Callable = additional_errors
    self.__errors = []
    self.__out = []

  def __get_dino(self) -> List[str]:
    return [
      "|                   ____      ",
      "|                .-~    '.    ",
      "|               / /  ~@\   )  ",
      "|              | /  \~\.  `\  ",
      "|             /  |  |< ~\(..) ",
      "|       _.--~T   \  \<   .,,  ",
      "|___.--~ .    _  /~\ \< /     ",
      "|       /|   /o\ /-~\ \_|     ",
      "|      |o|  / /|o/_   '--'    ",
      "|__   _j \_/ / /\|~    .      ",
      "|   ~~~|    `/ / / \.__/l_    ",
      "|_     l      /_/~-.___.--~   "
    ]

  def split_string(self, s: str, chunk_size: int):
    return (s[i:chunk_size+i] for i in range(0, len(s), chunk_size))

  def check_issues(self):
    last_errors: List[str] = self.__additional_errors() if self.__additional_errors else None
    if not last_errors and not self.__out and not self.__errors:
      return

    self.__ci: int = 0
    max_width: int = get_terminal_size(fallback=(140, 80))[0]
    dino: List[str] = self.__get_dino()
    spacing: int = len(dino[0])

    def _print(_line_list: str or List[str]):
      if isinstance(_line_list, str):
        _line_list = [_line_list]

      for _line in _line_list:
        lines_to_print = self.split_string(_line, max_width-spacing)
        for l in lines_to_print:
          l = l.strip("\n").strip("\r")
          _fill: str = dino[self.__ci] if self.__ci < len(dino) else " " * spacing
          print(f"{_fill}{l}")
          self.__ci += 1

    print("")
    print("///////// Raaawr, something went wrong")
    if self.__errors:
      _print("-----[STDERR]")
      for line in self.__errors:
        _print(line)

    if last_errors:
      _print("-----[   API]")
      for line in last_errors:
        if JSONValueError.KEY not in line:
          _print(line.split("\n"))
          continue

        try:
          _print("")
          error_response = ApiErrorResponse(serialized_obj=line.split(JSONValueError.KEY)[1])
          _print(f"Error code: {error_response.code}")
          _print(f"Message: {error_response.message}")
          _print("")
        except Exception:
          _print(line)

    if self.__ci < len(dino):
      for i in range(self.__ci, len(dino)-1):
        print(dino[i])
    print("///////// END")

  def start(self, title: str, objects: List[object]):
    """
    :return tuple of intercepted stdout and stdin
    """
    total_tasks: int = len(objects)
    failed_tasks: int = 0
    ok_tasks: int = 0
    status_pattern: str = f"{{:3d}} {Symbols.CHECK.green()} | {{:3d}} {Symbols.CROSS.red()}"

    with ThreadPoolExecutor(max_workers=self.__pool_size) as e:
      futures: List[Future] = [e.submit(self.__callable, obj) for obj in objects]
      stdin, stderr, stdout = sys.stdin, sys.stderr, sys.stdout
      sys.stdin, sys.stderr, sys.stdout = mystdin, mystderr, mystdout = StringIO(), StringIO(), StringIO()
      i: int = 0
      done_indexes: List[int] = []
      p_options: ProgressBarOptions = ProgressBarOptions(
        progress_format="{begin_line}{text}:  [{percents_done:>3}% {filled}{empty} {elapsed}] {status}  | {value}/{max} {end_line}",
        character_style=CharacterStyles.squared
      )
      p: ProgressBar = ProgressBar(title, width=15, options=p_options, stdout=stdout)
      p.start(total_tasks)

      try:
        while len(done_indexes) < len(futures):
          if i >= len(futures):
            i = 0

          if i in done_indexes:
            i += 1
            continue

          if futures[i].done():
            try:
              if futures[i].result(timeout=0.0) is True:
                ok_tasks += 1
              else:
                failed_tasks += 1
              done_indexes.append(i)
            except TimeoutError:
              pass
            except (CancelledError, Exception) as e:
              print(f"Error: {str(e)}", file=mystderr)
              done_indexes.append(i)
              failed_tasks += 1
          i += 1

          p.progress(ok_tasks+failed_tasks, status_pattern.format(ok_tasks, failed_tasks))
      except Exception as e:
        self.__errors += str(e).split(os.linesep)
      finally:
        sys.stdin, sys.stderr, sys.stdout = stdin, stderr, stdout
        p.stop()

        mystdout.seek(0, 0)
        for line in mystdout.readlines():
          print(line, end='')

        self.__errors = [line.strip() for line in mystderr.getvalue().split("\n") if line.strip()]
        self.check_issues()


class Console(object):
  class status_context(ContextDecorator):
    def __init__(self, action_text: str):
      super(Console.status_context, self).__init__()

      self.__stdout_wrap, self.__stderr_wrap, self.__stdin_wrap = StringIO(), StringIO(), StringIO()
      self.__stdout, self.__stderr, self.__stdin = sys.stdout, sys.stderr, sys.stdin
      sys.stdout, sys.stderr, sys.stdin,  = self.__stdout_wrap, self.__stderr_wrap, self.__stdin_wrap

      self.__action_txt = action_text

    def __enter__(self):
      print(f"{self.__action_txt}...", flush=True, end='', file=self.__stdout)

    def __exit__(self, exc_type, exc_val, exc_tb):
      sys.stdout, sys.stderr, sys.stdin = self.__stdout, self.__stderr, self.__stdin
      print(Colors.RED.wrap("fail") if exc_type else Colors.GREEN.wrap("ok"), flush=True)

      self.__stdout_wrap.seek(0, 0)
      for line in self.__stdout_wrap.readlines():
        print(line, end='')

      return exc_val is None

  @classmethod
  def ask_pass(cls, *args: str) -> str:
    return getpass(" ".join(args))

  @classmethod
  def ask_confirmation(cls, t: str, force: bool = False) -> bool:
    if force:
      return True
    r: str = input(f"{t} (Y/N): ")
    return r.lower() == "y"

  @classmethod
  def ask(cls, text: str, _type: T = str) -> T or None:
    r: str = input(f"{text}: ")
    try:
      return _type(r)
    except (TypeError, ValueError):
      cls.print_error(f"Expecting type '{_type.__name__}', got value '{r}'")
      return None

  @classmethod
  def print_list(cls, servers: Dict[str, List[OpenStackVMInfo]]):
    max_cluster_name: int = max((len(i) for i in servers.keys())) if len(servers) > 0 else 0

    for cl_name, servers in servers.items():
      if servers:
        max_host_name = max_cluster_name + len(servers[0].domain) + len(str(len(servers)))
      else:
        max_host_name: int = 0

      if len(servers) > 10:
        print(
          f"{Colors.BRIGHT_YELLOW}{cl_name:{max_cluster_name}}{Colors.RESET}: {len(servers)} host(s)"
        )
      else:
        for server in servers:
          print(
            f"{Colors.BRIGHT_YELLOW}{server.fqdn:{max_host_name}}{Colors.RESET}"
          )
    print()

  @classmethod
  def print_warning(cls, *text: str):
    print(f"{Colors.BRIGHT_CYAN}///{Colors.YELLOW}Warning{Colors.RESET} -> ", *text)
    print()

  @classmethod
  def print_error(cls, *text: str):
    print(f"{Colors.BRIGHT_CYAN}///{Colors.BRIGHT_RED}Error{Colors.RESET} -> ", *text)

  @classmethod
  def print_debug(cls, *text: str):
    print(f"{Colors.BRIGHT_BLUE}[DEBUG]{Colors.RESET}: {Colors.YELLOW}", *text, Colors.RESET)

  @classmethod
  def print(cls, *args: str, flush: bool = False):
    print(*args, flush=flush)

  @classmethod
  def confirm_operation(cls, op: str, servers: Dict[str, List[OpenStackVMInfo]]) -> bool:
    summary_servers: int = sum([len(v) for v in servers.values()])
    if summary_servers == 0:
      print("No items to process")
      return False
    cls.print_list(servers)
    return cls.ask_confirmation(f"Confirm {op} operation for {summary_servers} host(s)")
