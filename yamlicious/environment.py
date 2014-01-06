import collections
import re


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
    list_delimiter = list_delimiter or ','
    if include_envvars is not None and exclude_envvars is not None:
      raise Exception('You can only include or exclude keys, not both.')

    self._string_vars = {}
    self._list_vars = {}

    for k, v in environment.iteritems():
      if ((include_envvars is not None and k in include_envvars) or 
          (exclude_envvars is not None and k not in exclude_envvars) or
          (include_envvars is None and exclude_envvars is None)): 
        if list_delimiter in v:
          self._list_vars[k] = v.split(list_delimiter)
        else:
          self._string_vars[k] = v

  @property
  def non_envvar_keys(self):
    return set([
      k for k in self._string_vars.keys() + self._list_vars.keys()
      if k not in environment
    ])

  def merge(self, other):
    """Merge another environment with this one."""
    if other.non_envvar_keys.intersection(self.non_envvar_keys):
      raise Exception(
        'Environments cannot merge because ecah defines key {0}'.format(k)
      )

    def merge(l, r):
      return {
        k: r.get(k) if r.get(k) is not None else l.get(k)    
        for k in set(l.keys() + r.keys())
      }

    self._list_vars = merge(self._list_vars, other._list_vars)
    self._string_vars = merge(self._string_vars, other._string_vars)

  def substitute(self, document):
    """Perform string substitution on the given document"""
    
    # Perform substitution of a given subset of environment variables on a
    # given string
    def sub_str(s, env):
      ret = s
      for k, v in env.iteritems():
        ret = ret.replace('{' + k + '}', v)

      return ret
  
    # Perform substitution on the given string
    def sub(s):
      ret = set([sub_str(s, self._string_vars)])

      # Brute force approach. Run the string format operation for every value
      # of every variable. Runs on order of the number of variables in the
      # environment, rather than the number of variable substitutions in the
      # string. This is going to be slow as hell, but it might not matter, and
      # I can optimize it later. 
      for var, list_of_vals in self._list_vars.iteritems():
        for smbr in list(ret):
          start_size = len(ret)
          ret.update(set(
             sub_str(smbr, {var: v}) for v in list_of_vals
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
          self._string_vars['_KEY'] = subk
          ret[subk] = self.substitute(v)
        del self._string_vars['_KEY']
      return ret

    elif isinstance(document, collections.Iterable):
      ret = []
      for v in document:
        if isinstance(v, basestring):
          ret += sub(v)
        else:
          ret.append(self.substitute(v))

      return ret
