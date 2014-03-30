from setuptools import setup

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
    'voluptuous',
  ],
  test_suite='test',
)
