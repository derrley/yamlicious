import voluptuous

def merge_docs(docs, safe=True):
  doc = None
  for d in docs:
    if doc == None:
      doc = d
    else:
      doc.merge(d, safe)

  return doc


class LoaderBased(object):

  def __init__(self, loader):
    self.loader = loader


class Insert(LoaderBased):

  name = '_insert'
  validator = str

  def eval(self, doc, arg):
    return self.loader.load_file(arg)


class Merge(LoaderBased):

  name = '_merge'

  @property
  def validator(self):
    # Have to implement this as a property, otherwise python sees Any as a
    # bound method!
    return voluptuous.Any([dict], [list])

  def eval(self, doc, arg):
    return merge_docs(doc.make(a) for a in arg)


class MergeOverride(LoaderBased):

  name = '_merge_override'

  @property
  def validator(self):
    # Have to implement this as a property, otherwise python sees Any as a
    # bound method!
    return voluptuous.Any([dict], [list])

  def eval(self, doc, arg):
    return merge_docs((doc.make(a) for a in arg), safe=False)


class InsertMerge(LoaderBased):

  name = '_insert_merge'
  validator = [str]

  def eval(self, doc, arg):
    return merge_docs(self.loader.load_file(fp) for fp in arg)


class Include(LoaderBased):

  name = '_include'
  validator = [str]

  def eval(self, doc, arg):
    for d in (self.loader.load_file(fp) for fp in arg):
      doc.merge(d)
