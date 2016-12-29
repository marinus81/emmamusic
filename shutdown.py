#!/bin/python
# Simple script for shutting down the raspberry Pi at the press of a button.
# by Inderpreet Singh

import RPi.GPIO as GPIO
import time
import os
import subprocess
import signal

# Use the Broadcom SOC Pin numbers
# Setup the Pin with Internal pullups enabled and PIN in reading mode.


class Shutdown:

    finish=False
    
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.add_event_detect(4, GPIO.FALLING, callback = self.do_shutdown, bouncetime = 2000)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)


    # Our function on what to do when the button is pressed
    def do_shutdown(self,channel):
        #os.system("sudo shutdown -h now")
        print "do_shutdown"
        GPIO.cleanup()
        command = "/usr/bin/sudo /sbin/shutdown -h now"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        print output
        self.finish=True

    def signal_handler(self,signal, frame):
        print "signal handler - signal: %s" % signal
        self.finish=True
        GPIO.cleanup()
        


# Add our function to execute when the button pressed event happens
# Now wait!
if __name__ == '__main__':
    shutdown_monitor=Shutdown()
    
    print "start shutdown_monitor"

    while not shutdown_monitor.finish:
        #print "shutdown_monitor.finish=%s" % shutdown_monitor.finish
        time.sleep(1)

    print "Closing Shutdown Monitor Programm"