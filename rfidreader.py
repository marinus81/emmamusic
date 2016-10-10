import logging
import time
from pirc522 import RFID

#init Logging
logger = logging.getLogger()

class RFIDReader():
    def __init__(self, emscene, player):
        self.emscene = emscene
        self.player = player
        self.rdr = RFID(dev='/dev/spidev1.0',pin_rst=37)
        self.terminated = False
        
    def terminate(self):
        self.terminated = True
        self.rdr.cleanup()
        
    def __call__(self):
        while not self.terminated:
            # Read channel 0 in single-ended mode using the settings above
            (error, data) = self.rdr.request()
            if not error:
                logger.debug("\nDetected: " + format(data, "02x"))

            (error, uid) = self.rdr.anticoll()
            if not error:
                logger.debug("Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))
                #self.emscene.set_now_playing_title("Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))
                self.player.play(str(uid[0])+"."+str(uid[1])+"."+str(uid[2])+"."+str(uid[3]))
                #logger.debug(self.player.get_file_info())
            
                time.sleep(1.0)
                
            time.sleep(0.1)
