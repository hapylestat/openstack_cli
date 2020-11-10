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


from concurrent.futures._base import Future, CancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from getpass import getpass
from io import StringIO
from typing import Callable, List, Dict, TypeVar
import sys
from enum import Enum

from openstack_cli.core.colors import Colors, Symbols
from openstack_cli.modules.openstack import OpenStackVMInfo, JSONValueError
from openstack_cli.modules.openstack.api_objects import ApiErrorResponse
from openstack_cli.modules.progressbar import ProgressBar, ProgressBarOptions, CharacterStyles, get_terminal_size


T = TypeVar('T')


class TableStyle(Enum):
  default = 0
  line_highlight = 1


class TableColumnPosition(Enum):
  left = "<"
  right = ">"
  center = "^"


class TableColumn(object):
  def __init__(self, name: str = "", length: int = 1, pos: TableColumnPosition = TableColumnPosition.left,
               inv_ch: int = 0, sep: str = ""):
    """
    :param name: Column name
    :param length:  column width
    :param pos: Cell position align
    :param inv_ch: number of invisible characters
    :param sep: delimiter between columns
    """
    self.name: str = name
    self.length: int = max(length, len(name))
    self.inv_ch: int = inv_ch   # invisible_characters, such as color escape codes
    self.pos: str = pos.value
    self.sep: str = f" {sep}" if name else ""


class TableSizeColumn(object):
  def __init__(self, value: int):
    self.__value = value

  @property
  def value(self):
    return str(self)

  def __str__(self):
    if self.__value is None:
      return "0 b"

    if self.__value < 1000:
      return f"{self.__value} b"

    val = self.__value / 1000.0
    if val < 1000:
      return f"{val:0.2f} kb"

    val = val / 1000.0
    if val < 1000:
      return f"{val:0.2f} mb"

    val = val / 1000.0
    if val < 1000:
      return f"{val:0.2f} gb"

    val = val / 1000.0
    return f"{val:0.2f} tb"


class TableOutput(object):
  def __init__(self, *columns: TableColumn, style: TableStyle = TableStyle.default, print_row_number: bool = False):
    self.__print_row_number = print_row_number
    columns = [TableColumn(length=3)] + list(columns) if print_row_number else columns

    self.__columns = columns
    self.__column_pattern = "  ".join([f"{{:{c.pos}{c.length}}}{c.sep}" for c in columns])
    self.__column_inv_pattern = "  ".join([f"{{:{c.pos}{c.length + c.inv_ch}}}{c.sep}" for c in columns])
    self.__sep_columns = [("-" if c.name else " ") * c.length for c in columns]
    self.__style = style
    self.__prev_color = Colors.BRIGHT_BLACK
    self.__current_row = 0

  def print_header(self, solid: bool = False):
    print(self.__column_pattern.format(*[c.name for c in self.__columns]))
    if solid:
      print("-" * sum([c.length + len(c.sep) for c in self.__columns]))
    else:
      print(self.__column_pattern.format(*self.__sep_columns))

  def print_row(self, *values: str):
    if self.__print_row_number:
      values = [str(self.__current_row)] + list(values)

    if self.__style == TableStyle.line_highlight:
      print(f"{self.__prev_color}{self.__column_inv_pattern.format(*values)}{Colors.RESET}")
    else:
      print(self.__column_inv_pattern.format(*values))

    if values[-1:][0]:
      self.__prev_color = Colors.BRIGHT_WHITE if self.__prev_color == Colors.BRIGHT_BLACK else Colors.BRIGHT_BLACK

    if self.__print_row_number:
      self.__current_row += 1


class StatusOutput(object):
  def __init__(self, f: Callable[[], bool] or None = None, pool_size: int = 5):
    self.__callable: Callable[[None], bool] = f
    self.__pool_size = pool_size
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

  def check_issues(self, last_errors: List[str] = None):
    if not last_errors and not self.__out and not self.__errors:
      return

    self.__ci:int = 0
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
    if self.__out:
      _print("-----[STDOUT]")
      for line in self.__out:
        _print(line)

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

      finally:
        sys.stdin, sys.stderr, sys.stdout = stdin, stderr, stdout

        p.stop()
        self.__out = [line.strip() for line in mystdout.getvalue().split("\n") if line.strip()]
        self.__errors = [line.strip() for line in mystderr.getvalue().split("\n") if line.strip()]


class Console(object):

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
      print(
        f"{Colors.BRIGHT_YELLOW}{cl_name:{max_cluster_name}}{Colors.RESET} {{{Symbols.PC.yellow()}{len(servers)}; @{servers[0].domain}}}"
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
  def print(cls, *args: str):
    print(*args)

  @classmethod
  def confirm_operation(cls, op: str, servers: Dict[str, List[OpenStackVMInfo]]) -> bool:
    summary_servers: int = sum([len(v) for v in servers.values()])
    if summary_servers == 0:
      print("No items to process")
      return False
    cls.print_list(servers)
    return cls.ask_confirmation(f"Confirm {op} operation for {summary_servers} hosts")
