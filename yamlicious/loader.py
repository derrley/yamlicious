import os
import yaml

import yamlicious.document
import yamlicious.environment

import yamlicious.feature_keys.env
import yamlicious.feature_keys.merge


class Loader(object):

  def __init__(self,
               include_envvars=None,
               exclude_envvars=None,
               list_delimiter=None,
               exclude_key_names=None,
               extra_feature_keys=None,
               openfunc=None):
    self.include_envvars = include_envvars
    self.exclude_envvars = exclude_envvars
    self.list_delimiter = list_delimiter
    self.openfunc = openfunc or open

    #TODO: Hm. Perhaps a wiring context would serve better?
    keys = [
      yamlicious.feature_keys.env.Env(),
      yamlicious.feature_keys.merge.Include(self),
      yamlicious.feature_keys.merge.Insert(self),
      yamlicious.feature_keys.merge.MergeOverride(self),
      yamlicious.feature_keys.merge.InsertMerge(self),
      yamlicious.feature_keys.merge.Merge(self),
    ] + (extra_feature_keys or [])

    self.keys = [k for k in keys if k.name not in (exclude_key_names or [])]

  def new_env(self):
    return yamlicious.environment.Environment(
      os.environ, self.include_envvars, self.exclude_envvars,
      self.list_delimiter
    )

  def load_file(self, doc_path, default_doc=None, validator=None):
    with self.openfunc(doc_path) as f:
      return self.load_stream(f, default_doc, doc_path, validator)

  def load_stream(self, doc_stream, default_doc=None, doc_name=None,
                  validator=None):
    return self.load_string(
      doc_stream.read(), default_doc, doc_name or str(doc_stream), validator
    )

  def load_string(self, doc_string, default_doc=None, doc_name=None,
                  validator=None):
    return self.load_obj(
      yaml.load(doc_string), default_doc, doc_name, validator
    )

  def load_obj(self, doc_obj, default_doc=None, doc_name=None, validator=None):
    doc = yamlicious.document.Document(self.new_env(), doc_obj, doc_name)

    if default_doc is not None:
      doc = default_doc.merge(doc, safe=False)

    doc.evaluate_feature_keys(self.keys)

    if validator is not None:
      doc.validate(validator)

    return doc
