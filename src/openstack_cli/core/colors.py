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
  BLACK = "\033[30m"
  RED = "\033[31m"
  GREEN = "\033[32m"
  YELLOW = "\033[33m"
  BLUE = "\033[34m"
  MAGENTA = "\033[35m"
  CYAN = "\033[36m"
  WHITE = "\033[37m"

  BRIGHT_BLACK = "\033[30;1m"
  BRIGHT_RED = "\033[31;1m"
  BRIGHT_GREEN = "\033[32;1m"
  BRIGHT_YELLOW = "\033[33;1m"
  BRIGHT_BLUE = "\033[34;1m"
  BRIGHT_MAGENTA = "\033[35;1m"
  BRIGHT_CYAN = "\033[36;1m"
  BRIGHT_WHITE = "\033[37;1m"

  RESET = "\033[0m"

