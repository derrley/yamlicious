import collections
import re


class MergeException(Exception):
  pass


class Environment(object):
  
  def __init__(self, environment, include_envvars=None, exclude_envvars=None,
               list_delimiter=None):
    """
    :Paramters:
      `environment`:
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
    self._env = {}

    for k, v in environment.iteritems():
      if ((include_envvars is not None and k in include_envvars) or 
          (exclude_envvars is not None and k not in exclude_envvars) or
          (include_envvars is None and exclude_envvars is None)): 
        self[k] = v

    self._seed_keys = set(environment.keys())

  @property
  def non_seed_keys(self):
    """A set of keys in the environment that were added after creation."""
    return set(self._env) - self._seed_keys

  def __setitem__(self, k, v):
    """Set a variable in the environment.

    NOTE: This function only has an effect if the seed environment did not
          already define k. The seed (actual) environment supercedes the
          document's environment.
    """
    if k not in self._seed_keys:
      if self._list_delimiter in v:
        self._env[k] = v.split(self._list_delimiter)
        self._list_keys.add(k)
      else:
        self._env[k] = v
        self._string_keys.add(k)

  def __delitem__(self, k):
    if k not in self._seed_keys:
      del self._env[k]
      self._string_keys.discard(k)
      self._list_keys.discard(k)

  def __getitem__(self, k):
    return self._env[k]

  def __iter__(self):
    return iter(self._env)

  def dictcopy(self):
    return dict(self._env)

  def iteritems(self):
    return self._env.iteritems()

  def merge(self, other):
    """Merge another environment with this one."""
    both = other.non_seed_keys.intersection(self.non_seed_keys)
    if both:
      raise MergeException(
        'Both environments define nonseed keys {0}'.format(both)
      )

    for k in other.non_seed_keys:
      self[k] = other[k]

    return self

  def substitute(self, document, key_nest_level=1):
    """Perform string substitution on the given document"""
    
    # Perform substitution of a given subset of environment variables on a
    # given string
    def sub_str(s, env):
      ret = s
      for k, v in env.iteritems():
        ret = ret.replace('$({0})'.format(k), v)

      return ret
  
    # Perform substitution on the given string
    def sub(s):
      ret = set([sub_str(s, {k: self._env[k] for k in self._string_keys})])

      # Brute force approach. Run the string format operation for every value
      # of every variable. Runs on order of the number of variables in the
      # environment, rather than the number of variable substitutions in the
      # string. This is going to be slow as hell, but it might not matter, and
      # I can optimize it later. 
      for var in self._list_keys:
        for smbr in list(ret):
          start_size = len(ret)
          ret.update(set(
             sub_str(smbr, {var: v}) for v in self._env[var]
          ))

          if start_size != len(ret):
            ret.discard(smbr)

      return list(ret)

    if isinstance(document, basestring):
      ret = sub(document)
      return ret if len(ret) != 1 else ret[0]

    elif isinstance(document, collections.Mapping):
      ret = {}
      for k, v in document.iteritems():
        for subk in sub(k):
          special = '_' * key_nest_level + 'KEY'
          self[special] = subk
          ret[subk] = self.substitute(v, key_nest_level + 1)

        del self[special]
      return ret

    elif isinstance(document, collections.Iterable):
      ret = []
      for v in document:
        if isinstance(v, basestring):
          ret += sub(v)
        else:
          ret.append(self.substitute(v, key_nest_level))

      return ret
