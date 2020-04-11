#!/usr/bin/env python3

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

import codecs
import os
import re
from typing import List

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
  # auto-detects file encoding
  with codecs.open(os.path.join(here, *parts), 'r') as fp:
    return fp.read()


def find_tag(tag: str or List[str], *file_paths: str):
  tag_file = read(*file_paths)
  if isinstance(tag, str):
    tag = [tag]

  result_list: List[str] = []
  for t in tag:
    tag_match = re.search(
      rf"^__{t}__ = ['\"]([^'\"]*)['\"]",
      tag_file,
      re.M,
    )
    if tag_match:
      result_list.append(tag_match.group(1))

  if len(result_list) != len(tag):
    raise RuntimeError(f"Unable to find some tag from the list: {', '.join(tag)}")

  return result_list


def load_requirements():
  data = read("requirements.txt")
  return data.split("\n")


app_name, app_version = find_tag(["app_name", "app_version"], "src", "openstack_cli", "__init__.py")

setup(
  name=app_name,
  version=app_version,
  description="OpenStack VM orchestrator",
  long_description="OpenStack VM orchestrator",
  license='MIT',
  classifiers=[
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
  ],
  author='hapylestat@apache.org',
  package_dir={"": "src"},
  packages=find_packages(
    where="src",
    exclude=["contrib", "docs", "tests*", "tasks"],
  ),
  install_requires=load_requirements(),
  entry_points={
    "console_scripts": [
      "osvm=openstack_cli.core:main_entry",
      ],
  },
  zip_safe=True,
  python_requires='>=3.7',
)
