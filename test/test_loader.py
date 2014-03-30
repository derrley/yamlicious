import unittest
import os

import yamlicious.loader

import test.util


class LoaderTest(test.util.TestCase):

  env = {}
  loader_args = {}
  default_doc = None
  doc = ''
  expect = None
  validator = None

  def runTest(self):
    def loader(content):
      return yamlicious.loader.Loader(
        openfunc=self.make_fakefile(
          loader_files = {'file': content}
        ),
        **self.loader_args
      )

    os.environ.update(self.env)

    default_doc = None
    if self.default_doc is not None:
      default_doc = loader(self.default_doc).load_file('file')
 
    self.assertSelfExpect(
      loader(self.doc).load_file,
      lambda x: x.obj(),
      'file', default_doc, self.validator or object,
    )


class EmptyDocWithDefault(LoaderTest):

  default_doc = """\
    one: hi
    two: hi again
  """

  doc = ''

  expect = {
    'one': 'hi',
    'two': 'hi again',
  }


class DocWithNoDefault(LoaderTest):

  doc = """\
    one: hi
    two: hi again
  """

  default_doc = ''

  expect = {
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

  expect = {
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

  expect = {
    'one': ['ONE', 'TWO']
  }


class ExcludeKeyNames(LoaderTest):

  loader_args = {'exclude_key_names': ['_env']}

  doc = """\
    _env:
      THING: hi
    $(THING): $(_KEY)
  """

  expect = {
    '_env': {
      'THING': 'hi'
    },
    #TODO: Is this really a good idea?
    '$(THING)': '$(THING)'
  }


class ExtraFeatureKeys(LoaderTest):

  class TestKey(object):
    name = '_test'
    validator = str

    def eval(self, doc, arg):
      return doc.make('yay!')

  loader_args = {'extra_feature_keys': [TestKey()]}

  doc = """\
    hello:
      _test: stuff
  """

  expect = {
    'hello': 'yay!'
  }


class ValidatorTest(LoaderTest):

  validator = {str: [str]}

  doc = """\
    one:
      - two
      - three
  """

  expect = {
    'one': ['two', 'three']
  }


class ValidatorTestFailure(LoaderTest):

  validator = {str: [str]}

  doc = """\
    one: two
  """

  expect = yamlicious.document.DocumentValidationError
