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

from openstack_cli.modules.config import Configuration
from openstack_cli.modules.discovery import CommandMetaInfo
from openstack_cli.modules.openstack.objects import LoginResponse

__module__ = CommandMetaInfo("test")

j = """
{
    "token": {
        "audit_ids": [
            "0VA0g6A_Q6e1waGvZrX-Qg"
        ],
        "catalog": [
            {
                "endpoints": [
                    {
                        "id": "27bb485063454f56851a2a8525de8cbf",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:9001"
                    },
                    {
                        "id": "475aef55f6bd459698e1e9919a235253",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:9001"
                    },
                    {
                        "id": "7ed32cf8ac914b3a856eb356f40ea7c2",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:9001"
                    }
                ],
                "id": "4ad73b33a21c403da4e4465b8c587837",
                "name": "designate",
                "type": "dns"
            },
            {
                "endpoints": [
                    {
                        "id": "22f6a984fe1746efb14143b122d22029",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:5000"
                    },
                    {
                        "id": "5c2640b91d6248ac86098a98dfa470d6",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:5000"
                    },
                    {
                        "id": "63e6bf0912094917b7b0cade36630598",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:5000"
                    }
                ],
                "id": "4d3e336ea2b64cdfb3fa9e2e391679dd",
                "name": "keystone",
                "type": "identity"
            },
            {
                "endpoints": [
                    {
                        "id": "7f0df2b646c4425b8bd0d5e1988a5543",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8780"
                    },
                    {
                        "id": "e588a53f654c4d3091e7ebf772891614",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8780"
                    },
                    {
                        "id": "f25fbe6fe15f46bf90d5befa457d3d57",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:8780"
                    }
                ],
                "id": "51a429694db94560a32afb836971f684",
                "name": "placement",
                "type": "placement"
            },
            {
                "endpoints": [
                    {
                        "id": "0fd7999a50ba4e8796185343a2c66299",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:9696"
                    },
                    {
                        "id": "5a7ea895bc134b418afbccfa37f0655b",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:9696"
                    },
                    {
                        "id": "d73b03526b924c3398b7ced7149d1f4a",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:9696"
                    }
                ],
                "id": "62279d130c654f6d8d192bbcc1ef0632",
                "name": "neutron",
                "type": "network"
            },
            {
                "endpoints": [
                    {
                        "id": "3a88692dd8fd441881158d99445774f7",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8776/v2/f208f9e1ba374e5a9759f653cc63dcf7"
                    },
                    {
                        "id": "736f62f1cb3a442dadf61216c6312077",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:8776/v2/f208f9e1ba374e5a9759f653cc63dcf7"
                    },
                    {
                        "id": "d72e227284d544dc9a23aa040f79f66e",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8776/v2/f208f9e1ba374e5a9759f653cc63dcf7"
                    }
                ],
                "id": "7890e089339f42d79ea51266366e7934",
                "name": "cinderv2",
                "type": "volumev2"
            },
            {
                "endpoints": [
                    {
                        "id": "a5deb78328e44c6382fe5f77e402124f",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:8004/v1/f208f9e1ba374e5a9759f653cc63dcf7"
                    },
                    {
                        "id": "c23b6245055e40babddd470e75440f59",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8004/v1/f208f9e1ba374e5a9759f653cc63dcf7"
                    },
                    {
                        "id": "c2bfff5a1af549a392f90bbf259792be",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8004/v1/f208f9e1ba374e5a9759f653cc63dcf7"
                    }
                ],
                "id": "94a8a2ec17e945f6bb1b2c5ae87af1ba",
                "name": "heat",
                "type": "orchestration"
            },
            {
                "endpoints": [
                    {
                        "id": "b9c2f1e47335416593118296e958b009",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:8776/v3/f208f9e1ba374e5a9759f653cc63dcf7"
                    },
                    {
                        "id": "ded387cbacd64edc8f02e183f4af4e2c",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8776/v3/f208f9e1ba374e5a9759f653cc63dcf7"
                    },
                    {
                        "id": "fa33ab9ee7474f0d96010f5528102817",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8776/v3/f208f9e1ba374e5a9759f653cc63dcf7"
                    }
                ],
                "id": "b8ec9813d7154c11b9ba8451fab7676a",
                "name": "cinderv3",
                "type": "volumev3"
            },
            {
                "endpoints": [
                    {
                        "id": "1ad2ebd023dd404a943b5910c0f918e0",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:9292"
                    },
                    {
                        "id": "3d20077349d84b8cab0f37a572f48291",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:9292"
                    },
                    {
                        "id": "ae17281833b0491999a5300cd51b1370",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:9292"
                    }
                ],
                "id": "cd65a5f3c7394eb99b763eed0e0194a0",
                "name": "glance",
                "type": "image"
            },
            {
                "endpoints": [
                    {
                        "id": "7c684623ffd44108b4513836fc4d7296",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8774/v2.1"
                    },
                    {
                        "id": "ca2c07ab5af0427cbf3e9de4446e947d",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:8774/v2.1"
                    },
                    {
                        "id": "ddb1bcabaa0b4cc6a7fc791631708731",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8774/v2.1"
                    }
                ],
                "id": "e7f82c6cfdf54d9cb719d74fb33169e9",
                "name": "nova",
                "type": "compute"
            },
            {
                "endpoints": [
                    {
                        "id": "2f842dfd507849e1b5c07c98a5c30a82",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8000/v1"
                    },
                    {
                        "id": "74b6b7bc7fb64863b8168f2d67c05f44",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:8000/v1"
                    },
                    {
                        "id": "b704b969da71492a8661088b70fb1ec9",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:8000/v1"
                    }
                ],
                "id": "ead9ad8c32564696b48d09fddddd4b46",
                "name": "heat-cfn",
                "type": "cloudformation"
            },
            {
                "endpoints": [
                    {
                        "id": "11c668ef8095470ab3ed732d1242c64e",
                        "interface": "admin",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:9876"
                    },
                    {
                        "id": "2bb14879e09547aa84cb6646f6e7330e",
                        "interface": "public",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "https://api-os.eng.hortonworks.com:9876"
                    },
                    {
                        "id": "2fab5d5c18d74e96b9a8e8bb8b042cf9",
                        "interface": "internal",
                        "region": "RegionOne",
                        "region_id": "RegionOne",
                        "url": "http://os.eng.hortonworks.com:9876"
                    }
                ],
                "id": "ecc43117acf24511af35ad76fecc34a5",
                "name": "octavia",
                "type": "load-balancer"
            }
        ],
        "expires_at": "2020-04-15T07:39:53.000000Z",
        "is_domain": false,
        "issued_at": "2020-04-14T19:39:53.000000Z",
        "methods": [
            "password"
        ],
        "project": {
            "domain": {
                "id": "default",
                "name": "Default"
            },
            "id": "f208f9e1ba374e5a9759f653cc63dcf7",
            "name": "ambari"
        },
        "roles": [
            {
                "id": "9fe2ff9ee4384b1894a90878d3e92bab",
                "name": "_member_"
            }
        ],
        "user": {
            "domain": {
                "id": "default",
                "name": "Default"
            },
            "id": "6c6ef3e941ba4e4c9f3fffe6e2ca17d7",
            "name": "dgrinenko",
            "password_expires_at": null
        }
    }
}
"""


def __init__(conf: Configuration):
  t = LoginResponse(serialized_obj=j)
  print(t.token.user.id)
