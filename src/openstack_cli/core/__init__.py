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
from openstack_cli import __app_name__ as app_name
from openstack_cli import commands
from openstack_cli.core.config import Configuration
from openstack_cli.core.updates import upgrade_manager, import_upgrade_packs


def main_entry():

  conf: Configuration = Configuration(upgrade_manager=upgrade_manager, app_name=app_name, lazy_init=True)
  if upgrade_manager.upgrade_required(conf):
    import_upgrade_packs()

  is_debug: bool = "debug" in commands.discovery.kwargs_name
  if is_debug:
    os.environ["API_DEBUG"] = "True"
  try:
    # currently hack to avoid key generating on reset command
    if commands.discovery.command_name == "conf" and commands.discovery.command_arguments[:1] == "reset":
      pass
    elif commands.discovery.command_name == "version":
      pass
    else:
      conf.initialize()
      if conf.check_for_update:
        from openstack_cli.commands.version import print_little_banner
        print_little_banner()

    commands.discovery.start_application(kwargs={
      "conf": conf,
      "debug": is_debug
    })
  except KeyboardInterrupt:
    print("Cancelled by user...")
  except Exception as e:
    if is_debug:
      raise e
    else:
      print(f"Error: {str(e)}")


if __name__ == "__main__":
  main_entry()
