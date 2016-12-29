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
    
    shutdown=False #if True system will shutdown before quitting 
    
    def __init__(self, player):
        ui.Scene.__init__(self)
        
        #prepare signal handler for Ctrl+C and SIGTERM
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        
        #init MPD Player Interface
        self.player=player
        self.player.link_scene(self)
        
        #init last action timestamp
        self.last_action_ts=pygame.time.get_ticks()
        
        
        #load images
        self.img_prev=ui.get_image('rewind-icon_s')
        self.img_play=ui.get_image('play-icon_s')
        self.img_pause=ui.get_image('pause-icon_s')
        self.img_next=ui.get_image('forward-icon_s')
        
        label_height = ui.theme.current.label_height
        scrollbar_size = ui.SCROLLBAR_SIZE

        #create menu
        #create background image
        self.showing_splash=True #remember we show splash screen image
        self.background=ui.ImageButton(ui.Rect(0,16,320,215), ui.get_image('splash','/home/pi/music/images/'))
        self.background.on_clicked.connect(self.button_click)
        self.add_child(self.background)
        
        #create label for currently playing song
        self.now_playing=ui.Label(ui.Rect(0, 0, 320, label_height), '')
        self.add_child(self.now_playing)
        
        
        #create play control buttons (prev, play/pause, next)
        self.buttons_visible=False
        
        self.btn_prev=ui.ImageButton(ui.Rect(20,88,64,64), self.img_prev)
        self.btn_prev.on_clicked.connect(self.button_click)
        self.btn_prev.hidden=True #initially hidden
        self.add_child(self.btn_prev)
        
        self.playicon=True #initially we show the play icon (False means show Pause Icon)
        self.btn_play=ui.ImageButton(ui.Rect(120,88,64,64), self.img_play)
        self.btn_play.on_clicked.connect(self.button_click)
        self.btn_play.hidden=True #initially hidden
        self.add_child(self.btn_play)
        
        self.btn_next=ui.ImageButton(ui.Rect(220,88,64,64), self.img_next)
        self.btn_next.on_clicked.connect(self.button_click)
        self.btn_next.hidden=True #initially hidden
        self.add_child(self.btn_next)
        
        #create progress bar
        self.progress_view = ui.ProgressView(ui.Rect(0,231,320,9))
        self.add_child(self.progress_view)
        self.progress_view.hidden = True
   
    def set_now_playing_title(self, title):
        self.now_playing.text=title
        
    def new_card(self, card_id):
        self.last_action_ts=pygame.time.get_ticks()
        self.background.hidden=True
        self.background.image_view.image=ui.get_image(card_id,'/home/pi/music/images/')
        self.showing_splash=False #we no longer show the splash screen image
        self.background.hidden=False
        self.progress_view.hidden = False
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
        self.show_time=pygame.time.get_ticks() #refresh show time, so countdown restarts
        
        status=self.player.get_status()
        
        if btn is self.btn_play:
            logger.debug("button_click: btn_play ")
            player.pause()
        elif btn is self.btn_prev:
            try:
                if int(status['song']) > 0: #only accept 'prev' button push if this is not the first song
                    player.prev()
            except Exception as e:
                logger.error(e.args[0])
        
        elif btn is self.btn_next:
            try:
                if int(status['song']) < (int(status['playlistlength'])-1):
                    player.next()
            except Exception as e:
                logger.error(e.args[0])
                
        elif btn is self.background:
            logger.debug("button_click: background ")
            if self.now_playing.text != None:
                self.show_buttons()
        else:
            logger.debug("button_click: <unknown>")
            
    #update UI
    def update(self, dt):     
        try:
            status=player.get_status()
            currentsong=player.get_currentsong()

            #if self.now_playing.text != player.get_song_title():
            
            if 'title' in currentsong:
                self.now_playing.text = currentsong['title']
            else:
                self.now_playing.text = None
            
            
            #count idle time and shutdown if idle for longer thatn 120 seconds
            if status['state'] == 'play':
                self.last_action_ts=pygame.time.get_ticks()
                self.progress_view.progress=float(status['elapsed']) / float(currentsong['time'])
                logger.debug("progress: %s", float(status['elapsed']) / float(currentsong['time']))
            elif not self.showing_splash and self.now_playing.text == None:
                 self.background.image_view.image=ui.get_image('splash','/home/pi/music/images/')
                 self.progress_view.hidden = True
                 self.hide_buttons()
                
            if (pygame.time.get_ticks() - self.last_action_ts) > 180000:
                self.do_shutdown()
            
            #show buttons if they should be visible
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
        except Exception as e:
            logger.error(e.args[0])
	
    def signal_handler(self, signal, frame):
        logger.error("You pressed Ctrl+C!")
        ui.runui=False
        #sys.exit(0)

    def do_shutdown(self):
        #os.system("sudo shutdown -h now")
       self.shutdown=True
       ui.runui=False
        
        



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
    
    #shutdown procedure
    logger.debug("calling rfidreader.terminate()")
    rfidreader.terminate()
    logger.debug("calling player.close")
    player.close()
    logger.debug("calling pygame.quit")
    pygame.quit()
    
    if emscene.shutdown:
        time.sleep(1)
        command = "/usr/bin/sudo /sbin/shutdown -h now"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    
