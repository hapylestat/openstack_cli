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
from typing import List

from openstack_cli.modules.json2obj import SerializableObject


class Role(SerializableObject):
  id: str = None
  name: str = None


class UserDomain(SerializableObject):
  id: str = None
  name: str = None


class Endpoints(SerializableObject):
  region_id: str = None
  url: str = None
  region: str = None
  interface: str = None
  id: str = None


class EndpointCatalog(SerializableObject):
  type: str = None
  id: str = None
  name: str = None
  endpoints: List[Endpoints] = []


class User(SerializableObject):
  password_expires_at: str = None
  id: str = None
  name: str = None
  domain: UserDomain = None


class Token(SerializableObject):
  is_domain: bool = False
  methods: List[str] = []
  roles: List[Role] = []
  expires_at: str = None
  issued_at: str = None
  audit_ids: List[str] = []
  catalog: List[EndpointCatalog] = []
  user: User = None
  project: User = None


class LoginResponse(SerializableObject):
  token: Token = None
