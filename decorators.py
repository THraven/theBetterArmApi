"""This file holds all the decorators we use in this project"""

import json
import uweb

def head(f):
  """Will return a dict with all the data in env['QUERY_STRING']."""
  def wrapper(*args, **kwargs):
    self = args[0]
    raw = self.req.env["QUERY_STRING"]
    entrys = raw.split("&")
    data = {}
    for i in entrys:
      thing = i.split("=")
      data.update({"%s" % thing[0]: "%s" % thing[1]})
    args += (data, )
    f(*args, **kwargs)
  return wrapper


def axisInMachine(f):
  """will check how many axis are in the machine"""
  def wrapper(*args, **kwargs):
    self = args[0]
    self.s.poll()
    pos = self.s.actual_position
    allAxis = []
    axis = self.s.axis
    count = 0
    axisthing = []
    for i in pos:
      if axis[count]["max_position_limit"] != 0.0:
        allAxis.append(count)
      else:
        axisthing.append(axis[count]["max_position_limit"])
      count += 1
    args += (allAxis, )
    return f(*args, **kwargs)
  return wrapper


def haspost(fields=[], message='Error: postdata missing'):
    """Decorator that checks if the requested post vars are available"""
    def checkfields(f):
        def wrapper(*args, **kwargs):
          if not args[0].post:
            return args[0].ErrorPage(message)
          for field in fields:
            if field not in args[0].post:
              return args[0].ErrorPage('%s, %s missing.' % (message, field))
          return f(*args, **kwargs)
        return wrapper
    return checkfields


def JsonResponse(f):
  """Return the dict given as a json obj."""
  def wrapper(*args, **kwargs):
    return uweb.Response(
        content=json.dumps(f(*args, **kwargs)),
        content_type="application/json")
  return wrapper
