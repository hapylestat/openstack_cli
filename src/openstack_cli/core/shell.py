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

import sys
import time
import signal
import paramiko

from socket import socket
from enum import Enum
from threading import Thread
from typing import TextIO
from openstack_cli.modules.apputils.terminal.get_terminal_size import get_terminal_size


def _find_getch():
  try:                 # UNIX like
    import termios
  except ImportError:  # Windows
    import msvcrt
    import ctypes

    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    return msvcrt.getch

  import sys, tty
  def _getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
      tty.setraw(fd)
      ch = sys.stdin.read(1)
    finally:
      termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

  return _getch

_getch = _find_getch()

LL = False
SIGINT = False


def generate_ch_seq(arr):
  return ''.join([chr(x) for x in arr])

# check https://gist.github.com/hapylestat/1101cc1a5bde125cc5d56c6a401a4f35 tool for obtaining key sequences

NCODE_F_KEYS = 0
NCODE_SP_KEYS = 224

class FKEYS(Enum): #NCODE_F_KEYS
  F1 = 59
  F2 = 60
  F3 = 61
  F4 = 62
  F5 = 63
  F6 = 64
  F7 = 65
  F8 = 66
  F9 = 67
  F10 = 68
  F12 = 134

class ARROWS(Enum): #NCODE_SP_KEYS
  UP = 72
  DOWN = 80
  RIGHT = 77
  LEFT = 75

class KEYS(Enum): # NCODE_SP_KEYS
  INSERT = 82
  DELETE = 83
  HOME = 71
  END = 79
  PAGEUP = 73
  PAGEDOWN = 81

class NCODE_KEYS(Enum):
  TAB = 9
  ENTER = 13
  BACKSPACE = 8
  ESC = 27


fkeys = {
  FKEYS.F1.value: generate_ch_seq([27, 79, 80]),  # F1
  FKEYS.F2.value: generate_ch_seq([27, 79, 81]),  # F2
  FKEYS.F3.value: generate_ch_seq([27, 79, 82]),  # F3
  FKEYS.F4.value: generate_ch_seq([27, 79, 83]),  # F4
  FKEYS.F5.value: generate_ch_seq([27, 91, 49, 53, 126]),  # F5
  FKEYS.F6.value: generate_ch_seq([27, 91, 49, 55, 126]),  # F6
  FKEYS.F7.value: generate_ch_seq([27, 91, 49, 56, 126]),  # F7
  FKEYS.F8.value: generate_ch_seq([27, 91, 49, 57, 126]),  # F8
  FKEYS.F9.value: generate_ch_seq([27, 91, 50, 48, 126]),  # F9
  FKEYS.F10.value: generate_ch_seq([27, 91, 50, 49, 126])   # F10
}

# escape seq
arrows = {
  ARROWS.UP.value: "\033[A",  # up
  ARROWS.DOWN.value: "\033[B",  # down
  ARROWS.RIGHT.value: "\033[C",  # right
  ARROWS.LEFT.value: "\033[D"   # left
}

# 224 code subspace
nav_keys = {
  KEYS.INSERT.value: generate_ch_seq([27, 91, 50, 126]),  # insert
  KEYS.DELETE.value: generate_ch_seq([27, 91, 51, 126]),  # delete
  KEYS.HOME.value: generate_ch_seq([27, 91, 72]),       # home
  KEYS.END.value: generate_ch_seq([27, 91, 70]),       # end
  KEYS.PAGEUP.value: generate_ch_seq([27, 91, 53, 126]),  # PageUp
  KEYS.PAGEDOWN.value: generate_ch_seq([27, 91, 54, 126]),  # PageDown
}

"""
Requirements:

export TERM=xterm-noapp
"""


def _special_commands(channel: paramiko.Channel):
  global LL
  global SIGINT
  _k = ord(_getch())
  if _k == NCODE_SP_KEYS and ord(_getch()) == FKEYS.F12.value:
    LL = not LL
    print("\n Character code debugging is: {}".format(LL))
    if LL:
      print("> ", end='', flush=True)
  elif _k == NCODE_F_KEYS and ord(getch()) == FKEYS.F5.value:
    channel.resize_pty(*get_terminal_size())
  elif _k == 99:  # C:
    SIGINT = True
  elif _k == 105: # I
    t: paramiko.Transport = channel.get_transport()
    sock: socket = t.sock
    localname, peername = sock.getsockname(), sock.getpeername()
    local = localname if localname else ("unknown", 0)
    remote = peername if peername else ("unknown", 0)
    print(f"""
Connection: {t.local_version} -> {t.remote_version} ({'active' if t.active == 1 else 'inactive'}, auth: {t.authenticated})
Local endpoint: {local[0]}:{local[1]}, host key type = {t.host_key_type}
Repote Endpoint: {remote[0]}:{remote[1]}, chipher type = {t.remote_cipher}, mac = {t.remote_mac}

Preffered:
   Ciphers: {','.join(t.preferred_ciphers)}
   Keys: {','.join(t.preferred_keys)}
   Macs: {','.join(t.preferred_macs)}
""")
  else:
    return chr(7)

# check pynput code

def getch(cmd: TextIO, channel: paramiko.Channel):
  global SIGINT

  if SIGINT:
    SIGINT = False
    return chr(3)

  ch = _getch()
  n = ord(ch)
  nn = None

  if n in (NCODE_F_KEYS, NCODE_SP_KEYS):  # some sequences return several codes
    nn = ord(_getch())

  if LL and not (n == NCODE_SP_KEYS and nn == FKEYS.F12.value):
    if nn:
      print("{} {} ".format(n, nn), end='', flush=True)
    else:
      print("{} ".format(n), end='', flush=True)

    return
  elif n == NCODE_SP_KEYS:  # next will come arrow keys
    if nn in arrows:
      return arrows[nn]

    if nn in nav_keys:
      return nav_keys[nn]

    if nn == FKEYS.F12.value:  # F12  CUSTOM COMMANDS
      return _special_commands(channel)
  elif n == NCODE_F_KEYS:  # F1-F12
    if nn in fkeys:
       return fkeys[nn]
  elif n == NCODE_KEYS.TAB.value:
    return "\t"
  elif n in (NCODE_KEYS.ENTER.value, NCODE_KEYS.BACKSPACE.value, NCODE_KEYS.ESC.value):
    pass
  # elif n < 32 or n > 177:
  #   print("Unknown char! Char code: {}".format(n))


  return ch


def _sigint(signum, frame):
  global SIGINT
  SIGINT = True


def _sigwinch(*args):
  print("EE:")
  print(args)


def __buffered_reader(stdread: paramiko.ChannelFile, stdwrite: TextIO):
  global SIGINT
  import select
  import time
  channel: paramiko.Channel = stdread.channel
  while not SIGINT and not channel.exit_status_ready():
    time.sleep(0.2)
    if channel.recv_ready():
      r, w, x = select.select([channel], [], [], 0.0)
      if len(r) > 0:
        stdwrite.buffer.write(channel.recv(1024))
        stdwrite.flush()

  SIGINT = True


def __input_handler(stdin: TextIO, rstdin: TextIO, channel: paramiko.Channel):
  global SIGINT
  while not SIGINT:
    buff = getch(stdin, channel)
    if buff:
      if isinstance(buff, str):
        buff = buff.encode("UTF-8")

      rstdin.write(buff)


def __window_size_change_handler(channel: paramiko.Channel):
  width, height = get_terminal_size()
  while not SIGINT:
    time.sleep(1)
    nwidth, nheight = get_terminal_size()
    if nwidth != width or nheight != height:
      width = nwidth
      height = nheight
      channel.resize_pty(width=width, height=height)


def shell(channel: paramiko.Channel):
  stdin: paramiko.ChannelFile = channel.makefile_stdin("wb")
  stdout: paramiko.ChannelFile = channel.makefile("r")
  stderr: paramiko.ChannelFile = channel.makefile_stderr("r")
  print("Tip: F12 + I to show connection info, F12+C to close connection, F12+F5 force PTY size update")

  stdoutReader = Thread(target=__buffered_reader, name="stdoutReader", args=(stdout, sys.stdout))
  stderrReader = Thread(target=__buffered_reader, name="stderrReader", args=(stderr, sys.stderr))
  stdinWriter = Thread(target=__input_handler, name="stdinWriter", args=(sys.stdin, stdin, channel))
  sizeHandler = Thread(target=__window_size_change_handler, name="TerminalSizeWatchdog", args=(channel,))

  sizeHandler.setDaemon(True)
  stdoutReader.setDaemon(True)
  stderrReader.setDaemon(True)
  stdinWriter.setDaemon(True)

  orig_sigint = signal.getsignal(signal.SIGINT)
  try:
    signal.signal(signal.SIGINT, _sigint)

    sizeHandler.start()
    stderrReader.start()
    stdoutReader.start()
    stdinWriter.start()

    stdoutReader.join()
    print("Closing ssh session...")
    channel.close()
  finally:
    signal.signal(signal.SIGINT, orig_sigint)

