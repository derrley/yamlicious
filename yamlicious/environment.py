import re


class MergeException(Exception):
  pass


class Environment(object):
  
  def __init__(self, environment_dict=None, include_envvars=None, exclude_envvars=None,
               list_delimiter=None):
    """
    :Paramters:
      `environment_dict`:
        Dictionary representing the environment to load from. Pass os.environ
        here if you'd like to load the *real* environment.

      `include_envvars`
        Allow an environment variable to override *these keys only*. Any other
        key in the environment is ignored. Setting this has no impact on the
        interpretation of variables declared in the doucment using ``_env``.

      `exclude_envvars`
        Ignore these variables when they're set in the environment. Setting
        this has no impact on the interpretation of variables declared in the
        doucment using ``_env``.
    """
    self._list_delimiter = list_delimiter or ','

    if include_envvars is not None and exclude_envvars is not None:
      raise Exception('You can only include or exclude keys, not both.')

    self._string_keys = set()
    self._list_keys = set()
    self._seed_keys = set()
    self._dict = {}

    environment_dict = environment_dict or {}
    for k, v in environment_dict.items():
      if ((include_envvars is not None and k in include_envvars) or 
          (exclude_envvars is not None and k not in exclude_envvars) or
          (include_envvars is None and exclude_envvars is None)): 
        self[k] = v

    self._seed_keys = set(environment_dict.keys())

  def clone(self):
    r = Environment()

    r._string_keys = set(self._string_keys)
    r._list_keys = set(self._list_keys)
    r._seed_keys = set(self._seed_keys)
    r._dict = dict(self._dict)

    return r

  @property
  def non_seed_keys(self):
    """A set of keys in the environment that were added after creation."""
    return set(self._dict) - self._seed_keys

  def dict(self):
    return dict(self._dict)

  def __eq__(self, other):
    return hasattr(other, '_dict') and self._dict == other._dict

  def __setitem__(self, k, v):
    """Set a variable in the environment.

    NOTE: This function only has an effect if the seed environment did not
          already define k. The seed (actual) environment supercedes subsequent
          mutation.
    """
    if k not in self._seed_keys:
      if self._list_delimiter in v:
        self._dict[k] = v.split(self._list_delimiter)
        self._list_keys.add(k)
      else:
        self._dict[k] = v
        self._string_keys.add(k)

  def __delitem__(self, k):
    if k not in self._seed_keys:
      del self._dict[k]
      self._string_keys.discard(k)
      self._list_keys.discard(k)

  def __getitem__(self, k):
    return self._dict[k]

  def __iter__(self):
    return iter(self._dict)

  def items(self):
    return self._dict.items()

  def merge(self, other):
    """Merge another environment with this one."""
    both = other.non_seed_keys.intersection(self.non_seed_keys)
    if both:
      raise MergeException(
        'Both environments define nonseed keys {0}'.format(both)
      )

    for k in other:
      self[k] = other[k]

    return self

  def substitute(self, document, key_nest_level=1):
    """Perform string substitution on the given document"""
    
    # Perform string-variable substitution.
    def sub_str(s, env):
      ret = s
      for k, v in env.items():
        ret = ret.replace('$({0})'.format(k), v)

      return ret
  
    # Perform substitution on the given string
    def sub(s):
      ret = [sub_str(s, {k: self._dict[k] for k in self._string_keys})]

      # Brute force approach. Run the string format operation for every value
      # of every variable. Runs on order of the number of variables in the
      # environment, rather than the number of variable substitutions in the
      # string. This is going to be slow as hell, but it might not matter, and
      # I can optimize it later. 
      for var in self._list_keys:
        replace_with = []
        for i, smbr in enumerate(ret):
          lst_repl = [sub_str(smbr, {var: v}) for v in self._dict[var]]

          if any([elt != smbr for elt in lst_repl]):
            replace_with.append((i, lst_repl))

        offset = 0
        for i, replace_list in replace_with:
          del ret[i+offset]

          for item in reversed(replace_list):
            ret.insert(i+offset, item)

          offset += len(replace_list) - 1

      return ret

    if document == None:
      return document

    if isinstance(document, dict):
      ret = {}
      for k, v in document.items():
        for subk in sub(k):
          special = '_' * key_nest_level + 'KEY'
          self[special] = subk
          ret[subk] = self.substitute(v, key_nest_level + 1)

        del self[special]
      return ret

    if isinstance(document, list):
      ret = []
      for v in document:
        if isinstance(v, dict) or isinstance(v, list):
          ret.append(self.substitute(v, key_nest_level))
        else:
          ret += sub(v)

      return ret

    ret = sub(document)
    return ret if len(ret) != 1 else ret[0]
