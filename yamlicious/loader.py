import os
import yaml

import yamlicious.environment

class Loader(object):

  def __init__(self,
               include_envvars=None,
               exclude_envvars=None,
               list_delimiter=None):

    self.env = yamlicious.environment.Environment(
      os.environ, include_envvars, exclude_envvars, list_delimiter
    )

  def load(self, f):
    return self.env.substitute(yaml.load(f.read()))
