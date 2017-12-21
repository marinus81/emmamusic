#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import pygameui as ui
import logging
import pygame
import signal
import threading
import time
from rfidreader import RFIDReader
import wiringpi2 as wiringpi
from player import Player
#from mpd import MPDClient
#from threading import Lock

# Init Display
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# Tell Pygame to not use any audio driver
os.environ["SDL_AUDIODRIVER"] = "none"

# init Logging
log_format = '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format))
logger = logging.getLogger()

# if program was started with --debug parameter, set logging level to DEBUG
if len(sys.argv) > 1 and sys.argv[1] == '--debug':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.ERROR)
logger.addHandler(console_handler)


# MARGIN = 20


class EmmaMusicScene(ui.Scene):
    """
    Emma Music Player Main UI Scene
    """

    shutdown = False  # if True will call OS shutdown command right before quitting
    DIM_BRIGHT=500
    DIM_DARK=150
    DIM_SHUT=20

    def __init__(self, player):
        """
        Class Initializer

        :param player: link to lockable MPD Client object used to communicate with MPD
        """
        ui.Scene.__init__(self)

        #setup LCD Light (GPIO 18 (PWM) is connected to LCD Backlight
        wiringpi.wiringPiSetupGpio()
        wiringpi.pinMode(18, wiringpi.PWM_OUTPUT)  # pwm only works on GPIO port 18


        # prepare signal handler for Ctrl+C and SIGTERM
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # init MPD Player Interface
        self.player = player
        self.player.link_scene(self)

        # init last action timestamp
        self.last_action_ts = pygame.time.get_ticks()

        # load images
        self.img_prev = ui.get_image('rewind-icon_s')
        self.img_play = ui.get_image('play-icon_s')
        self.img_pause = ui.get_image('pause-icon_s')
        self.img_next = ui.get_image('forward-icon_s')

        label_height = ui.theme.current.label_height
        scrollbar_size = ui.SCROLLBAR_SIZE

        # create menu
        # create background image
        self.showing_splash = True  # remember we show splash screen image
        self.background = ui.ImageButton(ui.Rect(0, 16, 320, 215), ui.get_image('splash', '/home/pi/music/images/'))
        self.background.on_clicked.connect(self.button_click)
        self.add_child(self.background)

        # create label for currently playing song
        self.now_playing = ui.Label(ui.Rect(0, 0, 320, label_height), '')
        self.add_child(self.now_playing)

        # create play control buttons (prev, play/pause, next)
        self.buttons_visible = False

        self.btn_prev = ui.ImageButton(ui.Rect(20, 88, 64, 64), self.img_prev)
        self.btn_prev.on_clicked.connect(self.button_click)
        self.btn_prev.hidden = True  # initially hidden
        self.add_child(self.btn_prev)

        self.playicon = True  # initially we show the play icon (False means show Pause Icon)
        self.btn_play = ui.ImageButton(ui.Rect(120, 88, 64, 64), self.img_play)
        self.btn_play.on_clicked.connect(self.button_click)
        self.btn_play.hidden = True  # initially hidden
        self.add_child(self.btn_play)

        self.btn_next = ui.ImageButton(ui.Rect(220, 88, 64, 64), self.img_next)
        self.btn_next.on_clicked.connect(self.button_click)
        self.btn_next.hidden = True  # initially hidden
        self.add_child(self.btn_next)

        # create progress bar
        self.progress_view = ui.ProgressView(ui.Rect(0, 231, 320, 9))
        self.add_child(self.progress_view)
        self.progress_view.hidden = True

        self.set_lcd_brightness(self.DIM_BRIGHT) #light LCD

    def set_now_playing_title(self, title):
        """
        Set the displayed title text

        :param title: title text to display
        :return:
        """
        self.now_playing.text = title

    def new_card(self, card_id):
        """
        A new RFID Card has been read by the rfid_reader and now we should play a new title

        :param card_id: the 4 byte ID of the RFID card in dotted decimal format. This will be the key to the playlist filename to play
        :return:
        """

        self.last_action_ts = pygame.time.get_ticks()
        # self.background.hidden=True
        self.background.image_view.image = ui.get_image(card_id, '/home/pi/music/images/')
        self.showing_splash = False  # we no longer show the splash screen image
        # self.background.hidden=False
        self.progress_view.hidden = False  # we play a song, so show progress bar
        self.show_buttons()  # show play controll buttons

    def set_background_image(self, imagename):
        """
        Set the backgroud image

        :param imagename: filename (without extension - .png will be added automatically) of image to show as background
        :return:
        """
        self.background.image = ui.get_image(imagename, '/home/pi/music/images/')

    def show_buttons(self):
        """
        Show playcontrol buttons

        :return:
        """
        self.show_time = pygame.time.get_ticks()  # remember time when we showed buttons, do this also if buttons
        # are already showing
        if not self.buttons_visible:
            self.btn_prev.hidden = False
            self.btn_play.hidden = False
            self.btn_next.hidden = False
            self.set_lcd_brightness(self.DIM_BRIGHT)
            self.buttons_visible = True

    def hide_buttons(self):
        """
        Hide playcontrol buttons

        :return:
        """
        if self.buttons_visible:
            self.btn_prev.hidden = True
            self.btn_play.hidden = True
            self.btn_next.hidden = True
            self.set_lcd_brightness(self.DIM_DARK)
            self.buttons_visible = False

    def button_click(self, btn, mbtn):
        """
        Event Handler for a "click" on one of the buttons

        :param btn: which button was "clicked"
        :param mbtn: not used (mouse button)
        :return:
        """
        self.last_action_ts = pygame.time.get_ticks()  # update last action timestamp (idle shutdown countdown restarts)
        self.show_time = pygame.time.get_ticks()  # refresh show time timestamp, so countdown restarts

        status = self.player.get_status()

        # which button was pressed?
        if btn is self.btn_play:
            logger.debug("button_click: btn_play ")
            player.pause()  # toggle play/pause
        elif btn is self.btn_prev:
            logger.debug("button_click: btn_prev ")
            try:
                if int(status['song']) > 0:  # only accept 'prev' button push if this is not the first song
                    player.prev()
            except Exception as e:
                logger.error(e, exc_info=True)  # log any exceptions
        elif btn is self.btn_next:
            logger.debug("button_click: btn_next ")
            try:
                if int(status['song']) < (int(status['playlistlength']) - 1):
                    player.next()
            except Exception as e:
                logger.error(e, exc_info=True)  # log any exceptions
        elif btn is self.background:
            logger.debug("button_click: background ")
            if status['state'] == 'play' or status['state']== 'pause':
                self.show_buttons()
        else:
            logger.debug("button_click: <unknown>")

    def update(self, dt):
        """
        update the UI - periodically called by main loop

        :param dt: time delta since last call
        :return:
        """

        try:
            status = player.get_status()  # get mpd status (playing, pause, etc.)
            currentsong = player.get_currentsong()  # get current playing title details (name, time, etc.)

            # Update song title display
            if 'title' in currentsong:
                self.now_playing.text = unicode(currentsong['title'], "utf-8")
            else:
                self.now_playing.text = u'Ü'.encode('utf-8') #None

            # if we are playing, update progress bar
            if status['state'] == 'play':
                self.last_action_ts = pygame.time.get_ticks()  # while we play a music, update last active timestamp (i.e do not shutdown while playing)
                progress = float(status['elapsed']) / float(currentsong['time'])
                logger.debug("progress: {}".format(progress))
                self.progress_view.progress = progress if (
                    progress <= 1.0) else 1.0  # necessary due to precission issues at the end of a song
            elif status['state'] == 'pause':
                pass        #do not update if paused
            elif not self.showing_splash and self.now_playing.text == None:
                # no song playing and not yet showing splash screen - load it and show it!
                self.background.image_view.image = ui.get_image('splash', '/home/pi/music/images/')
                self.progress_view.hidden = True
                self.showing_splash = True
                self.hide_buttons()  # hide play buttons as we don't play any song

            # shutdown if idle for longer thatn 180 seconds
            if (pygame.time.get_ticks() - self.last_action_ts) > 180000:
                self.do_shutdown()

            # update play/pause, etc. buttons if they should be visible
            if self.buttons_visible:
                logger.debug("Status: %s, playicon= %s" % (status['state'], self.playicon))
                if status['state'] != 'play' and self.playicon:  # not playing, but showing play icon - display pause
                    self.btn_play.image_view.image = self.img_pause
                    self.playicon = not self.playicon
                elif status['state'] == 'play' and not self.playicon:  # other way around
                    self.btn_play.image_view.image = self.img_play
                    self.playicon = not self.playicon

                if (
                            pygame.time.get_ticks() - self.show_time) > 5000:  # if some time has passed without any touch event, hide buttons
                    self.hide_buttons()

            ui.Scene.update(self,
                            dt)  # call parent (do we want to catch exceptions there - should be moved outside of try block?)
        except Exception as e:
            logger.error(e, exc_info=True)  # log any exceptions

    def signal_handler(self, signal, frame):
        """
        Handle any signals (SIGTERM, SIGHUP, etc.)

        :param signal:
        :param frame:
        :return:
        """
        logger.error("Received Signal to Terminate")
        self.set_lcd_brightness(self.DIM_SHUT)
        ui.runui = False
        # sys.exit(0)

    def do_shutdown(self):
        """
        Terminate this program and shutdown system afterwards

        :return:
        """
        self.set_lcd_brightness(self.DIM_SHUT)
        self.shutdown = True
        ui.runui = False

    def set_lcd_brightness(self, dc):
        """
        Set LCD Screen brightnes.

        :param dc: duty cycle for PWM PIN (GPIO 18). 0 is off, 1023 is fully on
        :return:
        """

        if 0 <= dc < 1024:
            logging.debug("Setting LCD Brightnes to {}".format(dc))
            wiringpi.pwmWrite(18, dc)  # duty cycle between 0 and 1024. 0 = off, 1023 = fully on
        else:
            logging.error("Invalid duty cycle for LCD Brightnes {}".format(dc))


if __name__ == '__main__':

    player = Player()  # create new player object (Lockable MPDClient)

    ui.init('Raspberry Pi UI', (320, 240))  # init PiTFT UI and hide mouse icon
    pygame.mouse.set_visible(False)

    emscene = EmmaMusicScene(player)  # create new UI Scene, and pass reference to player object

    # start RFID Reader Thread
    rfidreader = RFIDReader(emscene,
                            player)  # holds reference to UI for any updates and player to see directly launch a title TODO: can probably be simplified
    threading.Thread(target=rfidreader).start()

    ui.scene.push(emscene)  # put UI on the screen
    ui.run()  # run main loop

    # shutdown procedure
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
