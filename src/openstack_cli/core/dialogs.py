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


def get_tk():
  """
  At this point terminal will lost focus due to Tk root window, thus initializing this at the last moment.

  :rtype typing.Tuple[tkinter.Tk, tkinter.filedialog]
  """
  try:
    tk_enabled=True
    from tkinter import filedialog, TclError, Tk
  except ImportError:
    tk_enabled=False
    class TclError(Exception): pass
    class Tk(object): pass
    class filedialog(object):
      @staticmethod
      def askopenfilename(*args, **kwargs):
        return None

  if not tk_enabled:
    return None, None

  try:
    root: Tk = Tk()
    root.withdraw()
    return root, filedialog
  except TclError:
    return None, None

def ask_open_file(title: str = "Select file", allowed_extensions=(('All files', '*.*'),)) -> str:
  root, filedialog = get_tk()
  if filedialog:
    return filedialog.askopenfilename(title=title, filetypes=allowed_extensions)
  else:
    return input(f"{title}: ")
