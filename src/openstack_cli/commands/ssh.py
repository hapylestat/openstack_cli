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

import os
import sys
import subprocess

from openstack_cli.core.shell import shell
from openstack_cli.modules.apputils.terminal.get_terminal_size import get_terminal_size
from openstack_cli.modules.apputils.terminal import Console
from openstack_cli.modules.openstack import OpenStack
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo

__module__ = CommandMetaInfo("ssh", "Establish an SSH connection to a cluster node")
__args__ = __module__.arg_builder\
  .add_default_argument("name", str, "full node name or cluster name")\
  .add_default_argument("node_number", int, "node number of the cluster to connect to", default=-1)\
  .add_argument("user_name", str, "User name to login", alias="user-name", default="root")\
  .add_argument("use_password", bool, "Use password auth instead of key",  alias="use-password", default=False)\
  .add_argument("use_key", str, "Private key to use instead of one detected automatically", alias="use-key", default="None")\
  .add_argument("own", bool, "Display only own clusters", default=False)\
  .add_argument("port", int, "SSH Port", default=22)\
  .add_argument("internal", bool, "Use internal SSH Client", alias="buildin", default=False)

from openstack_cli.modules.utils import host_selector

IS_WIN: bool = sys.platform == "win32"


def _locate_binary(name: str) -> str:
  _default: str = "c:\\windows\\system32\\openssh" if IS_WIN else "/usr/bin/ssh"
  name = f"{name}.exe" if IS_WIN else name
  path_list = os.getenv("PATH").split(os.path.pathsep)
  for path in path_list:
    if name in os.listdir(path):
      return os.path.join(path, name)

  return os.path.join(_default, name)


def _internal(host: str, port: int = 22, user_name: str = "root", password: bool = False, key_file: str = None):
  import paramiko

  s = paramiko.SSHConfig()

  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  args = {
    "hostname": host,
    "port": port,
    "username": user_name,
    "look_for_keys": False,
    "allow_agent": False
  }
  if password:
    pasw = Console.ask_pass("SSH Password: ")
    args["password"] = pasw
  else:
    k = paramiko.RSAKey.from_private_key_file(key_file)
    args["pkey"] = k

  ssh.connect(**args)

  width, height = get_terminal_size()
  term = "xterm-noapp"
  shell(ssh.invoke_shell(
    term=term,
    width=width,
    height=height,
    environment={
      "TERM": term
    }
  ))


def _external(host: str, port: int = 22, user_name: str = "root", password: bool = False, key_file: str = None):
  args = [
    f"{user_name}@{host}",
    "-p",
    str(port),
    "-oStrictHostKeyChecking=no",
    f"-oUserKnownHostsFile={'NUL' if IS_WIN else '/dev/null'}"
  ]

  if key_file:
    args.extend([
      "-oPreferredAuthentications=publickey",
      "-oPasswordAuthentication=no",
      "-oIdentitiesOnly=yes",
      "-i",
      key_file
    ])
  elif password:
    args.extend([
      "-oPreferredAuthentications=password",
      "-oPasswordAuthentication=yes"
    ])

  _bin = _locate_binary("ssh")
  if IS_WIN:
    args = [_bin] + args
    p = subprocess.Popen(args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    p.wait()
  else:
    os.execv(_bin, [_bin] + args)

def _open_console(internal:bool, host: str, port: int = 22, user_name: str = "root", password: bool = False,
                  key_file: str = None):

  if internal:
    _internal(host, port, user_name, password, key_file)
  else:
    _external(host, port, user_name, password, key_file)


def __init__(conf: Configuration, name: str, node_number: int, user_name: str, use_password: bool, use_key: str,
             own: bool, port: int, internal: bool):

  if use_key == "None":
    use_key = None

  ostack = OpenStack(conf)
  node = host_selector(ostack, name, node_number, own)
  print(f"Establishing connection to {node.fqdn}({node.ip_address}) as '{user_name}' user...")
  if use_password:
    _open_console(internal, node.ip_address, port=port, user_name=user_name, password=True)
  else:
    if not os.path.exists(conf.local_key_dir):
      os.makedirs(conf.local_key_dir, exist_ok=True)

    if not use_key and node.key_name and node.key_name in conf.key_names and conf.get_key(node.key_name).private_key:
      #PKCS8 format -> openssl
      pkcs8_frmt_B = "-----BEGIN PRIVATE KEY-----"
      pkcs8_frmt_E ="-----END PRIVATE KEY-----"
      openssl_frmt_B = "-----BEGIN RSA PRIVATE KEY-----"
      openssl_frmt_E = "-----END RSA PRIVATE KEY-----"

      key = conf.get_key(node.key_name).private_key
      if pkcs8_frmt_B in key:
        key = key.replace(pkcs8_frmt_B, openssl_frmt_B)

      if pkcs8_frmt_E in key:
        key = key.replace(pkcs8_frmt_E, openssl_frmt_E)

      use_key = os.path.join(conf.local_key_dir, node.key_name) + ".key"
      with open(use_key, "w+", encoding="UTF-8") as f:
        f.write(key)
      try:
        os.chmod(use_key, 0o600)
      except OSError:
        pass
    else:
      raise ValueError("No custom key provided nor private key found in the key storage. Please add private key to"
                       " storage or use custom one with 'use-key' argument")

    _open_console(internal, node.ip_address, user_name=user_name, port=port, key_file=use_key)
