#!/bin/python
# Simple script for shutting down the raspberry Pi at the press of a button.
# by Inderpreet Singh

import RPi.GPIO as GPIO
import time

# Use the Broadcom SOC Pin numbers
# Setup the Pin with Internal pullups enabled and PIN in reading mode.

GPIO.setmode(GPIO.BCM)

time.sleep(5)

GPIO.setup(4, GPIO.OUT)
GPIO.output(4,False)

time.sleep(5)

