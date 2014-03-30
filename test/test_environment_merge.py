import unittest

import yamlicious.environment


class MergeTest(unittest.TestCase):

  seed = {}

  left_keys = {}
  right_keys = {}

  merge_expected = {}

  merge_exception = False

  def setUp(self):
    def update(e, vals):
      for k, v in vals.items():
        e[k] = v

    self.left_env = yamlicious.environment.Environment(self.seed)
    update(self.left_env, self.left_keys)

    self.right_env = yamlicious.environment.Environment(self.seed)
    update(self.right_env, self.right_keys)

  def runTest(self):
    if not self.merge_exception:
      self.left_env.merge(self.right_env)
      self.assertEquals(self.merge_expected, self.left_env.dict())
    else:
      self.assertRaises(
        yamlicious.environment.MergeException,
        self.left_env.merge, 
        self.right_env
      )


class OneLeft(MergeTest):

  left_keys = {
    'key': '1'
  }

  merge_expected = {
    'key': '1'
  }


class OneRight(MergeTest):

  right_keys = {
    'key': '1'
  }

  merge_expected = {
    'key': '1'
  }


class NonSeedValueConflict(MergeTest):

  merge_exception = True

  left_keys = {
    'key': '1'
  }

  right_keys = {
    'key': '1'
  }


class NoConflict(MergeTest):

  left_keys = {
    'key': '1'
  }

  right_keys = {
    'other_key': '21'
  }

  merge_expected = {
    'key': '1',
    'other_key': '21',
  }


class NoConflictWithSeed(MergeTest):

  seed = {
    'seed_key': '1'
  } 

  left_keys = {
    'key': '1'
  }

  right_keys = {
    'other_key': '21'
  }

  merge_expected = {
    'key': '1',
    'other_key': '21',
    'seed_key': '1',
  }


class SubstitutionAfterMerge(MergeTest):

  seed = {
    'seed_list': '1,2,3',
    'seed_string': 'imaseed',
  } 

  left_keys = {
    'left_string': 'imaleft',
    'left_list': '4,5',
  }

  right_keys = {
    'right_string': 'imaright',
    'right_list': '6,7,8',
  }

  document = {
    'seed_list': '$(seed_list)',
    'seed_string': '$(seed_string)',
    'left_string': '$(left_string)',
    'left_list': '$(left_list)',
    'right_string': '$(right_string)',
    'right_list': '$(right_list)',
  }

  sub_expected = {
    'seed_list': ['1', '2', '3'],
    'seed_string': 'imaseed',
    'left_string': 'imaleft',
    'left_list': ['4', '5'],
    'right_string': 'imaright',
    'right_list': ['6', '7', '8'],
  }

  def runTest(self):
    self.left_env.merge(self.right_env)

    self.assertDictEqual(
      self.sub_expected, self.left_env.dict()
    )
