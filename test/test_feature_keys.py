import io
import contextlib
import unittest

import yamlicious.loader


def make_stringio(string):
  try:
    return io.StringIO(string)
  except TypeError:
    return io.StringIO(unicode(string))


def make_fakefile(loader_files):
  @contextlib.contextmanager
  def fakeopen(fname):
    yield make_stringio(loader_files[fname])

  return fakeopen


class TestInclude(unittest.TestCase):

  loader_files = {}
  doc = ''
  expect = {}

  def runTest(self):
    loader = yamlicious.loader.Loader(
      openfunc=make_fakefile(self.loader_files)
    )

    self.assertEquals(
      self.expect,
      loader.load_stream(make_stringio(self.doc)).dict
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
