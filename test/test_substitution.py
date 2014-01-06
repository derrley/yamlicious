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

    operation = self.assertEquals
    if isinstance(self.expected, list):
      operation = self.assertItemsEqual

    operation(self.expected, env_under_test.substitute(self.document))
 

class SimpleString(SubTest):
  env = {
    'ONE': 'The first',
    'TWO': 'The second',
  }

  document = '{ONE} then {TWO}'
  expected = 'The first then The second'


class UnboundVariable(SubTest):
  document = '{UNBOUND}'
  expected = '{UNBOUND}'


class UnusedList(SubTest):
  env = {'SOMETHING': '1,2'}
  document = '{SOMETHING_ELSE}'
  expected = '{SOMETHING_ELSE}'


class ListAndString(SubTest):
  env = {
    'ONE': 'The first',
    'TWO': 'The second',
    'SOME_LIST': 'First list,Second list',
  }

  document = '{ONE} then {TWO} in {SOME_LIST}'
  expected = [
    'The first then The second in First list',
    'The first then The second in Second list',
  ]


class DotProduct(SubTest):
  env = {
    'BOYS': 'joey,johnny,bobby',
    'GIRLS': 'sally,mary',
  }

  document = '{BOYS} likes {GIRLS}'
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
    '{SOME_LIST}': 'List item'
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
    '{SOME_LIST}': '{_KEY} is in the list' 
  }

  expected = {
    'First': 'First is in the list',
    'Second': 'Second is in the list',
  }


class ListIntoList(SubTest):
  env = {
    'SOME_LIST': 'First,Second',
  }

  document = [
    'nonlist entry',
    '{SOME_LIST} entry', 
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
    '{SOME_LIST}': [
      'value',
      '{SOME_LIST} under {_KEY}',
    ]
  }

  expected = {
    'First': [
      'value',
      'Second under First',
      'First under First',
    ],

    'Second': [
      'value',
      'First under Second',
      'Second under Second',
    ],
  }
