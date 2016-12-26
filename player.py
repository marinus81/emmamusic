#!/usr/bin/env python
# encoding: utf-8

"""
player.py

The audio player. A simple wrapper around the MPD client. Uses a lockable version
of the MPD client object, because we're using multiple threads
"""


__version_info__ = (0, 0, 2)
__version__ = '.'.join(map(str, __version_info__))
__author__ = "David Hamann based on work of Willem van der Jagt"
import time
import logging



from mpd import *
from threading import Lock

logger = logging.getLogger()



class LockableMPDClient(MPDClient):
    def __init__(self, use_unicode=False):
        super(LockableMPDClient, self).__init__()
        self.use_unicode = use_unicode
        self._lock = Lock()
    def acquire(self):
        self._lock.acquire()
    def release(self):
        self._lock.release()
    def __enter__(self):
        self.acquire()
    def __exit__(self, type, value, traceback):
        self.release()


class Player(object):

    """The class responsible for playing audio"""

    def __init__(self):
        """Setup a connection to MPD to be able to play audio.

        Also update the MPD database with any new MP3 files that may have been added
        and clear any existing playlists.
        """

        logger.debug("Player INIT")
        self.mpd_client = LockableMPDClient()
        self.conn_details={ "host" : "localhost", "port" : 6600 }
        self.init_mpd()
        
        self.songtitle=""
        self.em_scene=""
        
    def link_scene(self, scene):
        self.em_scene=scene

                
    def init_mpd(self):
        try:
            print "Connecting to MPD."
            with self.mpd_client:
                self.mpd_client.connect(**self.conn_details)

                self.mpd_client.update()
                self.mpd_client.clear()
                #self.mpd_client.setvol(100)
        except:
            print "Connection to MPD failed. Trying again in 10 seconds."
            time.sleep(10)
            self.init_mpd(conn_details)

    def connect_mpd(self):
        try:
            self.mpd_client.connect(**self.conn_details)
        except ConnectionError as e:
            logger.debug("ConnectionError Exception: "+e.args[0])
            if e.args[0] == "Already connected":
                logger.debug("Already connected")
            else:
                logger.error("Failed to Connect to MPD")


    def stop(self):
        """On stopping, reset the current playback and stop and clear the playlist

        In contract to pausing, stopping is actually meant to completely stop playing
        the current book and start listening to another"""

      
        with self.mpd_client:
            self.mpd_client.stop()
            self.mpd_client.clear()


    def play(self,playlistname, progress=None, retry=0):
        """Play a playlist"""
 
       
            
        #order of try and with is important - otherwise retry will block due to Locking   
        try:
            with self.mpd_client:    
                self.mpd_client.clear()
                self.mpd_client.load(playlistname)
           
                if progress:
                    # resume at last known position
                    self.mpd_client.seek(progress)
                else: 
                    # start playing from the beginning
                    self.mpd_client.play()
                 
                self.em_scene.new_card(playlistname)
                
                info=self.mpd_client.currentsong()
                print(info)
                if 'title' in info:
                    self.songtitle=info['title']
        except ConnectionError as e:
            if retry < 3:
                logger.debug("play: connection Error - "+e.args[0]+" - retry")
                self.connect_mpd()
                self.play(playlistname,progress,retry+1)
        #except Exception as e:
        #   logger.error("Could not play playlist: "+playlistname+"Error: %s" % e.args[0])
 
    def pause(self):
        with self.mpd_client:
            self.mpd_client.pause()
    
    def get_status(self):
        with self.mpd_client:
            return self.mpd_client.status()
            
    def next(self):
        with self.mpd_client:
            if self.mpd_client.status()['playlistlength'] > 1:
                self.mpd_client.next()
    
    def prev(self):
        with self.mpd_client:
            if self.mpd_client.status()['playlistlength'] > 1:
                self.mpd_client.previous()


    def get_file_info(self):
        with self.mpd_client:
            return self.mpd_client.currentsong()
    
    def get_song_title(self):
        return self.songtitle

    def close(self):
        self.stop()
        time.sleep(0.5)
        self.mpd_client.close()
        time.sleep(0.5)
        self.mpd_client.disconnect()
