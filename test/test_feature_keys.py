import unittest

import yamlicious.loader

from test.util import make_stringio, make_fakefile


class TestInclude(unittest.TestCase):

  loader_files = {}
  doc = ''
  expect = None

  def runTest(self):
    loader = yamlicious.loader.Loader(
      openfunc=make_fakefile(self.loader_files)
    )

    if isinstance(self.expect, type) and issubclass(self.expect, Exception):
      self.assertRaises(
        self.expect,
        loader.load_stream,
        make_stringio(self.doc),
      )
    else:
      self.assertEquals(
        self.expect,
        loader.load_stream(make_stringio(self.doc)).obj()
      )


class SimpleInclude(TestInclude):
  loader_files = {
    'doc': """
      stuff:
        - is cool
    """
  }

  doc = """
    _include:
      - doc
    stuff:
      - is awesome
  """

  expect = {
    'stuff': [
      'is awesome',
      'is cool',
    ]
  }


class IncludeEnv(TestInclude):
  loader_files = {
    'doc': """
      _env:
        HI: stuff
      stuff:
        - is cool
    """
  }

  doc = """
    _include:
      - doc
    stuff:
      - is $(HI)
  """

  expect = {
    'stuff': [
      'is stuff',
      'is cool',
    ]
  }


class InsertAndMerge(TestInclude):
  loader_files = {
    'doc': """
      stuff:
        - is cool
    """
  }

  doc = """
    _merge:
      - stuff:
        - is awesome
      - _insert: doc
  """

  expect = {
    'stuff': [
      'is awesome',
      'is cool',
    ]
  }


class InsertAndMergeValidationFailure(TestInclude):
  loader_files = {
    'doc': """
      stuff:
        - is cool
    """
  }

  doc = """
    _merge:
      - stuff:
        - is awesome
      - _insert: [doc]
  """

  expect = yamlicious.document.FeatureKeyEvaluationError


class InsertAndMergeOverride(TestInclude):
  loader_files = {
    'doc': """
      stuff:
        is cool
    """
  }

  doc = """
    _merge_override:
      - stuff: is awesome
      - _insert: doc
  """

  expect = {
    'stuff': 'is cool',
  }


class InsertMerge(TestInclude):
  loader_files = {
    'doc1': """
      stuff:
        - is cool
    """,
    'doc2': """
      stuff:
        - is awesome
    """,
  }

  doc = """
    _insert_merge:
      - doc1
      - doc2
  """

  expect = {
    'stuff': [
      'is cool',
      'is awesome',
    ]
  }
