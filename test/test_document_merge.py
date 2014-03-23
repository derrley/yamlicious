import unittest

import yamlicious.environment as ye
import yamlicious.document as yd


class MergeTest(unittest.TestCase):

  l = yd.Document(ye.Environment())
  r = yd.Document(ye.Environment())
  expect = yd.Document(ye.Environment())

  def runTest(self):
    self.assertEquals(
      self.expect,
      self.l.merge(self.r),
    )


class MergeWithEnvTest(MergeTest):
  """Tests that document merges include environment merge and substitution.

  This class tests that an envvar in a merged document is substituted into the
  parent document.
  """

  l = yd.Document(
    ye.Environment(),
    {'one': '$(THING)'},
  )

  r = yd.Document(
    ye.Environment({'THING': 'hi'}),
    {'two': 'hitwo'},
  )

  expect = yd.Document(
    ye.Environment({'THING': 'hi'}),
    {'one': 'hi',
      'two': 'hitwo'},
  )
