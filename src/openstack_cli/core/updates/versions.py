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

from openstack_cli.commands.version import ConfProperties
from openstack_cli.modules.apputils.config import StorageProperty
from openstack_cli.modules.apputils.config.upgrades import upgrade, UpgradeCatalog, NoUpgradeNeeded


@upgrade(version=0.0)
class VersionCheck(UpgradeCatalog):
  def __get_current_version(self) -> ConfProperties:
    from openstack_cli.commands.version import get_current_version
    return get_current_version()

  def _get_do_upgrade_dev_version(self):
    p = self._storage.get_property("general", "dev_upgrade", StorageProperty(name="dev_upgrade", value="True"))
    try:
      return p.value == "True"
    except ValueError:
      return True

  def _set_do_upgrade_dev_version(self, disable: bool):
    self._storage.set_property("general", StorageProperty(name="dev_upgrade", value=str(disable)))

  def __call__(self, *args, **kwargs):
    current_version = self.__get_current_version().version
    if current_version != 0.0 and current_version == self._conf.version:
      raise NoUpgradeNeeded()
    elif current_version == 0.0 and not self._get_do_upgrade_dev_version():
      raise NoUpgradeNeeded()

    if self._catalog_version is None:
      return
    print("""
..#######...######..##.....##.##.....##
.##.....##.##....##.##.....##.###...###
.##.....##.##.......##.....##.####.####
.##.....##..######..##.....##.##.###.##
.##.....##.......##..##...##..##.....##
.##.....##.##....##...##.##...##.....##
..#######...######.....###....##.....##

OpenStack tool need to be configured first before it could be used.

""")
    if current_version == 0.0:
      print("!!! Warning !!! The current application is a dev/self-build version")
      self._set_do_upgrade_dev_version(self.ask_question("Try to migrate configuration schema each time (y/n): "))


