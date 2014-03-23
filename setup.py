from setuptools import setup, find_packages
import os

setup(
  name='yamlicious',
  packages=find_packages(),
  scripts=[os.path.join('bin', p) for p in os.listdir('bin')],
  install_requires=[
    'pyyaml',
  ],
  test_suite='test',
)
