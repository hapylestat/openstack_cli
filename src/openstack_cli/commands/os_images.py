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

from typing import List, Tuple

from openstack_cli.core.output import TableOutput, TableColumn, TableSizeColumn
from openstack_cli.modules.openstack import OpenStack
from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo


__module__ = CommandMetaInfo("os-images")
__args__ = __module__.get_arguments_builder() \
  .add_argument("all", bool, "Display all available images", default=False)\
  .add_argument("snapshot", bool, "Display only snapshots", default=False)\
  .add_default_argument("search_pattern", str, "search query", default="")


def __init__(conf: Configuration, search_pattern: str, snapshot: bool, all: bool):
  ostack = OpenStack(conf)
  if snapshot:
    show_snap(ostack, search_pattern)
  elif all:
    show_all(ostack, search_pattern)
  else:
    show_normal(ostack, search_pattern)


def show_snap(ostack: OpenStack, search_pattern: str):
  pass


def show_all(ostack: OpenStack, search_pattern: str):
  images = ostack.images

  table = TableOutput(
    TableColumn("Id", 36),
    TableColumn("Name", 60),
    TableColumn("Size", 9),
    TableColumn("Status", 10),
    TableColumn("Description", 20)
  )

  table.print_header()

  for image in images:
    if image.image_type:
      continue

    if search_pattern and search_pattern.lower() not in image.name.lower():
      continue

    table.print_row(
      image.id,
      image.name,
      TableSizeColumn(image.size).value,
      image.status,
      image.description if image.description else "-"
    )


def show_normal(ostack: OpenStack, search_pattern: str):
  images = ostack.os_images

  table = TableOutput(
    TableColumn("Name", 30),
    TableColumn("Alias", 30),
    TableColumn("Size", 9),
    TableColumn("Description", 90)
  )
  table.print_header()

  for image in images:
    if search_pattern and search_pattern.lower() not in image.name.lower():
      continue

    table.print_row(
      image.name,
      image.alias,
      TableSizeColumn(image.size).value,
      image.description
    )
