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

from enum import Enum

UNIX_ESCAPE_KEYS = 27


class FUNC_KEYS(Enum):  # NCODE_F_KEYS
  F1 = (UNIX_ESCAPE_KEYS, 79, 80)
  F2 = (UNIX_ESCAPE_KEYS, 79, 81)
  F3 = (UNIX_ESCAPE_KEYS, 79, 82)
  F4 = (UNIX_ESCAPE_KEYS, 79, 83)
  F5 = (UNIX_ESCAPE_KEYS, 91, 49, 53, 126)
  F6 = (UNIX_ESCAPE_KEYS, 91, 49, 55, 126)
  F7 = (UNIX_ESCAPE_KEYS, 91, 49, 56, 126)
  F8 = (UNIX_ESCAPE_KEYS, 91, 49, 57, 126)
  F9 = (UNIX_ESCAPE_KEYS, 91, 50, 48, 126)
  F10 = (UNIX_ESCAPE_KEYS, 91, 50, 49, 126)
  F11 = (UNIX_ESCAPE_KEYS, 91, 50, 51, 126)
  F12 = (UNIX_ESCAPE_KEYS, 91, 50, 52, 126)


class ARROW_KEYS(Enum):  # NCODE_SP_KEYS
  UP = (UNIX_ESCAPE_KEYS, 91, 65)
  DOWN = (UNIX_ESCAPE_KEYS, 91, 66)
  RIGHT = (UNIX_ESCAPE_KEYS, 91, 67)
  LEFT = (UNIX_ESCAPE_KEYS, 91, 68)


class NAV_KEYS(Enum):  # NCODE_SP_KEYS
  INSERT = (UNIX_ESCAPE_KEYS, 91, 50, 126)
  DELETE = (UNIX_ESCAPE_KEYS, 91, 51, 126)
  HOME = (UNIX_ESCAPE_KEYS, 91, 49, 126)
  END = (UNIX_ESCAPE_KEYS, 91, 52, 126)
  PAGEUP = (UNIX_ESCAPE_KEYS, 91, 53, 126)
  PAGEDOWN = (UNIX_ESCAPE_KEYS, 91, 54, 126)


class NCODE_KEYS(Enum):
  TAB = (9,)
  ENTER = (10,)
  BACKSPACE = (127,)
  ESC = (UNIX_ESCAPE_KEYS,)
