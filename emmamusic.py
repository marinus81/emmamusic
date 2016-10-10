import os
import sys
import pygameui as ui
import logging
import pygame
import RPi.GPIO as GPIO
import signal
import threading
import time
from rfidreader import RFIDReader

from player import Player
from mpd import MPDClient
from threading import Lock


#Init Display
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

#Tell Pygame to not use any audio driver
os.environ["SDL_AUDIODRIVER"] = "disk" 
os.environ["SDL_PATH_DSP"] = "/dev/null" 

#init Logging
log_format = '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format))
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

MARGIN = 20



class EmmaMusicScene(ui.Scene):
    def __init__(self, player):
        ui.Scene.__init__(self)
        
        self.player=player
        label_height = ui.theme.current.label_height
        scrollbar_size = ui.SCROLLBAR_SIZE
        
        self.now_playing=ui.Label(ui.Rect(0, 0, 320, label_height), 'Lied 1234')
        self.add_child(self.now_playing)
        
    def gpi_button(self, btn, mbtn):
        logger.info(btn.text)
        
        if btn.text == '17 on':
            logger.debug("Button 17 on pressed")
    
    def set_now_playing_title(self, title):
        self.now_playing.text=title
     
    def update(self, dt):     
        ui.Scene.update(self, dt)
        #if self.now_playing.text != player.get_song_title():
        self.now_playing.text = player.get_song_title()

        #self.set_now_playing_title(player.songtitle()['title'])
	
def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    rfidreader.terminate()
    player.close()
    sys.exit(0)



if __name__ == '__main__':
    
    player=Player()
        
    
    ui.init('Raspberry Pi UI', (320, 240))
    pygame.mouse.set_visible(False)
    
    emscene = EmmaMusicScene(player)

    #start RFID Reader Thread
    rfidreader = RFIDReader(emscene,player)
    threading.Thread(target=rfidreader).start()
  
    signal.signal(signal.SIGINT, signal_handler)
    
    ui.scene.push(emscene)
    ui.run()
