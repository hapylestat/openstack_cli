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

from typing import Tuple, Callable

"""
Linux terminal recommendation for VT combinations to send

export TERM=xterm-noapp
"""

import sys, os
from select import select

try:
  import termios
  __IS_UNIX = True

  def __getch() -> Tuple[int]:
    buff = []

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    new_settings = termios.tcgetattr(fd)
    new_settings[0] = new_settings[0] & ~(termios.BRKINT | termios.IGNBRK)
    new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
    new_settings[6][termios.VMIN] = 0
    new_settings[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
    try:
      while not buff:
        r, _, _ = select([sys.stdin], [], [])
        if not r:
          continue
        ch = os.read(fd, 1)
        while ch is not None and ch:
          buff.append(int.from_bytes(ch, "big"))
          ch = os.read(fd, 1)
        if buff:
          return tuple(buff)
    except KeyboardInterrupt:
      return 3,
    finally:
      termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

except (ImportError, ModuleNotFoundError):
  __IS_UNIX = False

  import ctypes
  import msvcrt

  kernel32 = ctypes.windll.kernel32
  kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

  from .keymapping_win import KB_BASIC_CODE, KB_EXT_CODE

  def __getch() -> Tuple[int]:
    buff = [ord(msvcrt.getwch())]
    if buff[0] in (KB_BASIC_CODE, KB_EXT_CODE):
      buff.append(ord(msvcrt.getwch()))
    return tuple(buff)


getch: Callable[[], Tuple[int]] = __getch


def __generate_ch_seq(arr):
  return ''.join([chr(x) for x in arr])


from .keymapping_unix import ARROW_KEYS as __UNIX_ARROX_KEYS, NAV_KEYS as __UNIX_NAV_KEYS, FUNC_KEYS as __UNIX_FUNC_KEYS
if __IS_UNIX:
  from .keymapping_unix import ARROW_KEYS, NAV_KEYS, FUNC_KEYS, NCODE_KEYS
else:
  from .keymapping_win import ARROW_KEYS, NAV_KEYS, FUNC_KEYS, NCODE_KEYS

#  win/unix -> unix
VTKEYS = {
  # ARROWS
  ARROW_KEYS.UP.value:    __generate_ch_seq(__UNIX_ARROX_KEYS.UP.value),       # up
  ARROW_KEYS.DOWN.value:  __generate_ch_seq(__UNIX_ARROX_KEYS.DOWN.value),     # down
  ARROW_KEYS.RIGHT.value: __generate_ch_seq(__UNIX_ARROX_KEYS.RIGHT.value),    # right
  ARROW_KEYS.LEFT.value:  __generate_ch_seq(__UNIX_ARROX_KEYS.LEFT.value),     # left
  # NAV-KEYS
  NAV_KEYS.INSERT.value: __generate_ch_seq(__UNIX_NAV_KEYS.INSERT.value),      # insert
  NAV_KEYS.DELETE.value: __generate_ch_seq(__UNIX_NAV_KEYS.DELETE.value),      # delete
  NAV_KEYS.HOME.value: __generate_ch_seq(__UNIX_NAV_KEYS.HOME.value),          # home
  NAV_KEYS.END.value: __generate_ch_seq(__UNIX_NAV_KEYS.END.value),            # end
  NAV_KEYS.PAGEUP.value: __generate_ch_seq(__UNIX_NAV_KEYS.PAGEUP.value),      # PageUp
  NAV_KEYS.PAGEDOWN.value: __generate_ch_seq(__UNIX_NAV_KEYS.PAGEDOWN.value),  # PageDown

  # F-KEYS
  FUNC_KEYS.F1.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F1.value),            # F1
  FUNC_KEYS.F2.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F2.value),            # F2
  FUNC_KEYS.F3.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F3.value),            # F3
  FUNC_KEYS.F4.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F4.value),            # F4
  FUNC_KEYS.F5.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F5.value),            # F5
  FUNC_KEYS.F6.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F6.value),            # F6
  FUNC_KEYS.F7.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F7.value),            # F7
  FUNC_KEYS.F8.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F8.value),            # F8
  FUNC_KEYS.F9.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F9.value),            # F9
  FUNC_KEYS.F10.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F10.value),          # F10
  FUNC_KEYS.F11.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F11.value),          # F11
  FUNC_KEYS.F12.value: __generate_ch_seq(__UNIX_FUNC_KEYS.F12.value)           # F12
}


def _main():
  """
  Test codes, to use:
   - change directory to terminal package
   - execute python
   - python >>> import getch
   - python >>> getch._main()
  """
  print("Key VT/Scan codes testing tool, hit ESC to exit:")
  while True:
    ch = getch()
    print(f"{ch} ", end='', flush=True)

    if ch == NCODE_KEYS.ESC.value:
      print("Exiting...")
      break
