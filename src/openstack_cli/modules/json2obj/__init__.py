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
    if isinstance(d, dict):
      for k, v in d.items():
        if k not in self.__class__.__dict__:
          raise RuntimeError(self.__class__.__name__ + " doesn't contain property " + k)
        attr_type = self.__class__.__dict__[k]
        if isinstance(attr_type, list) and len(attr_type) > 0 and issubclass(attr_type[0], SerializableObject):
          obj_list = []
          if isinstance(v, list):
            for vItem in v:
              obj_list.append(attr_type[0](vItem))
          else:
            obj_list.append(attr_type[0](v))
          self.__setattr__(k, obj_list)
        elif self.__isclass(attr_type) and issubclass(attr_type, SerializableObject):
          self.__setattr__(k, attr_type(v))
        else:
          self.__setattr__(k, v)

  def serialize(self) -> dict:
    ret = {}

    # first of all we need to move defaults from class
    properties = dict(self.__class__.__dict__)
    properties.update(dict(self.__dict__))

    properties = {k: v for k, v in properties.items() if k[:1] != "_"}

    for k, v in properties.items():
      if v is not None:
        if isinstance(v, list) and len(v) > 0:
          v_result = []
          for v_item in v:
            if issubclass(v_item.__class__, SerializableObject):
              v_result.append(v_item.serialize())
            elif issubclass(v_item, SerializableObject):
              v_result.append(v_item().serialize())
            else:
              v_result.append(v_item)
          ret[k] = v_result
        elif issubclass(v.__class__, SerializableObject):  # here we have instance of an class
          ret[k] = v.serialize()
        elif self.__isclass(v) and issubclass(v, SerializableObject):  # here is an class itself
          ret[k] = v().serialize()
        else:
          ret[k] = v

    return ret
