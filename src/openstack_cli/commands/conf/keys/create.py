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

from openstack_cli.core.output import StatusOutput
from openstack_cli.modules.apputils.terminal import Console
from openstack_cli.modules.openstack import OpenStack
from openstack_cli.modules.openstack.api_objects import VMKeyPairItemBuilder
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo


__module__ = CommandMetaInfo("create", "Create new ssh keys")
__args__ = __module__.arg_builder\
  .add_default_argument("name", str, "Name of the key")

def _create_key(conf:Configuration, ostack:OpenStack, keyBuilder: VMKeyPairItemBuilder):
  key = keyBuilder.build()

  try:
    conf.add_key(key)
    ostack.create_key(key)

    Console.print(f"Key with name '{key.name}' successfully added")
  except ValueError as e:
    if ostack.has_errors:
      so = StatusOutput(None, pool_size=0, additional_errors=ostack.last_errors)
      so.check_issues()
    else:
      Console.print_error(f"Configuration already have the key with name {key.name}, please remove it first")


def __init__(conf: Configuration, name: str):
  from cryptography.hazmat.primitives import serialization as crypto_serialization
  from cryptography.hazmat.primitives.asymmetric import rsa
  from cryptography.hazmat.backends import default_backend as crypto_default_backend

  ostack = OpenStack(conf)

  key = rsa.generate_private_key(
    backend=crypto_default_backend(),
    public_exponent=65537,
    key_size=2048
  )
  private_key = key.private_bytes(
    crypto_serialization.Encoding.PEM,
    crypto_serialization.PrivateFormat.TraditionalOpenSSL,  # PKCS8 is not supported best by paramiko
    crypto_serialization.NoEncryption())
  public_key = key.public_key().public_bytes(
    crypto_serialization.Encoding.OpenSSH,
    crypto_serialization.PublicFormat.OpenSSH
  )

  keyBuilder = VMKeyPairItemBuilder() \
    .set_name(name) \
    .set_private_key(private_key) \
    .set_public_key(public_key)

  _create_key(conf, ostack, keyBuilder)


