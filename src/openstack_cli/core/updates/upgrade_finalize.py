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

from openstack_cli.commands.version import get_current_version
from openstack_cli.core import Configuration
from openstack_cli.modules.apputils.config.upgrades import UpgradeCatalog, upgrade


@upgrade(version=999.0)
class FinalizeUpgrade(UpgradeCatalog):

  def __call__(self, *args, **kwargs):
    assert isinstance(self._conf, Configuration)
    conf: Configuration = self._conf
    version: float = get_current_version().version
    print(f"Complete version update to {version}")
    conf.version = version
