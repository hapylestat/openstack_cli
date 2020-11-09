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
from typing import List

from openstack_cli.core.output import TableOutput, TableColumn, TableColumnPosition

from openstack_cli.core.colors import Colors
from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo
from openstack_cli.modules.openstack import OpenStack


__module__ = CommandMetaInfo("quota")


def get_percents(current: float, fmax: float):
  if fmax == 0:
    return 0

  return (current * 100) / fmax


def get_progressbar(percents, color=""):
  width = 30
  f = int(round((percents * width) / 100))
  nf = int(width - f)
  if color:
    return f"[{color}{'#' * f}{' '* nf}{Colors.RESET}]"
  else:
    return f"[{'#' * f}{' '* nf}]"


def __init__(conf: Configuration):
  stack = OpenStack(conf)
  limits = stack.quotas

  to = TableOutput(
    TableColumn("Metric", length=limits.max_metric_len, pos=TableColumnPosition.right, sep=":"),
    TableColumn("Used", length=7, pos=TableColumnPosition.right, sep="|",),
    TableColumn("Avl.", length=7, pos=TableColumnPosition.right, sep="|",),
    TableColumn("Total", length=7, pos=TableColumnPosition.right),
    TableColumn("", length=30)
  )

  print(f"Region {conf.region} stats\n")

  to.print_header(solid=True)

  for metric in limits:
    prc = get_percents(metric.used, metric.max_count)
    c_end = Colors.RESET if prc > 80 else ""
    c_start = Colors.RED if prc > 90 else Colors.YELLOW if prc > 80 else ""

    to.print_row(
      f"{c_start}{metric.name}{c_end}",
      f"{c_start}{metric.used}{c_end}",
      metric.available,
      metric.max_count,
      f"{get_progressbar(prc, c_start)} {c_start}{prc:.1f}%{c_end}"
    )

  print()
  print("* Used/Avl.    - raw metric")
