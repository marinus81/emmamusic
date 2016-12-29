#!/bin/python
# Simple script for shutting down the raspberry Pi at the press of a button.
# by Inderpreet Singh

import RPi.GPIO as GPIO
import time

# Use the Broadcom SOC Pin numbers
# Setup the Pin with Internal pullups enabled and PIN in reading mode.

GPIO.setmode(GPIO.BCM)
#GPIO.remove_event_detect(4)

time.sleep(5)

GPIO.setup(4, GPIO.OUT)
GPIO.output(4,False)

#GPIO.cleanup()

time.sleep(5)

