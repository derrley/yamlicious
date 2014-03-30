import io
import contextlib

import unittest


class TestCase(unittest.TestCase):

  def make_stringio(self, string):
    try:
      return io.StringIO(string)
    except TypeError:
      return io.StringIO(unicode(string))

  def make_fakefile(self, loader_files):
    @contextlib.contextmanager
    def fakeopen(fname):
      yield self.make_stringio(loader_files[fname])

    return fakeopen

  def assertSelfExpect(self, func, chain, *args):
    if isinstance(self.expect, type) and issubclass(self.expect, Exception):
      self.assertRaises(self.expect, func, *args)
    else:
      self.assertEquals(self.expect, chain(func(*args)))
