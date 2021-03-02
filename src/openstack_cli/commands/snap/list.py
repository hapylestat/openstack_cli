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

from typing import List, Dict

from openstack_cli.modules.apputils.terminal import TableOutput, TableColumn, TableSizeColumn, TableMaxValue
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo
from openstack_cli.modules.openstack import OpenStack, OSImageInfo, DiskImageInfo

__module__ = CommandMetaInfo("list", item_help="Manage OpenStack Snapshoots", default_sub_command="list")
__args__ = __module__.arg_builder\
  .add_default_argument("search_pattern", str, "search filter", default="")\
  .add_argument("own", bool, "Show only own items", default=False)


def __init__(conf: Configuration, search_pattern: str, own: bool):
  ostack = OpenStack(conf)
  image_id_ref: Dict[str, DiskImageInfo] = {img.id: img  for img in ostack.images}
  images: List[tuple[DiskImageInfo, str, DiskImageInfo]] = []    #  Snap Image, Base Image Name, Base Image
  user_id = conf.user_id

  _search_pattern = search_pattern.lower() if search_pattern else None

  max_name_len: TableMaxValue[int] = TableMaxValue(0)
  max_base_name: TableMaxValue[int] = TableMaxValue(0)

  for image in ostack.images:
    if own and image.user_id != user_id:
      continue
    if not image.image_type:
      continue
    if search_pattern and _search_pattern not in image.name.lower():
      continue

    base_image: DiskImageInfo = image_id_ref[image.base_image_ref] if image.base_image_ref in image_id_ref else None
    base_os_image: OSImageInfo = ostack.get_os_image(base_image) if base_image else None

    base_image_name: str = base_os_image.name if base_os_image else\
                         base_image.name if base_image else "unknown"
    max_name_len.process(len(image.name))
    max_base_name.process(len(base_image_name))

    images.append((image, base_image_name, base_image,))

  table = TableOutput(
    TableColumn("Name", max_name_len.value),
    TableColumn("Status", 10),
    TableColumn("Base Image Name", max_base_name.value),
    TableColumn("Snap Size | Base Sise | Total Size", 36),
    TableColumn("Visibility", 10)
  )

  table.print_header()

  for image, base_name, base_image in images:
    snap_size = TableSizeColumn(image.size)
    base_image_size = TableSizeColumn(base_image.size) if base_image else snap_size

    table.print_row(
      image.name,
      image.status,
      base_name,
      f"{(snap_size-base_image_size).value:>10} | {base_image_size.value:>10} | {snap_size.value:>10}",
      image.visibility
    )
