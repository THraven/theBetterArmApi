"""This file holds all the decorators we use in this project."""

import json
import uweb


def head(f):
  """Will return a dict with all the data in env['QUERY_STRING']."""
  def wrapper(*args, **kwargs):
    pages = args[0]
    raw = pages.req.env["QUERY_STRING"]
    if len(raw) > 0:
      entrys = raw.split("&")
      data = {}
      for i in entrys:
        index, value = i.split("=")
        data.update({"%s" % index: "%s" % value})
      pages.headz = data
      return f(*args, **kwargs)
    return f(*args, **kwargs)
  return wrapper


def haspost(fields=[], message='Error: postdata missing'):
  """Decorator that checks if the requested post vars are available"""
  def checkfields(f):
    def wrapper(*args, **kwargs):
      pages = args[0]
      if not pages.post:
        return pages.ErrorPage(message)
      for field in fields:
        if field not in pages.post:
          return pages.ErrorPage('%s, %s missing.' % (message, field))
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
