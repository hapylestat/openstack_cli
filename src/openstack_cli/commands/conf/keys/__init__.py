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
from openstack_cli.modules.apputils.discovery.commands import NotImplementedCommandException
from openstack_cli.modules.apputils.terminal import Colors
from openstack_cli.modules.apputils.terminal.colors import Symbols
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo

__module__ = CommandMetaInfo("keys", "Manage ssh keys for the VM", default_sub_command="list")

CHECK_ICON = Symbols.CHECK.color(Colors.GREEN)
UNCHECK_ICON = Symbols.CROSS.color(Colors.RED)
KEY_ICON = Symbols.KEY.color(Colors.BRIGHT_YELLOW)

def __init__(conf: Configuration):
  raise NotImplementedCommandException()
