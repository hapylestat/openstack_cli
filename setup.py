#!/usr/bin/env python3

import codecs
import os
import re

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
  # auto-detects file encoding
  with codecs.open(os.path.join(here, *parts), 'r') as fp:
    return fp.read()


def find_version(*file_paths):
  version_file = read(*file_paths)
  version_match = re.search(
    r"^__version__ = ['\"]([^'\"]*)['\"]",
    version_file,
    re.M,
  )
  if version_match:
    return version_match.group(1)

  raise RuntimeError("Unable to find version string.")


def load_requirements():
  data = read("requirements.txt")
  return data.split("\n")


setup(
  name="openstack-cli",
  version=find_version("src", "openstack_cli", "__init__.py"),
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
