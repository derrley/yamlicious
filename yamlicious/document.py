import yaml


class TypeMismatch(Exception):
  pass


class CantMergeType(Exception):
  pass


def merge_dicts(l, r, safe=True):
  shared_keys = set(l.keys()) & set(r.keys())
  new_dict = {}

  for k in shared_keys:
    if not type(l[k]) == type(r[k]):
      raise TypeMismatch(k, type(l[k]), type(r[k]))

    if isinstance(l[k], list):
      new_dict[k] = l[k] + r[k]
    elif isinstance(l[k], dict):
      new_dict[k] = merge_dicts(l[k], r[k])
    else:
      if safe:
        raise CantMergeType(k, type(l[k]))
      else:
        new_dict[k] = r[k]

  for d in l, r:
    for k in set(d.keys()) - shared_keys:
      new_dict[k] = d[k]

  return new_dict


class Document(object):

  def __init__(self, env, document_dict=None):
    self.env = env
    self._dict = document_dict or {}

    self.substitute()

  @property
  def dict(self):
    return dict(self._dict)

  def substitute(self):
    """Run string substitution on the target document.

    You should run this function after changing the environment of this
    document in a way that could potentially resolve pending string
    substitutions.
    """
    self._dict = self.env.substitute(self._dict)

  def merge(self, document, safe=True):
    self.env.merge(document.env)
    self._dict = merge_dicts(self._dict, document._dict, safe)

    self.substitute()

    return self

  def evaluate_feature_keys(self, feature_keys):
    fk_dict = {key.name: key for key in feature_keys}

    def traverse_dict(d):
      if isinstance(d, dict):
        if len(d) == 1 and d.keys()[0] in fk_dict:
          key = d.keys()[0]
          doc = fk_dict[key].eval(self, traverse_dict(d[key]))
          self.env.merge(doc.env)
          return doc._dict
        else:
          return {k: traverse_dict(v) for k, v in d.items()}
      elif isinstance(d, list):
        return [traverse_dict(i) for i in d]
      else:
        return d

    # Handle functional keys.
    self._dict = traverse_dict(self._dict)

    # Handle document keys -- top level keys that disappear.
    delkeys = []
    for k, v in self._dict.items():
      if k in fk_dict:
        fk_dict[k].eval(self, v)
        delkeys.append(k)

    for k in delkeys:
      del self._dict[k]

  def __eq__(self, other):
    return (hasattr(other, '_dict') and hasattr(other, 'env') and
            other._dict == self._dict and other.env == self.env)
