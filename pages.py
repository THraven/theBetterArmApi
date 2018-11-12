#!/usr/bin/python
"""Html generators for the base uweb server"""
# if you want to easly find a link and you have the ctrl+f feature just search FF[link name] and you'll find it

import uweb
import linuxcnc
import os, sys, time, os.path
import json


class PageMaker(uweb.DebuggingPageMaker):
  """Holds all the html generators for the webapp

  Each page as a separate method.
  """
  axis = {
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
  s = linuxcnc.stat()
  c = linuxcnc.command()

  def Test(self):
    F = open("armApi/prefabs/0&amount.txt", "r+")
    if F.read() == "":
      F.write("%s"%len(os.listdir("armApi/prefabs")))
      F.close()
    else:
      files = os.listdir("armApi/prefabs/")
      number = int(files[0].split("&")[0]) + 1
      F = open("armApi/prefabs/0&amount.txt", "w")
      F.write("%s"%number)

  def queryParser(self):
    "will return a dict with all the data in env['QUERY_STRING']"
    raw = self.req.env["QUERY_STRING"]
    entrys = raw.split("&")
    data = {}
    for i in entrys:
      thing = i.split("=")
      data.update({"%s"%thing[0]: "%s"%thing[1]})
    return data


  def axisInMachine(self):
    "checks what axis are in the machine using thier maximum position limit"
    self.s.poll()
    pos = self.s.actual_position
    allAxis = []
    axis = self.s.axis
    count = 0
    axisthing = []
    for i in pos:
      if axis[count]["max_position_limit"] != 0.0:
        allAxis.append(count)
        count += 1
      else:
        axisthing.append(axis[count]["max_position_limit"])
        count += 1
    return allAxis

  def Index(self):
    """Returns the index.html template"""
    return self.parser.Parse('index.html')

  # FFPostion
  def Position(self):
    "this is the position link. it will allow you to change and get he position of the head"
    # if you wanna change how the POST works, do it here
    def post():
      if self.req.env["REQUEST_METHOD"] == "POST":
        self.s.poll()
        gcode = "G1 "
        pos = self.s.actual_position
        axis = self.axisInMachine()
        for i in axis:
          if self.post.getfirst(self.axis[i]):
            gcode = gcode + "%s%s "%(self.axis[i], self.post.getfirst(self.axis[i]))
          else:
            gcode = gcode + "%s%s "%(self.axis[i], round(pos[i]))

        gcode = gcode + "F%s" %self.post.getfirst("F") if self.post.getfirst("F") else gcode + "F10000"
        self.c.mdi(gcode)
        return gcode

    # if you wanna change how the GET works, do it here
    def get():
      self.s.poll()
      pos = self.s.actual_position
      axis, axis_max, axis_min = {},{},{}
      for i in self.axisInMachine():
        axis.update({"%s"%self.axis[i]: pos[i]})
        axis_max.update({"%s"%self.axis[i]: self.s.axis[i]["max_position_limit"]})
        axis_min.update({"%s"%self.axis[i]: self.s.axis[i]["min_position_limit"]})
      Rjson = {"axis": axis, "axis_max": axis_max, "axis_min": axis_min}
      return uweb.Response(json.dumps(Rjson), content_type="application/json")

    # if you wanna change how the HEAD works, do it here
    def head():
      pass
      # if self.post.getfirst("submit")
    method = {
      "POST": post(),
      "GET": get(),
    }
    return method[self.req.env["REQUEST_METHOD"]]

  # FFFile
  def File(self):
    "this link will give you the abilliy to send a file and execute it"
    def get():
        self.s.poll()
        file = self.s.file
        if file != "":
          Temp = file.split("/")
          running = [True, Temp[len(Temp) -1]]
        else:
          running = [False, "no file running"]
        Rjson = {"Running": running[0], "Running_file": running[1], "file": file}
        return uweb.Response(json.dumps(Rjson), content_type="application/json")

    def post():
      try:
        fileData = self.post["File"].value
        fileName = self.post["File"].filename
        self.s.poll()
        self.c.mode(linuxcnc.MODE_AUTO)
        self.c.wait_complete()
        with open("armApi/temp.ngc", "w") as F:
          F.write(fileData)
        self.c.program_open("/home/machinekit/Desktop/armApi/temp.ngc")
        self.c.wait_complete()
        self.c.auto(linuxcnc.AUTO_RUN, 1)
        Rjson = {"fileData": fileData, "fileName": fileName}
        return Rjson
      except Exception as e:
        if self.req.env["REQUEST_METHOD"] == "POST":
          raise e
        else:
          pass

    method = {
      "GET": get(),
      "POST": post(),
    }

    return method[self.req.env["REQUEST_METHOD"]]

  # FFStats
  def Stats(self):
    def get():
      self.s.poll()
      Max_vel = self.s.max_velocity
      Spin_rate = self.s.spindle_speed
      Axis = []
      for i in self.axisInMachine():
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
      return uweb.Response(json.dumps(Rjson), content_type="application/json")

    def head():
      if self.req.env['REQUEST_METHOD'] == "HEAD":
        headz = self.queryParser()
        for i in headz:
          Max_vel = 1 if i == "Max_vel" else None
          Spin_rate = 1 if i == "Spin_rate" else None
          Feed_rate = 1 if i == "Feed_rate" else None
        if Max_vel:
          self.c.maxvel(float(headz["Max_vel"]))
        if Spin_rate:
          pass
        if Feed_rate:
          self.c.feedrate(float(headz["Feed_rate"]))
        return 1
    method = {
      "GET": get(),
      "HEAD": head(),
    }
    return method[self.req.env["REQUEST_METHOD"]]

  # FFHome
  def Home(self):
    def get():
      self.s.poll()
      home = self.s.homed
      if 0 in home:
        home = False
      else:
        home = True
      return home

    def post():
      if self.req.env["REQUEST_METHOD"] == "POST":
        for i in self.axisInMachine():
          self.c.home(i)
          self.c.wait_complete()

    method = {
      "GET": get(),
      "POST": post(),
    }
    return method[self.req.env["REQUEST_METHOD"]]

  # FFButtons
  def Buttons(self):
    if self.req.env["REQUEST_METHOD"] == "POST":
      if self.post.getfirst("Command") =="Mdi_mode":
        self.c.mode(linuxcnc.MODE_MDI)
      elif self.post.getfirst("Command") =="Estop":
        self.s.poll()
        # return uweb.Response(json.dumps({"stop": self.s.estop}), content_type="application/json")
        if self.s.estop:
          self.c.state(2)
        else:
          self.c.state(1)
      elif self.post.getfirst("Command") =="Stop":
        self.c.abort()
      elif self.post.getfirst("Command") =="Pause":
        self.c.auto(linuxcnc.AUTO_PAUSE)
      elif self.post.getfirst("Command") =="Resume":
        self.c.auto(linuxcnc.AUTO_RESUME)
      elif self.post.getfirst("Command") =="Repeat":
        self.c.mode(linuxcnc.MODE_AUTO)
        self.c.program_open("/home/machinekit/Desktop/armApi/temp.ngc")
        self.c.wait_complete()
        self.c.auto(linuxcnc.AUTO_RUN, 1)
      else:
        return "button not found"


  # FFPrefabs
  def Prefabs(self):
    "this link will allow you to send a server a file and it will store it"
    # this is will make sure that all ids in the file are one of a kind
    F = open("armApi/prefabs/0&amount.txt", "w")
    F.close()
    F = open("armApi/prefabs/0&amount.txt", "r+")
    if F.read() == "":
      F.write("%s"%len(os.listdir("armApi/prefabs")))
      F.close()
    else:
      files = os.listdir("armApi/prefabs/")
      number = int(files[0].split("&")[0]) + 1
      F = open("armApi/prefabs/0&amount.txt", "w")
      F.write("%s"%number)

    def get():
      Rjson = {}
      for i in os.listdir("armApi/prefabs"):
        compon = i.split("&")
        F = open("armApi/prefabs/%s"%i, "r")
        Rjson.update({"%s"%compon[0]: {"name": compon[1], "content": F.read()}})
      return uweb.Response(json.dumps(Rjson), content_type="application/json")

    def post():
      if self.req.env["REQUEST_METHOD"] == "POST":
        name = self.post["file"].filename
        content = self.post["file"].value
        O = open("armApi/prefabs/0&amount.txt", "r")
        number = O.read()
        F = open("armApi/prefabs/%s&%s"%(number, name), "w")
        try:
          F.write(unicode(content, "utf-8"))
        except Exception as e:
          return "please use utf8 encoding for your files"
        return self.Index()

    def head():
      if self.req.env["REQUEST_METHOD"] == "HEAD":
        id = self.queryParser()["id"]
        for i in os.listdir("armApi/prefabs"):
          name = i.split("&")[0]
          if name == id:
            fullname = i
        self.c.mode(linuxcnc.MODE_AUTO)
        self.c.wait_complete()
        self.c.program_open("/home/machinekit/Desktop/armApi/prefabs/%s"%fullname)
        self.c.wait_complete()
        self.c.auto(linuxcnc.AUTO_RUN, 1)


    method = {
      "GET": get(),
      "POST": post(),
      "HEAD": head(),
    }

    return method[self.req.env["REQUEST_METHOD"]]

  # FFpower
  def Power(self):
    def get():
      self.s.poll()
      return self.s.axis[1]["enabled"]
    def post():
      if self.req.env["REQUEST_METHOD"] == "POST":
        self.s.poll()
        on = self.s.axis[1]["enabled"]
        if on:
          self.c.state(3)
        else:
          self.c.state(4)
        return self.Index()


    method = {
      "GET": get(),
      "POST": post(),
    }

    return method[self.req.env["REQUEST_METHOD"]]


  def Status(self):
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
      return uweb.Response(json.dumps(Rjson), content_type="application/json")


  def FourOhFour(self, path):
    """The request could not be fulfilled, this returns a 404."""
    return uweb.Response(self.parser.Parse('404.utp', path=path),
                         httpcode=404)