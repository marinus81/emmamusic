import os
import subprocess
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
os.environ["SDL_AUDIODRIVER"] = "none" 
#os.environ["SDL_PATH_DSP"] = "/dev/null" 

#init Logging



log_format = '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format))
logger = logging.getLogger()
if len(sys.argv) >1 and sys.argv[1]=='--debug':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.ERROR)
logger.addHandler(console_handler)

MARGIN = 20



class EmmaMusicScene(ui.Scene):
    def __init__(self, player):
        ui.Scene.__init__(self)
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.player=player
        self.player.link_scene(self)
        
        self.last_action_ts=pygame.time.get_ticks()
        
        
        self.img_prev=ui.get_image('rewind-icon_s')
        self.img_play=ui.get_image('play-icon_s')
        self.img_pause=ui.get_image('pause-icon_s')
        self.img_next=ui.get_image('forward-icon_s')
        
        label_height = ui.theme.current.label_height
        scrollbar_size = ui.SCROLLBAR_SIZE

        self.background=ui.ImageButton(ui.Rect(0,16,320,215), ui.get_image('splash','/home/pi/music/images/'))
        self.background.on_clicked.connect(self.button_click)
        self.add_child(self.background)
        
        self.now_playing=ui.Label(ui.Rect(0, 0, 320, label_height), '')
        self.add_child(self.now_playing)
        
        self.buttons_visible=False
        
        self.btn_prev=ui.ImageButton(ui.Rect(20,88,64,64), self.img_prev)
        self.btn_prev.on_clicked.connect(self.button_click)
        self.btn_prev.hidden=True
        self.add_child(self.btn_prev)
        
        self.playicon=True
        self.btn_play=ui.ImageButton(ui.Rect(120,88,64,64), self.img_play)
        self.btn_play.on_clicked.connect(self.button_click)
        self.btn_play.hidden=True
        self.add_child(self.btn_play)
        
        self.btn_next=ui.ImageButton(ui.Rect(220,88,64,64), self.img_next)
        self.btn_next.on_clicked.connect(self.button_click)
        self.btn_next.hidden=True
        self.add_child(self.btn_next)
        
   
   
    def set_now_playing_title(self, title):
        self.now_playing.text=title
        
    def new_card(self, card_id):
        self.last_action_ts=pygame.time.get_ticks()
        self.background.hidden=True
        self.background.image_view.image=ui.get_image(card_id,'/home/pi/music/images/')
        self.background.hidden=False
        self.show_buttons()
        
    def set_background_image(self, imagename):
        self.background.image=ui.get_image(imagename,'/home/pi/music/images/')
        
    def show_buttons(self):
        if not self.buttons_visible:
            self.show_time=pygame.time.get_ticks() #remember time when we showed buttons
            self.btn_prev.hidden=False
            self.btn_play.hidden=False
            self.btn_next.hidden=False
            self.buttons_visible=True
        
    def hide_buttons(self):
        if self.buttons_visible:
            self.btn_prev.hidden=True
            self.btn_play.hidden=True
            self.btn_next.hidden=True
            self.buttons_visible=False

    def button_click(self, btn, mbtn):
        self.last_action_ts=pygame.time.get_ticks()
        if btn is self.btn_play:
            logger.debug("button_click: btn_play ")
            self.show_time=pygame.time.get_ticks() #refresh show time, so countdown restarts
            player.pause()
        elif btn is self.btn_prev: 
            player.prev()
        
        elif btn is self.btn_next:
            player.next()
        
        elif btn is self.background:
            logger.debug("button_click: background ")
            if self.now_playing.text != '':
                self.show_buttons()
        else:
            logger.debug("button_click: <unknown>")
            
    def update(self, dt):     
        status=player.get_status()

        #if self.now_playing.text != player.get_song_title():
        self.now_playing.text = player.get_song_title()
        
        if status['state'] == 'play':
            self.last_action_ts=pygame.time.get_ticks()
        
        if (pygame.time.get_ticks() - self.last_action_ts) > 120000:
            self.do_shutdown()
        
        if self.buttons_visible:
            logger.debug("Status: %s, playicon= %s"%(status['state'],self.playicon))
            if status['state'] != 'play' and self.playicon:
                self.btn_play.image_view.image=self.img_pause
                self.playicon=not self.playicon
            elif status['state'] == 'play' and not self.playicon:
                self.btn_play.image_view.image=self.img_play
                self.playicon=not self.playicon
                    
            if (pygame.time.get_ticks() - self.show_time) > 5000:   #if some time has passed, hide buttons
                self.hide_buttons()
        
        ui.Scene.update(self, dt)
        #self.set_now_playing_title(player.songtitle()['title'])
	
    def signal_handler(self, signal, frame):
        logger.error("You pressed Ctrl+C!")
        logger.debug("calling rfidreader.terminate()")
        rfidreader.terminate()
        logger.debug("calling player.close")
        player.close()
        logger.debug("calling pygame.quit")
        pygame.quit()
        logger.debug("calling sys.exit(0)")
        sys.exit(0)

    def do_shutdown(self):
        #os.system("sudo shutdown -h now")
        rfidreader.terminate()
        player.close()
        time.sleep(5)
        #GPIO.cleanup()
        command = "/usr/bin/sudo /sbin/shutdown -h now"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        #output = process.communicate()[0]
        #print output
        pygame.quit()
        sys.exit(0)



if __name__ == '__main__':
    
    player=Player()
        
    
    ui.init('Raspberry Pi UI', (320, 240))
    pygame.mouse.set_visible(False)
    
    emscene = EmmaMusicScene(player)

    #start RFID Reader Thread
    rfidreader = RFIDReader(emscene,player)
    threading.Thread(target=rfidreader).start()
  
   
    
    ui.scene.push(emscene)
    ui.run()
