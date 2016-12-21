#!/usr/bin/python

from __future__ import print_function
import subprocess, time, Image, socket
from Adafruit_Thermal import *

printer      = Adafruit_Thermal("/dev/ttyAMA0", 9600, timeout=5)

# Called after every action.
def face():
  printer.printImage(Image.open('gfx/face01.png'), True)
  printer.feed(7)
  

face()
