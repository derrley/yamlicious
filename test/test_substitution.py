import unittest

import yamlicious.environment


class SubTest(unittest.TestCase):
  env = {}
  include = None
  exclude = None

  document = 'test string here'
  expected = 'test string here'

  def runTest(self):
    env_under_test = yamlicious.environment.Environment(
      self.env,
      self.include,
      self.exclude,
    )

    actual = env_under_test.substitute(self.document)
    if isinstance(self.expected, list):
      self.assertEquals(set(self.expected), set(actual))
    else:
      self.assertEquals(self.expected, actual)
 

class SimpleString(SubTest):
  env = {
    'ONE': 'The first',
    'TWO': 'The second',
  }

  document = '$(ONE) then $(TWO)'
  expected = 'The first then The second'


class UnboundVariable(SubTest):
  document = '$(UNBOUND)'
  expected = '$(UNBOUND)'


class UnusedList(SubTest):
  env = {'SOMETHING': '1,2'}
  document = '$(SOMETHING_ELSE)'
  expected = '$(SOMETHING_ELSE)'


class ListAndString(SubTest):
  env = {
    'ONE': 'The first',
    'TWO': 'The second',
    'SOME_LIST': 'First list,Second list',
  }

  document = '$(ONE) then $(TWO) in $(SOME_LIST)'
  expected = [
    'The first then The second in First list',
    'The first then The second in Second list',
  ]


class DotProduct(SubTest):
  env = {
    'BOYS': 'joey,johnny,bobby',
    'GIRLS': 'sally,mary',
  }

  document = '$(BOYS) likes $(GIRLS)'
  expected = [
    'joey likes sally', 
    'joey likes mary', 
    'johnny likes sally', 
    'johnny likes mary', 
    'bobby likes sally', 
    'bobby likes mary', 
  ]


class ListIntoDict(SubTest):
  env = {
    'SOME_LIST': 'First,Second',
  }

  document = {
    '$(SOME_LIST)': 'List item'
  }

  expected = {
    'First': 'List item',
    'Second': 'List item',
  }


class ListIntoDictWithSpecialKey(SubTest):
  env = {
    'SOME_LIST': 'First,Second',
  }

  document = {
    '$(SOME_LIST)': '$(_KEY) is in the list' 
  }

  expected = {
    'First': 'First is in the list',
    'Second': 'Second is in the list',
  }


class ListIntoDictWithNestedSpecialKey(SubTest):
  env = {
    'TOP_LIST': 'First,Second',
    'BOTTOM_LIST': 'Third,Fourth',
  }

  document = {
    '$(TOP_LIST)': {
      '$(BOTTOM_LIST)': '$(_KEY) on top and $(__KEY) on bottom'
    }
  }

  expected = {
    'First': {
      'Third': 'First on top and Third on bottom',
      'Fourth': 'First on top and Fourth on bottom',
    },

    'Second': {
      'Third': 'Second on top and Third on bottom',
      'Fourth': 'Second on top and Fourth on bottom',
    },
  }


class ListIntoDictWithNestedSpecialKeyThatSkipsLevel(SubTest):
  env = {
    'TOP_LIST': 'First,Second',
    'BOTTOM_LIST': 'Third,Fourth',
  }

  document = {
    '$(TOP_LIST)': {
      'skip': {
        '$(BOTTOM_LIST)': ['$(_KEY) on top $(__KEY) is skip and $(___KEY) on bottom',
                           'other string']
      }
    }
  }

  expected = {
    'First': {
      'skip': {
        'Third': ['First on top skip is skip and Third on bottom', 'other string'],
        'Fourth': ['First on top skip is skip and Fourth on bottom', 'other string'],
      }
    },

    'Second': {
      'skip': {
        'Third': ['Second on top skip is skip and Third on bottom', 'other string'],
        'Fourth': ['Second on top skip is skip and Fourth on bottom', 'other string'],
      }
    },
  }


class ListIntoList(SubTest):
  env = {
    'SOME_LIST': 'First,Second',
  }

  document = [
    'nonlist entry',
    '$(SOME_LIST) entry', 
  ]

  expected = [
    'nonlist entry',
    'First entry',
    'Second entry',
  ]


class NestedListDict(SubTest):
  env = {
    'SOME_LIST': 'First,Second',
    'SOME_NUMBER': '1',
  }

  document = {
    '$(SOME_LIST)': [
      'value',
      '$(SOME_LIST) under $(_KEY)',
    ]
  }

  expected = {
    'First': [
      'value',
      'First under First',
      'Second under First',
    ],

    'Second': [
      'value',
      'First under Second',
      'Second under Second',
    ],
  }


class TwoDictsInAList(SubTest):
  """A failing substitution case I discovered while writing FK tests.

  We weren't maintaining the special key depth as we traversed through a list!
  """
  env = {}

  document = {
    '_merge': [
      {'stuff': ['$(_KEY) and $(__KEY)']},
      {'_insert': '$(_KEY) and $(__KEY)'}
    ]
  }

  expected = {
    '_merge': [
      {'stuff': ['_merge and stuff']},
      {'_insert': '_merge and _insert'}
    ]
  }
