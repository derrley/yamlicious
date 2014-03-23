import yamlicious.loader

# A couple of commonly found functions in JSON/YAML libraries.

def load(fname):
  return yamlicious.loader.Loader().load_file(fname)


def loads(yamldoc):
  return yamlicious.loader.Loader().load_string(yamldoc)
