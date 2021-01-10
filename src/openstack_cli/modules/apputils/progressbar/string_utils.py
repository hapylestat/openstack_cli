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
#
#  Github: https://github.com/hapylestat/apputils
#
#

import string
import re
from collections import defaultdict


FORMAT_RE = re.compile("\{\{([^{]*)\}\}")


def safe_format(s, **kwargs):
  """
  :type s str
  """
  return string.Formatter().vformat(s, (), defaultdict(str, **kwargs))


def safe_format_sh(s, **kwargs):
  """
  :type s str
  :type kwargs dict
  """

  to_replace = set(kwargs.keys()) & set(FORMAT_RE.findall(s))

  for item in to_replace:
    s = s.replace("{{" + item + "}}", kwargs[item])

  return s
