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

from typing import Dict, List

from openstack_cli.modules.apputils.terminal import TableOutput, TableColumn, TableColumnPosition
from openstack_cli.modules.apputils.terminal.get_terminal_size import get_terminal_size

from openstack_cli.modules.apputils.terminal.colors import Colors
from openstack_cli.core.config import Configuration
from openstack_cli.modules.apputils.discovery import CommandMetaInfo
from openstack_cli.modules.openstack import OpenStack, OpenStackQuotas, OpenStackQuotaType, OpenStackUsers

__module__ = CommandMetaInfo("quota", item_help="Show the allowed resource limits for the project")
__args__ = __module__.arg_builder\
  .add_argument("details", bool, "Show detailed resource consumption", default=False)\
  .add_argument("graph", bool, "Show Graphical statistic per-user", default=False)\
  .add_argument("show_clusters", bool, "Show user instances on details page", alias="show-clusters", default=False)


def get_percents(current: float, fmax: float):
  if fmax == 0:
    return 0
  elif fmax == -1:
    return 100

  return (current * 100) / fmax


def get_plain_progress(percents, color:str = "", width: int = 30, ch: str = "#"):
  f = int(round((percents * width) / 100))
  nf = int(width - f)
  if color:
    return f"{color}{ch * f}{' '* nf}{Colors.RESET}"
  else:
    return f"{ch * f}{' '* nf}"

def get_progressbar(percents, color:str = "", width: int = 30):
  return f"[{get_plain_progress(percents, color, width)}]"


def display_graph(_t: OpenStackQuotaType, metrics: Dict[str, Dict[OpenStackQuotaType, int]], users: OpenStackUsers,
                  quotas: OpenStackQuotas):
  """
  Interface example:

  QuotaType Graph
  ----------------

  nnnnnn                           |
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | ##################################                                  XXX XX / 10.94%
                                   |
  mmmmmmmmmmm                      |
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | ################################################################### XXX XX / 25.00%
                                   |
  xxxxxxxx                         |
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | ##                                                                    X XX /  1.00%
                                                                                                          |    |  |      |
                                                                                                             6   3    7
  """

  screen_max_width, _ = get_terminal_size()
  column12_del: str = " | "
  column23_del: str = " "
  column1_max_width: int = max(
    len(next(iter(metrics.keys()))),
    max([len(user) for id in metrics.keys() if (user:=users.get_user(id))])
  )
  column3_max_width: int = 16
  column2_max_width: int = screen_max_width - column1_max_width - column3_max_width - len(column12_del) - len(column23_del)

  max_metric_value: int = max([m for v in  metrics.values() if (m:=v[_t])])

  row_frmt_str: str = f"{{:<{column1_max_width}}}{column12_del}{{:<{column2_max_width}}}{column23_del}{{:>{column3_max_width}}}"

  print(f"{_t.name} Graph")
  print(f"{'-'*len(_t.name)}---------\n")

  _color = Colors.WHITE
  for user_id, user_metric in metrics.items():
    user_name = users.get_user(user_id)
    percents = get_percents(user_metric[_t], max_metric_value)
    actual_percents = get_percents(user_metric[_t], quotas.get_quota(_t)[0])
    progress_bar = get_plain_progress(percents, "", column2_max_width)

    if _t ==OpenStackQuotaType.RAM_MB:
      user_metric_str = f"{int(user_metric[_t]/1024):>4} GB"
    else:
      user_metric_str = user_metric[_t]

    metric_title = f"{user_metric_str:<6}/{actual_percents:6.2f}%"

    _col1_filler = " " * (column1_max_width - len(user_name))
    print(row_frmt_str.format(f"{_color}{user_name}{_col1_filler}{Colors.RESET}", "", ""))
    print(row_frmt_str.format(f"{_color}{user_id}{Colors.RESET}", progress_bar, metric_title))

    _color = Colors.WHITE if _color == Colors.BRIGHT_WHITE else Colors.BRIGHT_WHITE

  print("\n")


def display_combined_graph(metrics: Dict[str, Dict[OpenStackQuotaType, int]], users: OpenStackUsers,
                           quotas: OpenStackQuotas):
  """
  Interface example:

  QuotaType Graph
  ----------------

  nnnnnn                           | #############################################                       XXX XX / 10.94%
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | ##################################                                  XXX XX / 10.94%
                                   | ######################################                              XXX XX / 10.94%
                                   |
  mmmmmmmmmmm                      | ##########                                                          XXX XX / 25.00%
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | ################################################################### XXX XX / 25.00%
                                   | #########################                                           XXX XX / 25.00%
                                   |
  xxxxxxxx                         | #####                                                               XXX XX / 25.00%
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | ##                                                                    X XX /  1.00%
                                   | #                                                                   |    |  |      |
                                                                                                            6   3    7
  """
  _combined_quotas: List[OpenStackQuotaType] = [
    OpenStackQuotaType.INSTANCES,
    OpenStackQuotaType.CPU_CORES,
    OpenStackQuotaType.RAM_MB
  ]
  _colors: Colors = [
    Colors.WHITE,
    Colors.YELLOW,
    Colors.CYAN
  ]
  _quota_colors = {
    _combined_quotas[i]: _colors[i].value for i in range(0, len(_combined_quotas))
  }

  screen_max_width, _ = get_terminal_size()
  column12_del: str = " | "
  column23_del: str = " "
  column1_max_width: int = max(
    len(next(iter(metrics.keys()))),
    max([len(user) for id in metrics.keys() if (user:=users.get_user(id))])
  )
  column3_max_width: int = 16
  column2_max_width: int = screen_max_width - column1_max_width - column3_max_width - len(column12_del) - len(column23_del)

  max_metric_value: Dict[OpenStackQuotaType, int] = {
    q: max([m for v in  metrics.values() if (m:=v[q])]) for q in _combined_quotas
  }

  row_frmt_str: str = f"{{:<{column1_max_width}}}{column12_del}{{:<{column2_max_width}}}{column23_del}{{:>{column3_max_width}}}"


  caption_title = ", ".join([f"{_quota_colors[quota]}{quota.name}{Colors.RESET}" for quota in _combined_quotas])
  print(f"{caption_title} Quota Consuming Graph")
  print(f"{'-'*len(caption_title)}---------\n")

  for user_id, user_metric in metrics.items():
    columns = [users.get_user(user_id), user_id, ""]
    _combined = {_combined_quotas[i]: columns[i] for i in range(0, len(_combined_quotas))}
    progress_bar: Dict[OpenStackQuotaType, str] = {}
    metric_title: Dict[OpenStackQuotaType, str] = {}

    for _t in _combined_quotas:
      percents = get_percents(user_metric[_t], max_metric_value[_t])
      actual_percents = get_percents(user_metric[_t], quotas.get_quota(_t)[0])
      user_metric_str = f"{int(user_metric[_t]/1024):>4} GB" if _t == OpenStackQuotaType.RAM_MB else user_metric[_t]

      progress_bar[_t] = get_plain_progress(percents, "", column2_max_width, ch="⣿")
      metric_title[_t] = f"{user_metric_str:<6}/{actual_percents:6.2f}%"

    for _t in _combined_quotas:
      print(row_frmt_str.format(
        _combined[_t],
        f"{_quota_colors[_t]}{progress_bar[_t]}{Colors.RESET}",
        metric_title[_t]
      ))

    print(row_frmt_str.format("", "", ""))


  print("\n")

def _get_per_user_stats(ostack: OpenStack) -> Dict[str, Dict[OpenStackQuotaType, int]]:
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

  return resources

def _show_graph(ostack: OpenStack, quotas: OpenStackQuotas):
  users = ostack.users
  resources = _get_per_user_stats(ostack)

  display_combined_graph(resources, users, quotas)

  # display_graph(OpenStackQuotaType.INSTANCES, resources, users, quotas)
  # display_graph(OpenStackQuotaType.CPU_CORES, resources, users, quotas)
  # display_graph(OpenStackQuotaType.RAM_MB, resources, users, quotas)

def _show_details(conf: Configuration, ostack: OpenStack, quotas: OpenStackQuotas, show_clusters: bool):
   project_cpu_max, project_cpu_current = quotas.get_quota(OpenStackQuotaType.CPU_CORES)
   project_mem_max, project_mem_current = quotas.get_quota(OpenStackQuotaType.RAM_MB)
   project_instances_max, project_instances_current = quotas.get_quota(OpenStackQuotaType.INSTANCES)
   users = ostack.users
   servers = ostack.servers
   resources = _get_per_user_stats(ostack)

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


def __init__(conf: Configuration, details: bool, show_clusters: bool, graph: bool):
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

    if metric.max_count < 0 :
      c_start = ""
      c_end = ""

    to.print_row(
      f"{c_start}{metric.name}{c_end}",
      f"{c_start}{metric.used}{c_end}",
      "-" if metric.available < 0 else metric.available,
      "-" if metric.max_count < 0 else metric.max_count,
      f"{get_progressbar(prc, c_start)} {c_start}{prc:.1f}%{c_end}"
    )

  print()
  print("* Used/Avl.    - raw metric")
  print()

  if graph:
    _show_graph(stack, limits)
  elif details:
    print("Calculating per-user statistic....")
    _show_details(conf, stack, limits, show_clusters)
