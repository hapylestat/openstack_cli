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

import sys

if sys.platform == "win32":
  import ctypes

  kernel32 = ctypes.windll.kernel32
  kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


class Colors(object):
  RED = "\033[0;91m"
  YELLOW = "\033[0;93m"
  GREEN = "\033[0;92m"
  RESET = "\033[0m"
