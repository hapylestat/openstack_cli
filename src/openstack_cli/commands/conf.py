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


def __init__(conf: Configuration, sub_command: str):
  if sub_command == "reset":
    conf.reset()
    print("Configuration reset completed")
    return

  print(f"Address: {conf.os_address}, login: {conf.os_login} and pass: {conf.os_password}")

  # conf = SQLStorage()
  # a = conf.get_property("general", "option")
  # b = conf.get_property("general", "enc")
  # if not a:
  #   print("Property not found, trying to create!")
  #   conf.set_property("general", StorageProperty("option", "text", "lol world!"))
  #   conf.set_property("general", StorageProperty("enc", "encrypted", "encrypted text"))
  #   a = conf.get_property("general", "option")
  #   b = conf.get_property("general", "enc")
  #
  # if a:
  #   print(f"a: {a.name} = {a.value}")
  # else:
  #   print("Can't fetch the property a")
  #
  # if b:
  #   print(f"b: {b.name} = {b.value}")
  # else:
  #   print("Can't fetch the property b")
