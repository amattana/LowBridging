#!/usr/bin/env python
"""

  Send Slack Messages

  example:
        from aavsSlack import aavsSlack
        slack = aavsSlack(token="", channel="#aavs-notifications", station="AAVS2", tokenPath="", verbose=False)
        slack.info("Hello world!")
        slack.warning("Ops!")
        slack.error("OMG!")



"""
from slacker import Slacker
import os
import datetime
import urllib3
urllib3.disable_warnings()

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2020, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.2"
__maintainer__ = "Andrea Mattana"

defaultPath = "/opt/aavs/slack/"


class aavsSlack():
    def __init__(self, token="", channel="#aavs-notifications", station="AAVS2", tokenPath="", verbose=False):
        self.station = station.upper()
        self.channel = channel
        self.token = token
        self.verbose = verbose
        self.tokenFile = tokenPath
        if not self.tokenFile:
            if not self.tokenFile:
                self.tokenFile = defaultPath + self.station
            if os.path.exists(self.tokenFile):
                with open(self.tokenFile) as f:
                    self.token = f.readline()
                if self.token[-1] == "\n":
                    self.token = self.token[:-1]
        if self.verbose:
            print("Slack object created, channel: " + self.channel + ", token: " + self.token)
        try:
            if self.token:
                self.slack = Slacker(self.token)
            else:
                self.slack = None
        except:
            if self.verbose:
                msg = "Not a valid token: " + self.token
                print(msg)

    def _chat(self, message, verbose=False):
        try:
            if self.verbose or verbose:
                print("Sending message to ")
            msg = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%d %H:%M:%S  " + message)
            if self.token:
                self.slack.chat.post_message(self.channel, msg, as_user=True)
        except "not_in_channel":
            if self.verbose or verbose:
                msg = "The Bot is not in channel " + self.channel
                print(msg)
            pass
        except:
            if self.verbose or verbose:
                msg = "Slack Exception: Channel: " + self.channel + ", Msg: " + message + ", Token: " + self.token
                print(msg)
            pass

    def info(self, m="", v=False):
        self._chat(message=" - INFO - "+m, verbose=v)

    def warning(self, m="", v=False):
        self._chat(message=" - WARNING - "+m, verbose=v)

    def error(self, m="", v=False):
        self._chat(message=" - ERROR - "+m, verbose=v)

