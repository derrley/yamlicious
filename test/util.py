import io
import contextlib


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

