# theBetterArmApi

### general
A link consists of one or more functions within a method, these functions
are to separate the methods being send to the link and are to ensure that
if one call doesn't work the other one will continue to function as normal.

To change the way a function works simply go to the link bound method and
change the code inside the function named after the methods you want to change.

The index template is a testing environment and as a example file to show
how http request will have to be send. However the API will work fine if
you completely remove the templates folder.


### dependencies
**Machinekit**,
**Linuxcnc**,
**Uweb**

Must be installed for the API to work as it should.
To install these dependencies simply do the following:

there are a couple of ways to install machinkit,
visit: http://www.machinekit.io/docs/getting-started/getting-started-platform/
to see them all

to install Linuxcnc visit:
http://www.linuxcnc.org/docs/html/getting-started/getting-linuxcnc.html

to install Uweb simply open a command line and write:
`pip install uweb`


### mounting the server
after installing the dependencies clone the repository
to the directory you want to server to run and execute
the following commands

`uweb add [sitename]`

once uweb is done adding the server simply run `uweb start [sitename]` and uweb should start the server
