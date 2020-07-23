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

from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo


__module__ = CommandMetaInfo("conf")
__args__ = __module__.get_arguments_builder()\
  .add_default_argument("sub_command", str, "name of the sub-command", default="help")

from openstack_cli.modules.openstack.objects import OSNetworkItem


def configure_network(conf: Configuration):
  from openstack_cli.modules.openstack import OpenStack
  from openstack_cli.commands.networks import get_default_network

  old_network = conf.default_network

  if old_network:
    print(f"Previous network name: {old_network.name}")
    print("!!! THIS WILL CHANGE DEFAULT NETWORK !!!")

  net: OSNetworkItem = get_default_network(conf, OpenStack(conf), force=True)

  if net:
    print(f"\nSelected network: {net.name}")
    return

  print("\nNetwork not set")


def __init__(conf: Configuration, sub_command: str):
  if sub_command == "reset":
    conf.reset()
    print("Configuration reset completed")
  elif sub_command == "reset-cache":
    conf.invalidate_cache()
    print("Cached data flushed")
  elif sub_command == "network":
    configure_network(conf)
  else:
    print("Keep watching for the new features, thanks :) ")
