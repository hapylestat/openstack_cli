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


from openstack_cli.modules.openstack import OpenStack
from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo


__module__ = CommandMetaInfo("up")
__args__ = __module__.get_arguments_builder() \
  .add_default_argument("name", str, "name of the cluster", default="test")\
  .add_default_argument("count", int, "amount of nodes", default=0)\
  .add_argument("flavor", str, "Host flavor", default="")\
  .add_argument("os", str, "VM OS to spin up", default="")


def __init__(conf: Configuration, name: str, count: int, flavor: str, os: str):
  ostack = OpenStack(conf)
  ostack.start_instance()


