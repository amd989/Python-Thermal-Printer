#!/usr/bin/python

# Main script for Adafruit Internet of Things Printer 2.  Monitors button
# for taps and holds, performs periodic actions (Twitter polling by default)
# and daily actions (Sudoku and weather by default).
# Written by Adafruit Industries.  MIT license.
#
# MUST BE RUN AS ROOT (due to GPIO access)
#
# Required software includes Adafruit_Thermal, Python Imaging and PySerial
# libraries. Other libraries used are part of stock Python install.
#
# Resources:
# http://www.adafruit.com/products/597 Mini Thermal Receipt Printer
# http://www.adafruit.com/products/600 printer starter pack

from __future__ import print_function
import RPi.GPIO as GPIO
import subprocess, time, Image, socket
from Adafruit_Thermal import *
import threading
import server
import printer

ledPin       = 18
buttonPin    = 23
holdTime     = 2     # Duration for button hold (shutdown)
tapTime      = 0.01  # Debounce time for button taps
nextInterval = 0.0   # Time of next recurring operation
dailyFlag    = False # Set after daily trigger occurs
lastId       = '1'   # State information passed to/from interval script
device      = Adafruit_Thermal("/dev/ttyAMA0", 9600, timeout=5)
started      = False # Flag signaling the server has started


# Called after every action.
def face():
  device.printImage(Image.open('gfx/face01.png'), True)
  device.feed(7)
  
# Called when button is briefly tapped.  Invokes time/temperature script.
def tap():
  GPIO.output(ledPin, GPIO.HIGH)  # LED on while working
  subprocess.call(["python", "timetemp.py"])  
  GPIO.output(ledPin, GPIO.LOW)
  time.sleep(3)


# Called when button is held down.  Prints image, invokes shutdown process.
def hold():
  GPIO.output(ledPin, GPIO.HIGH)
  device.printImage(Image.open('gfx/goodbye.png'), True)
  device.feed(9)
  time.sleep(5)
  subprocess.call("sync")
  subprocess.call(["shutdown", "-h", "now"])
  GPIO.output(ledPin, GPIO.LOW)


# Called at periodic intervals (30 seconds by default).
# Invokes twitter script.
def interval():
  GPIO.output(ledPin, GPIO.HIGH)
  p = subprocess.Popen(["python", "twitter.py", str(lastId)],
    stdout=subprocess.PIPE)
  GPIO.output(ledPin, GPIO.LOW)
  return p.communicate()[0] # Script pipes back lastId, returned to main


# Called once per day (6:30am by default).
# Invokes weather forecast and sudoku-gfx scripts.
def daily():
  GPIO.output(ledPin, GPIO.HIGH)
  subprocess.call(["python", "forecast.py"])
  #subprocess.call(["python", "sudoku-gfx.py"])
  GPIO.output(ledPin, GPIO.LOW)


# Initialization

# Use Broadcom pin numbers (not Raspberry Pi pin numbers) for GPIO
GPIO.setmode(GPIO.BCM)

# Enable LED and button (w/pull-up on latter)
GPIO.setup(ledPin, GPIO.OUT)
GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# LED on while working
GPIO.output(ledPin, GPIO.HIGH)

# Processor load is heavy at startup; wait a moment to avoid
# stalling during greeting.
time.sleep(15)

# Show IP address (if network is available)
try:
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(('8.8.8.8', 0))
  device.boldOn()
  device.print('My IP address is ' + s.getsockname()[0])
  device.boldOff()
  device.feed(3)
except:
  device.boldOn()
  device.println('Network is unreachable.')
  device.boldOff()
  device.print('Connect display and keyboard\n'
    'for network troubleshooting.')
  device.feed(3)
  exit(0)

# Print greeting image
device.printImage(Image.open('gfx/hello.png'), True)
device.feed(3)
GPIO.output(ledPin, GPIO.LOW)

# Poll initial button state and time
prevButtonState = GPIO.input(buttonPin)
prevTime        = time.time()
tapEnable       = False
holdEnable      = False

# Starts the webservice
webservice_thread = threading.Thread(target=server.run_webservice)
webservice_thread.start()

# Main loop
while(True):

  # Poll current button state and time
  buttonState = GPIO.input(buttonPin)
  t           = time.time()

  # Has button state changed?
  if buttonState != prevButtonState:
    prevButtonState = buttonState   # Yes, save new state/time
    prevTime        = t
  else:                             # Button state unchanged
    if (t - prevTime) >= holdTime:  # Button held more than 'holdTime'?
      # Yes it has.  Is the hold action as-yet untriggered?
      if holdEnable == True:        # Yep!
        hold()                      # Perform hold action (usu. shutdown)
        holdEnable = False          # 1 shot...don't repeat hold action
        tapEnable  = False          # Don't do tap action on release
    elif (t - prevTime) >= tapTime: # Not holdTime.  tapTime elapsed?
      # Yes.  Debounced press or release...
      if buttonState == True:       # Button released?
        if tapEnable == True:       # Ignore if prior hold()
          tap()                     # Tap triggered (button released)
          face()                    # Print face after tap
          tapEnable  = False        # Disable tap and hold
          holdEnable = False
      else:                         # Button pressed
        tapEnable  = True           # Enable tap and hold actions
        holdEnable = True

  # LED blinks while idle, for a brief interval every 2 seconds.
  # Pin 18 is PWM-capable and a "sleep throb" would be nice, but
  # the PWM-related library is a hassle for average users to install
  # right now.  Might return to this later when it's more accessible.
  if ((int(t) & 1) == 0) and ((t - int(t)) < 0.15):
    GPIO.output(ledPin, GPIO.HIGH)
  else:
    GPIO.output(ledPin, GPIO.LOW)

  # Prints the printer queue
  while not printer.queue.empty():

    print_order = printer.queue.get()
    print_order.execute()

  # Once per day (currently set for 6:30am local time, or when script
  # is first run, if after 6:30am), run forecast and sudoku scripts.
  l = time.localtime()
  if (60 * l.tm_hour + l.tm_min) > (60 * 6 + 30):
    if dailyFlag == False:
      daily()
      dailyFlag = True
  else:
    dailyFlag = False  # Reset daily trigger

  # Every 30 seconds, run Twitter scripts.  'lastId' is passed around
  # to preserve state between invocations.  Probably simpler to do an
  # import thing.
  if t > nextInterval:
    nextInterval = t + 30.0
    result = interval()
    if result is not None:
      lastId = result.rstrip('\r\n')
