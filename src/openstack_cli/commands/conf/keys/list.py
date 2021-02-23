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

from typing import Dict, List
from openstack_cli.core.output import Console
from openstack_cli.modules.apputils.terminal import TableColumnPosition, TableColumn, TableOutput
from openstack_cli.commands.conf.keys import CHECK_ICON, KEY_ICON, UNCHECK_ICON
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo
from openstack_cli.modules.openstack import VMKeypairItemValue, OpenStack


__module__ = CommandMetaInfo("list", "list available ssh keys")


def _keys_list(conf: Configuration, ostack: OpenStack, show_row_nums: bool = False) -> List[VMKeypairItemValue]:
  server_keypairs: Dict[int, VMKeypairItemValue] = {hash(key): key for key in ostack.get_keypairs()}
  conf_keys = conf.get_keys()
  if not conf_keys:
    Console.print_warning("No keys found, add new ones")
    return []

  max_key_len = len(max(conf.key_names))
  to = TableOutput(
    TableColumn("Key Name", max_key_len + len(KEY_ICON), inv_ch=len(KEY_ICON)-2, pos=TableColumnPosition.left),
    TableColumn("Priv.Key", 3, inv_ch=len(CHECK_ICON)-2, pos=TableColumnPosition.center),
    TableColumn("Pub.Key", 3, inv_ch=len(CHECK_ICON)-2, pos=TableColumnPosition.center),
    TableColumn("Rem.Sync", 3, inv_ch=len(CHECK_ICON), pos=TableColumnPosition.center),
    TableColumn("Fingerprint", 48, pos=TableColumnPosition.left),
    print_row_number=show_row_nums
  )

  to.print_header()

  for kp in conf_keys:
    to.print_row(
      f"{KEY_ICON}{kp.name}",
      CHECK_ICON if kp.private_key else UNCHECK_ICON,
      CHECK_ICON if kp.public_key else UNCHECK_ICON,
      CHECK_ICON if hash(kp) in server_keypairs else UNCHECK_ICON,
      server_keypairs[hash(kp)].fingerprint
    )

  return conf_keys


def __init__(conf: Configuration):
  ostack = OpenStack(conf)
  _keys_list(conf, ostack)
