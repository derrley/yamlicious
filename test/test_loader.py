import unittest

import yamlicious.loader

import test.util


class LoaderTest(unittest.TestCase):

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
