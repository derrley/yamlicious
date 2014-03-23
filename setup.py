from setuptools import setup, find_packages
import os

setup(
  name='yamlicious',
  packages=[
    'yamlicious',
    'yamlicious/feature_keys',
  ],
  scripts=[
    'bin/yamlicious'
  ],
  install_requires=[
    'pyyaml',
  ],
  test_suite='test',
)
