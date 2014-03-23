import yamlicious.document as yd


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

  def eval(self, doc, arg):
    return self.loader.load_file(arg)


class Merge(LoaderBased):

  name = '_merge'

  def eval(self, doc, arg):
    return merge_docs(yd.Document(doc.env, a) for a in arg)


class MergeOverride(LoaderBased):

  name = '_merge_override'

  def eval(self, doc, arg):
    return merge_docs((yd.Document(doc.env, a) for a in arg), safe=False)


class InsertMerge(LoaderBased):

  name = '_insert_merge'

  def eval(self, doc, arg):
    return merge_docs(self.loader.load_file(fp) for fp in arg)


class Include(LoaderBased):

  name = '_include'

  def eval(self, doc, arg):
    for d in (self.loader.load_file(fp) for fp in arg):
      doc.merge(d)
