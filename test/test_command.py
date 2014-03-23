import io
import subprocess
import unittest
import yaml


class Command(unittest.TestCase):

  stdin = u''
  expected = {}

  def runTest(self):
    stdout = io.StringIO

    prc = subprocess.Popen(
      ['bin/yamlicious'],
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      env={
        'PYTHONPATH': '.'
      }
    )
    
    prc.stdin.write(self.stdin)
    prc.stdin.close()

    self.assertEquals(self.expected, yaml.load(prc.stdout.read()))


class CommandMerge(Command):

  stdin = u"""\
    _merge:
      - stuff:
        - is awesome
      - stuff:
        - is cool
  """

  expected = {
    'stuff': [
      'is awesome',
      'is cool',
    ]
  }
