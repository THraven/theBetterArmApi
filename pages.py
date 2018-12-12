#!/usr/bin/python
"""Html generators for the base uweb server."""

import uweb
import linuxcnc
import os
import os.path
import json
import decorators


class PageMaker(uweb.DebuggingPageMaker):
  """Holds all the html generators for the webapp.

  Each page as a separate method
  """


  @property
  def s(self):
    if hasattr(self, '_s'):
      return self._s
    self._s = linuxcnc.stat()
    return self._s

  @property
  def c(self):
    if hasattr(self, '_c'):
      return self._c
    self._c = linuxcnc.command()
    return self._c

  @property
  def e(self):
    if hasattr(self, '_e'):
      return self._e
    self._e = linuxcnc.error_channel()
    return self._e

  @property
  def axis(self):
    if hasattr(self, '_axis'):
      return self._axis
    self._axis = {
     0: "X",
     1: "Y",
     2: "Z",
     3: "A",
     4: "B",
     5: "C",
     6: "U",
     7: "V",
     8: "W",
     9: "R"
    }
    return self._axis

  @property
  def axisInMachine(self):
    if hasattr(self, '_axisInMachine'):
      return self._axisInMachine

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
    self._axisInMachine = allAxis
    return self._axisInMachine

  @property
  def headz(self):
    if hasattr(self, '_headz'):
      return self._headz
    return None

  @headz.setter
  def headz(self, value):
    self._headz = value

  @decorators.head
  def Test(self):
    pass
  # methods bound to a link
  def Index(self):
    """Return the index.html template."""
    return self.parser.Parse('index.html')

  def Position(self):
    """Return and set the position of all axis in machine."""
    # if you wanna change how the POST works, do it here
    def post():
      """will allow you to set the position of the head"""
      self.s.poll()
      gcode = "G1 "
      pos = self.s.actual_position
      temp = []
      for i in self.axisInMachine:
        if self.post.getfirst(self.axis[i]):
          gcode = gcode + "%s%s " % (self.axis[i],
                                     self.post.getfirst(self.axis[i]))
        else:
          gcode = gcode + "%s%s " % (self.axis[i], pos[i])

      if self.post.getfirst("F"):
        gcode = gcode + "F%s" % self.post.getfirst("F")
      else:
        gcode + "F10000"
      self.c.mdi(gcode)
      return gcode

    # if you wanna change how the GET works, do it here
    @decorators.JsonResponse
    def get():
      """Will give you the current position of the head."""
      self.s.poll()
      pos = self.s.actual_position
      temp = []
      axis = axis_max = axis_min = {}
      for i in self.axisInMachine:
        axis.update({"%s" % self.axis[i]: pos[i]})
        axis_max.update({"%s" % self.axis[i]: self.s.axis[i]["max_position_limit"]})
        axis_min.update({"%s" % self.axis[i]: self.s.axis[i]["min_position_limit"]})
      Rjson = {"axis": axis, "axis_max": axis_max, "axis_min": axis_min}
      return Rjson

    req = self.req.env["REQUEST_METHOD"]

    if req == "GET":
      return get()
    elif req == "POST":
      return post()

  @decorators.haspost(['File'])
  def File(self):
    """GET will return file running.

    POST will allow you to run a file.
    """
    @decorators.JsonResponse
    def get():
        """Will return if a file is running and if yes which."""
        self.s.poll()
        file = self.s.file
        if file != "":
          Temp = file.split("/")
          running = [True, Temp[len(Temp) - 1]]
        else:
          running = [False, "no file running"]
        Rjson = {"Running": running[0], "Running_file": running[1], "file": file}
        return Rjson

    def post():
      """Will allow you to set the file it should run."""
      try:
        fileData = self.post["File"].value
        fileName = self.post["File"].filename
        self.s.poll()
        self.c.mode(linuxcnc.MODE_AUTO)
        self.c.wait_complete()
        with open("armApi/temp.ngc", "w") as File:
          File.write(fileData)
        self.c.program_open("armApi/temp.ngc")
        self.c.wait_complete()
        self.c.auto(linuxcnc.AUTO_RUN, 1)
        Rjson = {"fileData": fileData, "fileName": fileName}
        return Rjson
      except Exception:
        pass
    req = self.req.env["REQUEST_METHOD"]

    if req == "GET":
      return get()
    elif req == "POST":
      return post()

  @decorators.head
  def Stats(self):
    """GET link will return the stats of the machine.

    HEAD will allow you to set some stats.
    """
    @decorators.JsonResponse
    def get():
      """Will return you some stats of the machine."""
      self.s.poll()
      Max_vel = self.s.max_velocity
      Spin_rate = self.s.spindle_speed
      Axis = []
      for i in self.axisInMachine:
        Axis.append(self.axis[i])
      sum = self.s.axis[0]["velocity"] + self.s.axis[1]["velocity"] + self.s.axis[2]["velocity"]
      Current_speed = sum / 3
      Feed_rate = self.s.feedrate
      Rjson = {
        "Max_vel": Max_vel,
        "Spin_rate": Spin_rate,
        "Axis": Axis,
        "Current_speed": Current_speed,
        "Feed_rate": Feed_rate,
      }
      return Rjson

    def head():
      """Will allow you to change some of the stats of the machine."""
      if self.headz['Max_vel']:
        self.c.maxvel(float(self.headz["Max_vel"]))
      if self.headz['Spin_rate']:
        pass
      if self.headz['Feed_rate']:
        self.c.feedrate(float(self.headz["Feed_rate"]))

    req = self.req.env["REQUEST_METHOD"]

    if req == "GET":
      return get()
    elif req == "HEAD":
      return head()

  def Home(self):
    """GET will return homed flag.

    POST will home the machine.
    """
    def get():
      """Will return which of the axis are homed and which are not."""
      self.s.poll()
      home = self.s.homed
      if 0 in home:
        home = False
      else:
        home = True
      return home

    def post():
      """Will allow you to tell the machine to go home."""  # It doesn't even have to be drunk.
      if self.req.env["REQUEST_METHOD"] == "POST":
        for i in self.axisInMachine:
          self.c.home(i)
          self.c.wait_complete()

    req = self.req.env["REQUEST_METHOD"]

    if req == "GET":
      return get()
    elif req == "POST":
      return post()

  @decorators.haspost(['Command'])
  def Buttons(self):
    """Buttons can handle button commands."""
    if self.req.env["REQUEST_METHOD"] == "POST":
      if self.post.getfirst("Command") == "Mdi_mode":
        self.c.mode(linuxcnc.MODE_MDI)
      elif self.post.getfirst("Command") == "Estop":
        self.s.poll()
        if self.s.estop:
          self.c.state(2)
        else:
          self.c.state(1)
      elif self.post.getfirst("Command") == "Stop":
        self.c.abort()
      elif self.post.getfirst("Command") == "Pause":
        self.c.auto(linuxcnc.AUTO_PAUSE)
      elif self.post.getfirst("Command") == "Resume":
        self.c.auto(linuxcnc.AUTO_RESUME)
      elif self.post.getfirst("Command") == "Repeat":
        self.c.mode(linuxcnc.MODE_AUTO)
        self.c.program_open("armApi/temp.ngc")
        self.c.wait_complete()
        self.c.auto(linuxcnc.AUTO_RUN, 1)
      else:
        return "button not found"

  @decorators.haspost(['file'])
  @decorators.head
  def Prefabs(self):
    """GET will return all prefabs saved in the prefabs folder.

    POST will allow you to save a file in the machine.

    HEAD will allow you to run the file given.
    """
    # this is will make sure that all ids in the file are one of a kind
    File = open("armApi/prefabs/0&amount.txt", "w")
    File.close()
    File = open("armApi/prefabs/0&amount.txt", "r+")
    if File.read() == "":
      File.write("%s" % len(os.listdir("armApi/prefabs")))
      File.close()
    else:
      files = os.listdir("armApi/prefabs/")
      number = int(files[0].split("&")[0]) + 1
      File = open("armApi/prefabs/0&amount.txt", "w")
      File.write("%s" % number)

    @decorators.JsonResponse
    def get():
      """Will allow you to get all the files stored and there content."""
      Rjson = {}
      for i in os.listdir("armApi/prefabs"):
        compon = i.split("&")
        File = open("armApi/prefabs/%s" % i, "r")
        Rjson.update({"%s" % compon[0]: {"name": compon[1], "content": File.read()}})
      return Rjson

    def post():
      """Will allow you to send a file and store it in the server."""
      name = self.post["file"].filename
      content = self.post["file"].value
      File = open("armApi/prefabs/0&amount.txt", "r")
      number = File.read()
      File = open("armApi/prefabs/%s&%s" % (number, name), "w")
      try:
        File.write(unicode(content, "utf-8"))
      except Exception:
        return "please use utf8 encoding for your files"
      return self.Index()

    def head():
      """Will allow you to run a file on the server."""
      if self.req.env["REQUEST_METHOD"] == "HEAD":
        id = self.headz["id"]
        for i in os.listdir("armApi/prefabs"):
          name = i.split("&")[0]
          if name == id:
            fullname = i
        self.c.mode(linuxcnc.MODE_AUTO)
        self.c.wait_complete()
        self.c.program_open("/armApi/prefabs/%s" % fullname)
        self.c.wait_complete()
        self.c.auto(linuxcnc.AUTO_RUN, 1)

    if self.req.env["REQUEST_METHOD"] == "GET":
      return get()
    elif self.req.env["REQUEST_METHOD"] == "POST":
      return post()
    elif self.req.env["REQUEST_METHOD"] == "HEAD":
      return head()

  def Power(self):
    """GET will return the power flag.

    POST will allow you to turn the power on and off.
    """
    def get():
      """Will return the power status."""
      self.s.poll()
      return self.s.axis[1]["enabled"]

    def post():
      """Will allow you to toggel the power."""
      self.s.poll()
      on = self.s.axis[1]["enabled"]
      if on:
        self.c.state(3)
      else:
        self.c.state(4)
      return self.Index()

    req = self.req.env["REQUEST_METHOD"]

    if req == "GET":
      return get()
    elif req == "POST":
      return post()

  @decorators.JsonResponse
  def Status(self):
    """GET will return return the status of some stuff look in the doc for specifics."""
    if self.req.env["REQUEST_METHOD"] == "GET":
      Rjson = {}
      self.s.poll()
      home = self.s.homed
      if 0 in home:
        home = False
      file = self.s.file
      if file != "":
        running = True
      Rjson.update({"Power": self.s.axis[1]["enabled"]})
      Rjson.update({"Home": home})
      Rjson.update({"Active": running})
      return Rjson

  @decorators.haspost(["FOM"])
  def Coolant(self):
    """GET will return the mist and flood flags.

    POST will allow you to turn the mist and flood on and off.
    """
    self.s.poll()

    @decorators.JsonResponse
    def get():
      """Will return the mist, flood status."""
      return {"mist": self.s.mist, "flood": self.s.flood}

    def post():
      """Will allow you to toggel the mist and flood."""
      if self.post.getfirst("FOM") == "flood":
        if self.s.flood:
          self.c.flood(linuxcnc.FLOOD_OFF)
        else:
          self.c.flood(linuxcnc.FLOOD_ON)
      if self.post.getfirst("FOM") == "mist":
        if self.s.mist:
          self.c.mist(linuxcnc.MIST_OFF)
        else:
          self.c.mist(linuxcnc.MIST_ON)

    req = self.req.env["REQUEST_METHOD"]

    if req == "GET":
      return get()
    elif req == "POST":
      return post()

  @decorators.JsonResponse
  def Error(self):
    """Return errors form the machine."""
    error = self.e.poll()

    if error:
      kind, msg = error
      if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
        typus = "error"
      else:
        typus = "info"
      return {"type": typus, "msg": msg}

  def FourOhFour(self, path):
    """The request could not be fulfilled, this returns a 404."""
    return uweb.Response(self.parser.Parse('404.utp', path=path),
                         httpcode=404)
