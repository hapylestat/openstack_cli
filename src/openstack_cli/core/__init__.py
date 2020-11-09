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


import os
from openstack_cli import commands
from openstack_cli.modules.config import Configuration


def main_entry():
  conf: Configuration = Configuration()
  is_debug: bool = "debug" in commands.discovery.kwargs_name
  if is_debug:
    os.environ["API_DEBUG"] = "True"
  try:
    # currently hack to avoid key generating on reset command
    if commands.discovery.command_name == "conf" and commands.discovery.command_arguments[:1] == "reset":
      pass
    else:
      conf.initialize()

    commands.discovery.start_application(kwargs={
      "conf": conf,
      "debug": is_debug
    })
  except Exception as e:
    if is_debug:
      raise e
    else:
      print(f"Error: {str(e)}")


if __name__ == "__main__":
  main_entry()
