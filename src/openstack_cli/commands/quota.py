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

from typing import Dict

from openstack_cli.modules.apputils.terminal import TableOutput, TableColumn, TableColumnPosition

from openstack_cli.modules.apputils.terminal.colors import Colors
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo
from openstack_cli.modules.openstack import OpenStack, OpenStackQuotas, OpenStackQuotaType, OpenStackVMInfo

__module__ = CommandMetaInfo("quota", item_help="Show the allowed resource limits for the project")
__args__ = __module__.arg_builder\
  .add_argument("details", bool, "Show detailed resource consumption", default=False)\
  .add_argument("show_clusters", bool, "Show user instances on details page", alias="show-clusters", default=False)


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

def _show_details(conf: Configuration, ostack: OpenStack, quotas: OpenStackQuotas, show_clusters: bool):
   project_cpu_max, project_cpu_current = quotas.get_quota(OpenStackQuotaType.CPU_CORES)
   project_mem_max, project_mem_current = quotas.get_quota(OpenStackQuotaType.RAM_MB)
   project_instances_max, project_instances_current = quotas.get_quota(OpenStackQuotaType.INSTANCES)

   servers = ostack.servers

   resources = {}

   for server in ostack.servers.items:
     if server.owner_id not in resources:
       resources[server.owner_id] = {
         "clusters": {},
         OpenStackQuotaType.CPU_CORES: 0,
         OpenStackQuotaType.RAM_MB: 0,
         OpenStackQuotaType.INSTANCES: 0
       }

     record = resources[server.owner_id]

     record[OpenStackQuotaType.CPU_CORES] += server.flavor.vcpus
     record[OpenStackQuotaType.INSTANCES] += 1
     record[OpenStackQuotaType.RAM_MB] += server.flavor.raw.ram
     if server.cluster_name not in record["clusters"]:
       record["clusters"][server.cluster_name] = 0

     record["clusters"][server.cluster_name] += 1

     resources[server.owner_id] = record

   padding = " " * 5
   print("Per-User statistic: ")

   user_sum_instances: int = 0
   user_sum_cpu: int = 0
   user_sum_mem: int = 0
   for user_id, record in resources.items():
     user_name = ostack.users.get_user(user_id)
     print(f"User id: {user_name if user_name else 'unknown'} ({user_id})")
     user_instances = record[OpenStackQuotaType.INSTANCES]
     user_mem = record[OpenStackQuotaType.RAM_MB]
     user_cpu = record[OpenStackQuotaType.CPU_CORES]

     print(f"{padding}Instances: {user_instances:<8} ({get_percents(user_instances, project_instances_max):0.2f}% from prj.cap.)")
     print(f"{padding}CPU      : {user_cpu:<8} ({get_percents(user_cpu, project_cpu_max):0.2f}% from prj.cap.)")
     print(f"{padding}MEM (GB) : {user_mem/1024:<8.2f} ({get_percents(user_mem, project_mem_max):0.2f}% from prj.cap.)")
     if show_clusters:
       _clusters = record["clusters"]  # {'cluster name': nodes amount}
       _clusters = [f"{k} (hosts: {v})" for k, v in _clusters.items()]

       title = "Clusters :"
       _padding = " " * len(title)
       _title_displayed: bool = False
       for cluster in _clusters:
         if _title_displayed:
           print(f"{padding}{_padding} {cluster}")
           continue

         print(f"{padding}{title} {cluster}")
         _title_displayed = True
     print()

     user_sum_cpu += user_cpu
     user_sum_mem += user_mem
     user_sum_instances += user_instances

   print("--------------------")
   print("Summary:")
   print(f"{padding}∑ Inst.  : {user_sum_instances:<9} "
         f"({get_percents(user_sum_instances, project_instances_max):0.2f}% calc./"
         f"{get_percents(project_instances_current, project_instances_max):0.2f}% act.)")

   print(f"{padding}∑ CPU    : {user_sum_cpu:<9} "
         f"({get_percents(user_sum_cpu, project_cpu_max):0.2f}% calc./"
         f"{get_percents(project_cpu_current, project_cpu_max):0.2f}% act.)")
   print(f"{padding}∑ MEM(GB): {user_sum_mem/1024:<9.2f} "
         f"({get_percents(user_sum_mem, project_mem_max):0.2f}% calc./"
         f"{get_percents(project_mem_current, project_mem_max):0.2f}% act.)")
   print()


def __init__(conf: Configuration, details: bool, show_clusters: bool):
  stack = OpenStack(conf)
  limits = stack.quotas

  to = TableOutput(
    TableColumn("Metric", length=limits.max_metric_len, pos=TableColumnPosition.right, sep=":", inv_ch=Colors.RED.wrap_len()),
    TableColumn("Used", length=7, pos=TableColumnPosition.right, sep="|", inv_ch=Colors.RED.wrap_len()),
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

  if details:
    print("Calculating per-user statistic....")
    _show_details(conf, stack, limits, show_clusters)
