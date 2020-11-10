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

import os
from calendar import timegm
from datetime import datetime
from time import strptime, sleep
from typing import List, Tuple

from openstack_cli.core.colors import Colors
from openstack_cli.modules.curl import curl
from openstack_cli.modules.json2obj import SerializableObject

from openstack_cli import __app_name__, __app_version__, __my_root_dir__, __properties_file__
from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo

__module__ = CommandMetaInfo("version")
__args__ = __module__.get_arguments_builder()


class ConfProperties(SerializableObject):
  app_name: str = ""
  app_version: str = ""
  commit_hash: str = ""
  update_src: str = ""

  @property
  def short_hash(self):
    return self.commit_hash[:10]

  @property
  def version(self) -> float:
    if self.app_version.startswith("v"):
      try:
        return float(self.app_version[1:])
      except:
        return 0.0
    try:
      return float(self.app_version)
    except:
      return 0.0

#
# ================= GITHUB OBJECTS
#


class GHAsset(SerializableObject):
  __strict__ = False

  name: str = ""
  browser_download_url: str = ""
  state: str = ""
  created_at: str = ""
  size: int = 0

  @property
  def created(self):
    return datetime.utcfromtimestamp(timegm(strptime(self.created_at, "%Y-%m-%dT%H:%M:%SZ")))


class GHRelease(SerializableObject):
  __strict__ = False

  tag_name: str = ""
  name: str = ""
  prerelease: bool = False
  assets: List[GHAsset] = []
  body: str = ""

  @property
  def version(self) -> float:
    if self.tag_name.startswith("v"):
      try:
        return float(self.tag_name[1:])
      except:
        return 0.0
    try:
      return float(self.tag_name)
    except:
      return 0.0


def get_current_version() -> ConfProperties:
  conf_file = os.path.join(__my_root_dir__, __properties_file__)
  if not os.path.exists(conf_file):
    return ConfProperties(
      app_name=__app_name__,
      app_version=__app_version__,
      commit_hash="dev-build",
      update_src=""
    )

  with open(conf_file, "r", encoding="UTF-8") as f:
    return ConfProperties(serialized_obj=f.read())


def print_banner(ver: ConfProperties):
  print(f"{Colors.WHITE.wrap(ver.app_name)} {ver.app_version} ({Colors.BRIGHT_BLACK.wrap(ver.short_hash)})")


def get_asset(ver: ConfProperties) -> Tuple[GHRelease, GHAsset]:
  r = curl(ver.update_src)
  if r.code not in [200, 201]:
    return None

  releases = sorted([GHRelease(serialized_obj=i) for i in r.from_json()], key=lambda x: x.version, reverse=True)
  release = releases[0] if releases else None

  if not release or release.version <= ver.version:
    return None

  for _asset in release.assets:
    if ".whl" in _asset.name and _asset.state == "uploaded":
      return release, _asset


def check():
  no_release = ""
  ver = get_current_version()
  print_banner(ver)

  if not ver.update_src:
    print(no_release)
    return

  release, asset = get_asset(ver)
  if not asset:
    print(no_release)
    return

  banner = f"""
  {Colors.BRIGHT_BLACK}=========================================================================================={Colors.RESET}
                                      {Colors.BRIGHT_CYAN.wrap("WARNIGN")}
  {Colors.BRIGHT_BLACK}=========================================================================================={Colors.RESET}
  Current version of {Colors.WHITE.wrap(ver.app_name)} is {Colors.BRIGHT_RED.wrap(ver.version)}, however version {Colors.BRIGHT_GREEN.wrap(release.version)} is available!

  {Colors.WHITE.wrap("Filename")}    : {asset.name}
  {Colors.WHITE.wrap("Size")}        : {asset.size / 1024:.2f} Kb
  {Colors.WHITE.wrap("Created")}     : {asset.created}
  {Colors.WHITE.wrap("Download url")}: {asset.browser_download_url}

  How to install:
   pip install {asset.browser_download_url}
   pip3 install {asset.browser_download_url}
   python3 -m pip install {asset.browser_download_url}
  {Colors.BRIGHT_BLACK}=========================================================================================={Colors.RESET}
  """
  print(banner)


def print_little_banner():
  ver = get_current_version()
  if not ver.update_src:
    return

  release, asset = get_asset(ver)
  if not asset:
    return

  banner = f"""
  {Colors.BRIGHT_BLACK}=========================================================================================={Colors.RESET}
    Current version of {Colors.WHITE.wrap(ver.app_name)} is {Colors.BRIGHT_RED.wrap(ver.version)}, however version {Colors.BRIGHT_GREEN.wrap(release.version)} is available!

    More details available using "{Colors.YELLOW}version{Colors.RESET}" command
  {Colors.BRIGHT_BLACK}=========================================================================================={Colors.RESET}
  """
  print(banner, flush=True)


def __init__(conf: Configuration):
  check()
