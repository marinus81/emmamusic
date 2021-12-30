#!/bin/python
# Simple script for shutting down the raspberry Pi at the press of a button.
# by Inderpreet Singh
import logging
import RPi.GPIO as GPIO
import time
import os
import subprocess
import signal


# Use the Broadcom SOC Pin numbers
# Setup the Pin with Internal pullups enabled and PIN in reading mode.


class Shutdown:
    """ Monitor press of a Button and shutdown if pressed"""

    finish = False

    def __init__(self):
        """
        constructor

        """
        logging.debug("Runing __init__, setup GPIO")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        logging.debug("add event handler for GPIO 4")
        GPIO.add_event_detect(4, GPIO.FALLING, callback=self.do_shutdown, bouncetime=4000)
        logging.debug("GPIO was setup, now adding signal handlers")
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        logging.debug("done setup signal handlers")

    # Our function on what to do when the button is pressed
    def do_shutdown(self, channel):
        """
        Event handler for falling edge of monitored GPIO Pin (Power button)

        :param channel: which GPIO PIN
        :return:
        """
        print("do_shutdown")
        logging.debug("running do_shutdown")
        GPIO.cleanup()
        command = "/usr/bin/sudo /sbin/shutdown -h now"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        print(output)
        logging.debug("command output %s" % output)
        self.finish = True

    def signal_handler(self, signal, frame):
        """
        Handle signals (SIGTERM, SIGUP)

        :param signal: Which SIGNAL?
        :param frame:
        :return:
        """
        print("signal handler - signal: %s" % signal)
        logging.debug("signal handler - signal %s" % signal)
        self.finish = True
        GPIO.cleanup()


# Add our function to execute when the button pressed event happens
# Now wait!
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    shutdown_monitor = Shutdown()
    print("start shutdown_monitor")
    logging.info("Start shutdown monitor")

    while not shutdown_monitor.finish:
        # print "shutdown_monitor.finish=%s" % shutdown_monitor.finish
        time.sleep(1)

    print("Closing Shutdown Monitor Programm")
    logging.info("End Shutdown monitor")
