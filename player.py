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
    """
    Simple implementation of a thread safe version of the MPDCLient Class
    """

    def __init__(self, use_unicode=False):
        """
        Constructor

        :param use_unicode: to be removed (not used)
        """
        super(LockableMPDClient, self).__init__()
        self.use_unicode = use_unicode
        self._lock = Lock()

    def acquire(self):
        """
        Accquire the Lock

        :return:
        """
        self._lock.acquire()

    def release(self):
        """
        Release the Lock

        :return:
        """
        self._lock.release()

    def __enter__(self):
        """
        Accquire the Lock if used in with block

        :return:
        """
        self.acquire()

    def __exit__(self, type, value, traceback):
        """
        Release the Lock at the end of with block. No Error handling done here in case of exception

        :param type:
        :param value:
        :param traceback:
        :return:
        """
        self.release()


class Player(object):
    """The class responsible for playing audio"""
    current_playlistname = 'init'

    def __init__(self):
        """Setup a connection to MPD to be able to play audio.

        Also update the MPD database with any new MP3 files that may have been added
        and clear any existing playlists.
        """

        logger.debug("Player INIT")
        self.mpd_client = LockableMPDClient()
        self.conn_details = {"host": "localhost", "port": 6600}
        self.init_mpd()

        self.em_scene = None

    def link_scene(self, scene):
        """
        Create a back link to the UI Scene object
        :param scene:
        :return:
        """
        self.em_scene = scene

    def init_mpd(self):
        """
        Initialize the MPDClient Object

        :return:
        """
        try:
            logger.debug("Connecting to MPD.")
            with self.mpd_client:
                self.mpd_client.connect(**self.conn_details)

                self.mpd_client.update()
                self.mpd_client.clear()
                # self.mpd_client.setvol(100)
        except:
            logger.error("Connection to MPD failed. Trying again in 10 seconds.")
            time.sleep(10)
            self.init_mpd(conn_details)

    def connect_mpd(self):
        """
        Connect MPD Client to MPD Server

        :return:
        """
        try:
            self.mpd_client.connect(**self.conn_details)
        except ConnectionError as e:
            logger.debug("ConnectionError Exception: " + e.args[0])
            if e.args[0] == "Already connected":
                logger.debug("Already connected")
            else:
                logger.error("Failed to Connect to MPD")

    def stop(self):
        """
        On stopping, reset the current playback and stop and clear the playlist

        :return:
        """
        with self.mpd_client:
            self.mpd_client.stop()
            self.mpd_client.clear()

    def play(self, playlistname, retry=0):
        """
        Play a playlist

        :param playlistname: play the playlist with this name
        :param retry:  retry count (used for recursive calling of this method - stop after a certian amount of retries)
        :return:
        """

        # order of try and with is important - otherwise retry will block due to Locking
        try:
            with self.mpd_client:
                if not (self.mpd_client.status()['state'] == 'play' and self.current_playlistname == playlistname):
                    self.current_playlistname = playlistname
                    self.mpd_client.clear()
                    self.mpd_client.load(playlistname)

                    # start playing from the beginning
                    self.mpd_client.play()

                    self.em_scene.new_card(playlistname)
                logger.debug("Status: %s" % self.mpd_client.status())
                logger.debug("currentsong: %s" % self.mpd_client.currentsong())
        except ConnectionError as e:
            if retry < 3:
                logger.debug("play: connection Error - " + e.args[0] + " - retry")
                self.connect_mpd()
                self.play(playlistname, retry + 1)
            else:
                logger.error("player.play(): cannot connect to MPD after 3 retries")
                # except Exception as e:
                #   logger.error("Could not play playlist: "+playlistname+"Error: %s" % e.args[0])

    def pause(self):
        """
        Toggle Play Pause of MPD

        :return:
        """
        with self.mpd_client:
            self.mpd_client.pause()

    def get_status(self):
        """
        Get current MPD Status

        :return: Dictionary of MPD Status Information
        """
        with self.mpd_client:
            return self.mpd_client.status()

    def get_currentsong(self):
        """
        Get Details on currently playing song

        :return: Dictionary of currently playing song details (title, time, etc.)
        """
        with self.mpd_client:
            return self.mpd_client.currentsong()

    def next(self):
        """
        Play next title in playlist

        :return:
        """
        with self.mpd_client:
            if self.mpd_client.status()['playlistlength'] > 1:
                self.mpd_client.next()
                logger.debug("Status: %s" % self.mpd_client.status())
                logger.debug("currentsong: %s" % self.mpd_client.currentsong())

    def prev(self):
        """
        Play previous Title in playlist

        :return:
        """
        with self.mpd_client:
            if self.mpd_client.status()['playlistlength'] > 1:
                self.mpd_client.previous()
                logger.debug("Status: %s" % self.mpd_client.status())
                logger.debug("currentsong: %s" % self.mpd_client.currentsong())


    def close(self):
        """
        Close connection to MPD Server

        :return:
        """
        logger.debug("player.close()")
        logger.debug("calling self.stop()")
        self.stop()
        time.sleep(0.5)
        logger.debug("trying to get lock (with self.mpd_client:)")
        with self.mpd_client:
            logger.debug("calling  self.mpd_client.close()")
            self.mpd_client.close()
            time.sleep(0.5)
            logger.debug("calling  self.mpd_client.disconnect()")
            self.mpd_client.disconnect()
