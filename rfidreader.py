import logging
import time
from pirc522 import RFID

#init Logging
logger = logging.getLogger()

class RFIDReader():
    """Simple RFID Reader running in a thread"""

    def __init__(self, emscene, player):
        """
        Constructor

        :param emscene: Emma Music Player UI Scene
        :param player:  Lockable MPDClient Instance
        """
        self.emscene = emscene
        self.player = player
        self.rdr = RFID(dev='/dev/spidev1.0',pin_rst=37) #requires /boot/config.txt modification: dtparam=spi=on dtoverlay=spi1-1cs,cs0_pin=16

        self.terminated = False
        
    def terminate(self):
        """
        Stop this thread

        :return:
        """
        self.terminated = True
        self.rdr.cleanup()
        
    def __call__(self):
        """
        Thread main loop

        :return:
        """
        while not self.terminated:
            # Read channel 0 in single-ended mode using the settings above
            (error, data) = self.rdr.request()
            if not error:
                logger.debug("\nDetected: " + format(data, "02x"))

            (error, uid) = self.rdr.anticoll()
            if not error:
                logger.debug("Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))
                self.player.play(str(uid[0])+"."+str(uid[1])+"."+str(uid[2])+"."+str(uid[3]))
                time.sleep(1.0)
                
            time.sleep(0.1)
