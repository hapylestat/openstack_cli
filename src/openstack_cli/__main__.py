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

from __future__ import absolute_import

import os
import sys


# If we are running from a wheel, add the wheel to sys.path
# This allows the usage python pip-*.whl/pip install pip-*.whl
if __package__ == '':
  # __file__ is pip-*.whl/pip/__main__.py
  # first dirname call strips of '/__main__.py', second strips off '/pip'
  # Resulting path is the name of the wheel itselfs
  # Add that to sys.path so we can import pip
  path = os.path.dirname(os.path.dirname(__file__))
  sys.path.insert(0, path)

from openstack_cli import core

if __name__ == '__main__':
  print("Hey test!")
  sys.exit(core.main_entry())
