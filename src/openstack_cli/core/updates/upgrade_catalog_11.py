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

from openstack_cli.commands.networks import print_networks
from openstack_cli.commands.conf.keys.create import _create_key
from openstack_cli.core import Configuration
from openstack_cli.modules.apputils.terminal import TableOutput, TableColumn
from openstack_cli.core.output import Console, StatusOutput
from openstack_cli.modules.apputils.config.upgrades import UpgradeCatalog, upgrade
from openstack_cli.modules.openstack import OpenStack, AuthRequestType
from openstack_cli.modules.openstack.objects import VMProject


@upgrade(version=1.1)
class UpgradeCatalog11(UpgradeCatalog):
  def __call__(self, *args, **kwargs):
    assert isinstance(self._conf, Configuration)
    conf: Configuration = self._conf

    if not conf.os_address:
      conf.os_address = self.ask_text_question("OpenStack identity api address: ")

    if not conf.os_login:
      conf.os_login = self.ask_text_question("OpenStack username: ")

    if not conf.os_password:
      conf.os_password = self.ask_text_question("OpenStack password: ", encrypted=True)

    osvm = OpenStack(conf)
    so = StatusOutput(additional_errors=osvm.last_errors)

    if not conf.project.id:
      print("Fetching available projects....")
      if not osvm.login(_type=AuthRequestType.UNSCOPED):
        if osvm.has_errors:
          so.check_issues()
          self.reset()
        raise RuntimeError("Unable to continue")

      projects = osvm.projects
      to = TableOutput(
        TableColumn("Id", 33),
        TableColumn("Name", 20),
        TableColumn("Enabled", 6),
        print_row_number=True
      )

      to.print_header()
      for prj in projects:
        to.print_row(prj.id, prj.name, prj.enabled)

      n: int = Console.ask("Select the project number to be used: ", _type=int)
      conf.project = VMProject(id=projects[n].id, name=projects[n].name, domain=projects[n].domain_id)
      osvm.logout()

    print(f"Checking login for the project '{conf.project.name}'...")
    if not osvm.login():
      if osvm.has_errors:
        so.check_issues()
        self.reset()
      raise RuntimeError("Unable to continue")

    if not conf.default_network:
      print("Please select default network for the VM (could be changed via 'conf network' command):")
      _net = print_networks(ostack=osvm, select=True)
      if not _net:
        raise RuntimeError("Network is not selected")
      conf.default_network = _net

    if not conf.default_vm_password:
      _p = self.ask_text_question("Default VM password: ", encrypted=True)
      if not _p:  # ToDo: add more strict check
        _p = "qwerty"
      conf.default_vm_password = _p

    _default_keypair_name = "default"
    keys = conf.get_keys()
    srv_keys = osvm.get_keypairs(no_cache=True)
    _is_srv_key = False
    _is_cfg_key = False
    for srv_key in srv_keys:
      if srv_key.name == _default_keypair_name:
        _is_srv_key = True
        break

    for cfg_key in keys:
      if cfg_key.name == _default_keypair_name:
        _is_cfg_key = True
        break

    if _is_cfg_key and not _is_srv_key:
      print(f"Purging  '{_default_keypair_name}' key from configuration")
      conf.delete_key(_default_keypair_name)
      _is_cfg_key = False

    if not _is_cfg_key and not _is_srv_key:
      print(f"Creating new '{_default_keypair_name}' keypair..")
      _create_key(conf, osvm, _default_keypair_name)
      print(f"Key '{_default_keypair_name}' could be exported using command 'conf keys export {_default_keypair_name}'")

    if not _is_cfg_key and _is_srv_key:
      print(f"Public key '{_default_keypair_name}' would be re-synced locally, please add private key or re-generate new default key")
