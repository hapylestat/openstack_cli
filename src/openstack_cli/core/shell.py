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

from threading import Thread
from typing import TextIO
from openstack_cli.modules.apputils.terminal.get_terminal_size import get_terminal_size
from openstack_cli.modules.apputils.terminal.getch import getch as _getch, FUNC_KEYS, NCODE_KEYS, VTKEYS


F12MENU = False
SIGINT = False

def _f12_commands(channel: paramiko.Channel):
  global F12MENU
  global SIGINT
  _k = _getch()

  if _k == FUNC_KEYS.F12.value:
    F12MENU = not F12MENU
    print(f"\n Character code debugging is: {F12MENU}")
    if F12MENU:
      print("> ", end='', flush=True)
  elif _k == (99,):  # C:
    SIGINT = True
  elif _k == (105,): # I
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


def getch(channel: paramiko.Channel):
  global SIGINT

  if SIGINT:
    SIGINT = False
    return chr(3)

  ch = _getch()

  if F12MENU and ch != FUNC_KEYS.F12.value:
    print(f"{ch} ", end='', flush=True)
    return
  elif ch == FUNC_KEYS.F12.value:
    return _f12_commands(channel)
  elif ch in VTKEYS:
    return VTKEYS[ch]
  elif ch == NCODE_KEYS.TAB.value:
    return "\t"
  elif ch in (NCODE_KEYS.ENTER.value, NCODE_KEYS.BACKSPACE.value, NCODE_KEYS.ESC.value):
    pass

  return "".join([chr(c) for c in ch])


def _sigint(signum, frame):
  global SIGINT
  SIGINT = True


def __buffered_reader(stdread: paramiko.ChannelFile, stdwrite: TextIO):
  global SIGINT
  import select
  import time
  channel: paramiko.Channel = stdread.channel
  while not SIGINT and not channel.exit_status_ready():
    if channel.recv_ready():
      r, w, x = select.select([channel], [], [], 0.0)
      if len(r) > 0:
        stdwrite.buffer.write(channel.recv(1024))
        stdwrite.flush()
    else:
       time.sleep(0.2)

  SIGINT = True


def __input_handler(stdin: TextIO, rstdin: TextIO, channel: paramiko.Channel):
  global SIGINT
  while not SIGINT:
    buff = getch(channel)
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
      width, height = nwidth, nheight
      channel.resize_pty(width=width, height=height)


def shell(channel: paramiko.Channel):
  stdin: paramiko.ChannelFile = channel.makefile_stdin("wb")
  stdout: paramiko.ChannelFile = channel.makefile("r")
  stderr: paramiko.ChannelFile = channel.makefile_stderr("r")
  print("Tip: F12 + I to show connection info, F12+C to close connection")

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
  finally:
    print("Closing ssh session...")
    try:
      channel.close()
    except:
      pass
    signal.signal(signal.SIGINT, orig_sigint)

