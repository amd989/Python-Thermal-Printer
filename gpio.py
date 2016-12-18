#!/usr/bin/python

import RPi.GPIO as GPIO
import time

# Use Raspberry Pi pin numbers (not Broadcom pin numbers)
#GPIO.setmode(GPIO.BOARD)
# Use broadcom pins
GPIO.setmode(GPIO.BCM)

greenled    = 18
greenbutton = 23

GPIO.setup(greenled, GPIO.OUT)
GPIO.setup(greenbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Read pin
#val = GPIO.input(pin)
#print val

while(1):
	GPIO.output(greenled, GPIO.HIGH)
	if(GPIO.input(greenbutton) == False):
		print "Green button pressed"
	time.sleep(1)
	GPIO.output(greenled, GPIO.LOW)
	if(GPIO.input(greenbutton) == False):
		print "Green button pressed"
	time.sleep(1)

# Watch for 'falling' event on pin:
# (experimental stuff)
#GPIO.set_falling_event(pin)
#if(GPIO.event_detected(pin)):
#	print("Falling edge detected!")

# Reset all channels to inputs w/no pullup/dn
#GPIO.cleanup()