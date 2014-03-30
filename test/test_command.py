import glob
import io
import subprocess
import unittest
import yaml


class Command(unittest.TestCase):

  stdin = ''
  expected = None

  def runTest(self):
    stdout = io.StringIO

    prc = subprocess.Popen(
      ['yamlicious'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    )
    
    try:
      prc.stdin.write(self.stdin)
    except TypeError:
      prc.stdin.write(bytes(self.stdin, 'UTF-8'))

    prc.stdin.close()

    self.assertEquals(self.expected, yaml.load(prc.stdout.read()))


class CommandMerge(Command):

  stdin = """\
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
