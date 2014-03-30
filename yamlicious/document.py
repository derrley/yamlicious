import pprint
import voluptuous


class TypeMismatch(Exception):
  pass


class CantMergeType(Exception):
  pass


class FeatureKeyEvaluationError(Exception):

  def __init__(self, doc, fk, val, path):
    s = 'In {0}, feature key at {1} failed validation:\n{2}\nvalidator: {3}'

    super(FeatureKeyEvaluationError, self).__init__(
      s.format(
        doc.name or 'unknown document',
        path or 'top of document',
        pprint.pformat({fk.name: val}),
        pprint.pformat({fk.name: fk.validator}),
      )
    )


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

  def __init__(self, env, document_dict=None, document_name=None):
    self.env = env
    self._dict = document_dict or {}
    self.name = document_name

    self.substitute()

  def dict(self):
    return dict(self._dict)

  def clone(self):
    return Document(self.env.clone(), self.dict())

  def make(self, document_dict):
    return Document(self.env.clone(), document_dict)

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

    def evaluate(key, val, path):
      fk = fk_dict[key]
      try:
        voluptuous.Schema(
          fk.validator if fk.validator is not None else object
        )(val)
        doc = fk.eval(self, val)

        if doc is not None:
          self.env.merge(doc.env)
          return doc.dict()

      except voluptuous.Invalid:
        raise FeatureKeyEvaluationError(self, fk, val, path)

    def traverse_dict(d, path):
      def path_plus(new_key):
        return path + '.' + new_key

      if isinstance(d, dict):
        if len(d) == 1 and list(d.keys())[0] in fk_dict:
          key = list(d.keys())[0]
          return evaluate(key, traverse_dict(d[key], path_plus(key)), path)
        else:
          return {k: traverse_dict(v, path_plus(k)) for k, v in d.items()}
      elif isinstance(d, list):
        return [
          traverse_dict(itm, path_plus(str(idx))) for idx, itm in enumerate(d)
        ]
      else:
        return d

    # Handle functional keys.
    self._dict = traverse_dict(self._dict, '')

    # Handle document keys -- top level keys that disappear.
    delkeys = []
    for k, v in self._dict.items():
      if k in fk_dict:
        evaluate(k, v, '')
        delkeys.append(k)

    for k in delkeys:
      del self._dict[k]

  def __eq__(self, other):
    return (hasattr(other, '_dict') and hasattr(other, 'env') and
            other._dict == self._dict and other.env == self.env)
