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

from openstack_cli.modules.apputils.terminal import TableOutput, TableColumn, TableSizeColumn, TableMaxValue
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo
from openstack_cli.modules.openstack import OpenStack, OSImageInfo, DiskImageInfo


__module__ = CommandMetaInfo("rm", item_help="Remove snap item", default_sub_command="list")
__args__ = __module__.arg_builder \
  .add_default_argument("search_pattern", str, "search filter", default="") \
  .add_argument("own", bool, "Show only own items", default=False)


def __init__(conf: Configuration):
  pass
