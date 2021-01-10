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
#
#  Github: https://github.com/hapylestat/apputils
#
#


import sys

from io import StringIO
from enum import Enum
from contextlib import ContextDecorator
from getpass import getpass
from typing import TypeVar

from .colors import Colors

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
    self.__line = "-"
    self.__space = " "
    self.__print_row_number = print_row_number
    columns = [TableColumn(length=3)] + list(columns) if print_row_number else columns

    self.__columns = columns

    self.__column_pattern = []
    self.__column_inv_pattern = []
    self.__sep_columns = []
    self.__sep_solid_columns = []
    self.__column_titles = []
    self.__table_width: int = 0

    for c in columns:
      self.__column_pattern.append(f"{{:{c.pos}{c.length}}}{c.sep}")
      self.__column_inv_pattern.append(f"{{:{c.pos}{c.length + c.inv_ch}}}{c.sep}")
      self.__sep_columns.append((self.__line if c.name else self.__space) * c.length)
      self.__sep_solid_columns.append(self.__line * (c.length + len(c.sep)))
      self.__column_titles.append(c.name)

      self.__table_width += c.length + len(c.sep)

    self.__column_pattern = "  ".join(self.__column_pattern)
    self.__column_inv_pattern = "  ".join(self.__column_inv_pattern)

    self.__column_solid_pattern = "--".join(["{}"] * len(columns))
    self.__style = style
    self.__prev_color = Colors.BRIGHT_BLACK
    self.__current_row = 0

  def print_header(self, solid: bool = False, custom_header: str = ""):
    _line = self.__column_solid_pattern.format(*self.__sep_solid_columns) if solid or custom_header \
      else self.__column_pattern.format(*self.__sep_columns)

    if custom_header:
      print()
      """
       custom_header
            |   -- _table_width - P - len(custom_header)
            ∨  ∨
      .....LOL....
      ^   ^      ^
      S   P       _table_width
      """
      p = round(self.__table_width / 2 - len(custom_header) / 2) - 1
      # ToDo: style with borders?
      print(f" {self.__space * p}{custom_header}{self.__space * (self.__table_width - p - len(custom_header))}")
    else:
      print(self.__column_pattern.format(*self.__column_titles))

    print(_line)

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
