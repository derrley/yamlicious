import copy
import itertools
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


class DocumentValidationError(Exception):
  pass


def merge_objs(l, r, safe=True):
  if l is None:
    return r

  if r is None:
    return l

  if not type(l) == type(r):
    raise TypeMismatch(l, r)

  if isinstance(l, list):
    return l + r

  if isinstance(l, dict):
    l_keys = set(l.keys())
    r_keys = set(r.keys())
    shared_keys = l_keys & r_keys
    l_only_keys = l_keys - shared_keys
    r_only_keys = r_keys - shared_keys

    return dict(
      itertools.chain(
        ((k, merge_objs(l[k], r[k], safe)) for k in shared_keys),
        ((k, l[k]) for k in l_only_keys),
        ((k, r[k]) for k in r_only_keys),
      )
    )

  if l == r:
    return l

  if safe:
    raise CantMergeType(l, r)

  return r


class Document(object):

  def __init__(self, env, document_obj=None, document_name=None):
    self.env = env
    self._obj = document_obj
    self.name = document_name

    self.substitute()

  def obj(self):
    return copy.deepcopy(self._obj)

  def clone(self):
    return Document(self.env.clone(), self.obj())

  def make(self, document_obj):
    return Document(self.env.clone(), document_obj)

  def substitute(self):
    """Run string substitution on the target document.

    You should run this function after changing the environment of this
    document in a way that could potentially resolve pending string
    substitutions.
    """
    self._obj = self.env.substitute(self._obj)

  def merge(self, document, safe=True):
    self.env.merge(document.env)
    self._obj = merge_objs(self._obj, document._obj, safe)

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
          return doc.obj()

      except voluptuous.Invalid:
        raise FeatureKeyEvaluationError(self, fk, val, path)

    def traverse(d, path):
      def path_plus(new_key):
        return path + '.' + new_key

      if isinstance(d, dict):
        if len(d) == 1 and list(d.keys())[0] in fk_dict:
          key = list(d.keys())[0]
          return evaluate(key, traverse(d[key], path_plus(key)), path)
        else:
          return {k: traverse(v, path_plus(k)) for k, v in d.items()}
      elif isinstance(d, list):
        return [
          traverse(itm, path_plus(str(idx))) for idx, itm in enumerate(d)
        ]
      else:
        return d

    # Handle functional keys.
    self._obj = traverse(self._obj, '')

    # Handle document keys -- top level keys that disappear.
    if isinstance(self._obj, dict):
      delkeys = []
      for k, v in self._obj.items():
        if k in fk_dict:
          evaluate(k, v, '')
          delkeys.append(k)

      for k in delkeys:
        del self._obj[k]

  def validate(self, validator):
    try:
      voluptuous.Schema(validator)(self._obj)
    except voluptuous.Invalid as e:
      raise DocumentValidationError(e)

  def __eq__(self, other):
    return (hasattr(other, '_obj') and hasattr(other, 'env') and
            other._obj == self._obj and other.env == self.env)
