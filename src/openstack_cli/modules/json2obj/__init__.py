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

import json
from types import FunctionType
from typing import List, Optional


class SerializableObject(object):
  """
   BaseConfigView is a basic class, which providing Object to Dict, Dict to Object conversion with
   basic fields validation.

   Should be subclassed for proper usage. For example we have such dictionary:

   my_dict = {
     name: "Amy",
     age: 18
   }

   and we want to convert this to the object with populated object fields by key:value pairs from dict.
   For that we need to declare object view and describe there expected fields:

   class PersonView(BaseConfigView):
     name = None
     age = None

    Instead of None, we can assign another values, they would be used as default if  data dict will not contain
     such fields.  Now it's time for conversion:

    person = PersonView(serialized_obj=my_dict)



    As second way to initialize view, view fields could be directly passed as constructor arguments:

    person = PersonView(name=


  """

  def __init__(self, serialized_obj: str or dict or object or None = None, **kwargs):
    if len(kwargs) > 0:
      self._handle_initialization(kwargs)
    else:
      if isinstance(serialized_obj, str):
        serialized_obj = json.loads(serialized_obj)
      self._handle_deserialization(serialized_obj)

  def _handle_initialization(self, kwargs):
    props = dir(self)
    for item in kwargs:
      if item not in props:
        continue
      self.__setattr__(item, kwargs[item])

  def _handle_deserialization(self, serialized_obj=None):
    if serialized_obj is not None:
      if self.__class__ is serialized_obj.__class__:
        self.__dict__ = serialized_obj.__dict__
        self.__annotations__ = serialized_obj.__annotations__
      else:
        self.deserialize(serialized_obj)
        self.clean()

  def __isclass(self, obj):
    try:
      issubclass(obj, object)
    except TypeError:
      return False
    else:
      return True

  def __isjson(self, json_string):
    try:
      json.loads(json_string)
    except ValueError:
      return False
    return True

  def clean(self):
    """
    Replace not de-serialized types with none
    """
    for item in dir(self):
      attr = self.__getattribute__(item)
      if item[:2] != "__" and self.__isclass(attr) and issubclass(attr, SerializableObject):
        self.__setattr__(item, None)
      elif item[:2] != "__" and isinstance(attr, list) and len(attr) == 1 and \
        self.__isclass(attr[0]) and issubclass(attr[0], SerializableObject):
        self.__setattr__(item, [])

  def deserialize(self, d: dict):
    errors = []
    if isinstance(d, dict):
      for k, v in d.items():
        if isinstance(k, str):  # hack, change variable name from a.b.c to a_b_c
          # ToDo: add some kind of annotation to make such conversion smoother
          k = k\
            .replace(".", "_")\
            .replace("-", "_")\
            .replace(":", "_")

        if k not in self.__class__.__dict__:
          t = "object" if not v else v.__class__.__name__
          errors.append(f"{self.__class__.__name__} doesn't contain property {k}: {t} (sample:{v})")
          continue
        elif k not in self.__class__.__annotations__:
          errors.append(f"{self.__class__.__name__} doesn't contain type annotation in the definition {k}")
          continue

        attr_type = self.__class__.__annotations__[k]
        is_annotated = "_GenericAlias" in attr_type.__class__.__name__
        if is_annotated:
          name = attr_type.__dict__["_name"].lower()
          attr_args: List[type] = attr_type.__dict__["__args__"]
        else:
          name = attr_type.__class__.__name__
          attr_args: List[type] = [attr_type[0]] if name == list else [attr_type]

        attr_type_arg: Optional[type] = attr_args[0] if attr_args else None

        if name == "list" and attr_args and issubclass(attr_type_arg, SerializableObject):
          obj_list = []
          if isinstance(v, list) or isinstance(v, List):
            for vItem in v:
              obj_list.append(attr_type_arg(vItem))
          else:
            obj_list.append(attr_type_arg(v))
          self.__setattr__(k, obj_list)
        elif name == "list" and attr_args:
          _lst = []
          if isinstance(v, list) or isinstance(v, List):
            for vItem in v:
              _lst.append(attr_type_arg(vItem))
          else:
            _lst.append(attr_type_arg(v))
          self.__setattr__(k, _lst)
        elif name == "dict" and attr_args and len(attr_args) == 2 and isinstance(v, dict):
          dict_item = {}
          for _k, _v in v.items():
            if _v:
              _v = attr_args[1](_v)

            dict_item[_k] = _v
          self.__setattr__(k, dict_item)
        elif self.__isclass(attr_type_arg) and issubclass(attr_type_arg, SerializableObject):
          # we expecting here an dict to deserialize but empty string come
          v = v if isinstance(v, dict) or (isinstance(v, str) and self.__isjson(v)) else None
          self.__setattr__(k, attr_type_arg(v))
        else:
          # if parsed type is not same as expected, create dummy one
          if v is not None and not isinstance(v, attr_type_arg):
            v = attr_type_arg()
          self.__setattr__(k, v)

      if errors:
        raise ValueError("A number of errors happen:  \n" + "\n".join(errors))

  def serialize(self) -> dict:
    ret = {}

    # first of all we need to move defaults from class
    properties = dict(self.__class__.__dict__)
    properties.update(dict(self.__dict__))

    properties = {k: v for k, v in properties.items() if k[-1:] != "_"}

    for k, v in properties.items():
      if isinstance(v, (FunctionType, property)):
        continue

      if v is not None:
        if isinstance(v, list) and len(v) > 0:
          v_result = []
          for v_item in v:
            if issubclass(v_item.__class__, SerializableObject):
              v_result.append(v_item.serialize())
            elif self.__isclass(v_item) and issubclass(v_item, SerializableObject):
              v_result.append(v_item().serialize())
            else:
              v_result.append(v_item)
          ret[k] = v_result
        elif issubclass(v.__class__, SerializableObject):  # here we have instance of an class
          ret[k] = v.serialize()
        elif isinstance(v, dict):
          d_result = {}
          for _k, _v in v.items():
            if _v and issubclass(_v.__class__, SerializableObject):
              _v = _v.serialize()
            d_result[_k] = _v
          ret[k] = d_result
        elif self.__isclass(v) and issubclass(v, SerializableObject):  # here is an class itself
          ret[k] = v().serialize()
        else:
          ret[k] = v
    return ret
