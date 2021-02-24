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

KB_BASIC_CODE = 0
KB_EXT_CODE = 224


class FUNC_KEYS(Enum):  # NCODE_F_KEYS
  F1 = (KB_BASIC_CODE, 59)
  F2 = (KB_BASIC_CODE, 60)
  F3 = (KB_BASIC_CODE, 61)
  F4 = (KB_BASIC_CODE, 62)
  F5 = (KB_BASIC_CODE, 63)
  F6 = (KB_BASIC_CODE, 64)
  F7 = (KB_BASIC_CODE, 65)
  F8 = (KB_BASIC_CODE, 66)
  F9 = (KB_BASIC_CODE, 67)
  F10 = (KB_BASIC_CODE, 68)
  F11 = (KB_EXT_CODE, 133)
  F12 = (KB_EXT_CODE, 134)


class ARROW_KEYS(Enum):  # NCODE_SP_KEYS
  UP = (KB_EXT_CODE, 72)
  DOWN = (KB_EXT_CODE, 80)
  RIGHT = (KB_EXT_CODE, 77)
  LEFT = (KB_EXT_CODE, 75)


class NAV_KEYS(Enum):  # NCODE_SP_KEYS
  INSERT = (KB_EXT_CODE, 82)
  DELETE = (KB_EXT_CODE, 83)
  HOME = (KB_EXT_CODE, 71)
  END = (KB_EXT_CODE, 79)
  PAGEUP = (KB_EXT_CODE, 73)
  PAGEDOWN = (KB_EXT_CODE, 81)


class NCODE_KEYS(Enum):
  TAB = (9,)
  ENTER = (13,)
  BACKSPACE = (8,)
  ESC = (27,)
