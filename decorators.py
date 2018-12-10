"""This file holds all the decorators we use in this project"""

import json
import uweb
import linuxcnc
s = linuxcnc.stat()
axis = {
    0: "X",  1: "Y",  2: "Z",  3: "A",
    4: "B",  5: "C",  6: "U",  7: "V",
    8: "W",  9: "R" }

def head(f):
  """Will return a dict with all the data in env['QUERY_STRING']."""
  def wrapper(*args, **kwargs):
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
    s.poll()
    pos = s.actual_position
    allAxis = []
    axis = s.axis
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


def checkxsrf(f):
    """Decorator that checks if the xsrf in the user's cookie matches that from
    the (post) request"""
    def wrapper(*args, **kwargs):
      if args[0].incorrect_xsrf_token:
        return args[0].ErrorPage(
            'Your XSRF token was incorrect, please try again.', 403)
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

def loggedin(f):
    """Decorator that checks if the user requesting the page is in fact logged
    in"""
    def wrapper(*args, **kwargs):
      if not args[0].user:
        return args[0].Login()
      return f(*args, **kwargs)
    return wrapper

import sys
PYTHON_VERSION = 2
if (sys.version_info > (3, 0)):
  PYTHON_VERSION = 3

def TemplateParser(template, *t_args, **t_kwargs):
    """Decorator that wraps the output in a templateparser call if its not
    already something that we prepared for direct output to the client"""
    def template_decorator(f):
      def wrapper(*args, **kwargs):
        pageresult = f(*args, **kwargs) or {}
        if ((PYTHON_VERSION == 3
             and not isinstance(pageresult, (str, uweb.Response, uweb.Redirect))
            )
          or (PYTHON_VERSION == 2
              and not isinstance(pageresult,
                                 (str, unicode, uweb.Response, uweb.Redirect)))
           ):
          if 'user' in pageresult:
            t_kwargs['user'] = pageresult['user']
          pageresult.update(args[0].Parts(*t_args, **t_kwargs))
          return args[0].parser.Parse(template, **pageresult)
        return pageresult
      return wrapper
    return template_decorator

def JsonResponse(f):
  def wrapper(*args, **kwargs):
    return uweb.Response(
        content=json.dumps(f(*args, **kwargs)),
        content_type="application/json")
  return wrapper
