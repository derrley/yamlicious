import unittest
import yamlicious.document


class MergeTest(unittest.TestCase):

  l = {}
  r = {}
  expect = {}
  safe = True

  def runTest(self):
    if isinstance(self.expect, type) and issubclass(self.expect, Exception):
      self.assertRaises(
        self.expect, yamlicious.document.merge_objs, self.l, self.r, self.safe
      )
    else:
      self.assertEquals(
        self.expect, yamlicious.document.merge_objs(self.l, self.r, self.safe)
      )


class Disjoint(MergeTest):

  l = {'one': 1}
  r = {'two': 2}
  expect = {'one': 1, 'two': 2}


class OverlapFail(MergeTest):

  l = {'one': 'one'}
  r = {'one': 'two'}
  expect = yamlicious.document.CantMergeType


class OverlapFailUnsafe(MergeTest):

  l = {'one': 1}
  r = {'one': 2}
  safe = False
  expect = {'one': 2}


class TypeMismatch(MergeTest):

  l = {'one': 1}
  r = {'one': 'hi'}
  expect = yamlicious.document.TypeMismatch

class OverlapList(MergeTest):

  l = {
    'one': [1, 2],
  }

  r = {
    'one': [3, 4]
  }

  expect = {
    'one': [1, 2, 3, 4]
  }


class NestedOverlapList(MergeTest):

  l = {
    'one': {
      'one': [1, 2],
    }
  }

  r = {
    'one': {
      'one': [3, 4],
    }
  }

  expect = {
    'one': {
      'one': [1, 2, 3, 4],
    }
  }


class NestedOverlapDisjoint(MergeTest):

  l = {
    'one': {
      'one': 1
    }
  }

  r = {
    'one': {
      'two': 2
    }
  }

  expect = {
    'one': {
      'one': 1,
      'two': 2,
    }
  }


class Lists(MergeTest):

  l = [1, 2]

  r = [3, 4]

  expect = [1, 2, 3, 4]


class Matching(MergeTest):

  l = 1
  r = 1
  expect = 1


class NonMatching(MergeTest):

  l = 1
  r = 2
  expect = yamlicious.document.CantMergeType
