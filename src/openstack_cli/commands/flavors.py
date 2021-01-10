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
from openstack_cli.core.output import TableOutput, TableColumn, TableSizeColumn, Console
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo

__module__ = CommandMetaInfo("flavors", "Display available VM resource configurations")
__args__ = __module__.arg_builder\
  .add_default_argument("image_name", str, "Image name (alias)", default="")\
  .add_argument("sort_by_name", bool, "Sort the list by name", alias="by-name", default=False)\
  .add_argument("all", bool, "Show all flavors", default=False)


def __init__(conf: Configuration, image_name: str, sort_by_name: bool, all: bool):
  sort_keys = {
    True: lambda x: x.name,
    False: lambda x: (x.vcpus, x.ram, x.disk, x.ephemeral_disk)
  }
  ostack = OpenStack(conf)
  if image_name:
    images = list(ostack.get_image_by_alias(image_name))
    if images and len(images) > 1:
      Console.print_error(f"Image '{image_name}' matches more than one image")
      return
    elif not images:
      Console.print_error(f"No image with name '{image_name}' found")
      return
    flavors = sorted(ostack.get_flavors(images[0]), key=sort_keys[sort_by_name])
  else:
    flavors = sorted(ostack.flavors, key=sort_keys[sort_by_name])

  table = TableOutput(
    TableColumn("Name", 20),
    TableColumn("vCPU", 5),
    TableColumn("RAM", 9),
    TableColumn("D+E Size", 15),
    TableColumn("Disk", 15),
    TableColumn("Ephemeral Disk", 15),
    TableColumn("Id", 36)
  )

  table.print_header()

  for flavor in flavors:
    if not all and flavor.ephemeral_disk == 0:
      continue
    table.print_row(
      flavor.name,
      flavor.vcpus,
      TableSizeColumn(flavor.ram).value,
      TableSizeColumn(flavor.sum_disk_size).value,
      TableSizeColumn(flavor.disk).value,
      TableSizeColumn(flavor.ephemeral_disk).value,
      flavor.id
    )
