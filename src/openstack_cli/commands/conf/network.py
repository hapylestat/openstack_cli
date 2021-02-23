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

from openstack_cli.modules.openstack.objects import OSNetworkItem
from openstack_cli.core.output import Console

from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo

__module__ = CommandMetaInfo("network", "Reconfigure default network interface for the new VM")


def configure_network(conf: Configuration):
  from openstack_cli.modules.openstack import OpenStack
  from openstack_cli.commands.networks import get_default_network

  old_network = conf.default_network

  if old_network:
    Console.print_warning(f"Previous network name: {old_network.name}")
    Console.print_warning("!!! THIS WILL CHANGE DEFAULT NETWORK !!!")

  net: OSNetworkItem = get_default_network(conf, OpenStack(conf), force=True)

  if net:
    print(f"\nSelected network: {net.name}")
    return

  Console.print_error("Network not set")



def __init__(conf: Configuration):
  configure_network(conf)
