import unittest
import os

import yamlicious.loader

import test.util


class LoaderTest(unittest.TestCase):

  env = {}
  loader_args = {}
  default_doc = None
  doc = ''
  expected_doc_dict = {}

  def runTest(self):
    def loader(content):
      return yamlicious.loader.Loader(
        openfunc=test.util.make_fakefile(
          loader_files = {'file': content}
        ),
        **self.loader_args
      )

    os.environ.update(self.env)

    default_doc = None
    if self.default_doc is not None:
      default_doc = loader(self.default_doc).load_file('file')

    self.assertEquals(
      self.expected_doc_dict,
      loader(self.doc).load_file('file', default_doc).dict(),
    )


class EmptyDocWithDefault(LoaderTest):

  default_doc = """\
    one: hi
    two: hi again
  """

  doc = ''

  expected_doc_dict = {
    'one': 'hi',
    'two': 'hi again',
  }


class DocWithNoDefault(LoaderTest):

  doc = """\
    one: hi
    two: hi again
  """

  default_doc = ''

  expected_doc_dict = {
    'one': 'hi',
    'two': 'hi again',
  }


class DocumentIsUnsafeMerge(LoaderTest):

  doc = """\
    one: hi
    two: hi again
  """

  default_doc = """\
    one: should be replaced
    three: should survive
  """

  expected_doc_dict = {
    'one': 'hi',
    'two': 'hi again',
    'three': 'should survive',
  }


class ListDelimiterTest(LoaderTest):

  loader_args = {'list_delimiter': ':'}

  env = {'THING': 'ONE:TWO'}

  doc = """\
    one: $(THING)
  """

  expected_doc_dict = {
    'one': ['ONE', 'TWO']
  }


class ExcludeKeyNames(LoaderTest):

  loader_args = {'exclude_key_names': ['_env']}

  doc = """\
    _env:
      THING: hi
    $(THING): $(_KEY)
  """

  expected_doc_dict = {
    '_env': {
      'THING': 'hi'
    },
    #TODO: Is this really a good idea?
    '$(THING)': '$(THING)'
  }


class ExtraFeatureKeys(LoaderTest):

  class TestKey(object):
    name = '_test'
    validator = None

    def eval(self, doc, arg):
      return doc.make({'yay!': ''})

  loader_args = {'extra_feature_keys': [TestKey()]}

  doc = """\
    hello:
      _test: stuff
  """

  expected_doc_dict = {
    'hello': {'yay!': ''}
  }
