class Env(object):
  """Feature key that changes environment."""

  name = '_env'
  validator = None

  def eval(self, doc, arg):
    for k, v in arg.items():
      doc.env[k] = v

    doc.substitute()
