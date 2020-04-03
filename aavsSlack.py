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
__version__ = "1.1"
__maintainer__ = "Andrea Mattana"

defaultPath = "/opt/aavs/slack/"


class aavsSlack():
    def __init__(self, token="", channel="#aavs-notifications", station="AAVS2", tokenPath="", verbose=False):
        self.station = station.upper()
        self.channel = channel
        if token:
            self.token = token
        else:
            if tokenPath:
                tokenFile = tokenPath
            else:
                tokenFile = defaultPath + self.station
            if os.path.exists(tokenFile):
                with open(tokenFile) as f:
                    tok = f.readline()
                if tok[-1] == "\n":
                    tok = tok[:-1]
            self.token = tok
        if verbose:
            print("Slack object created, channel: " + self.channel + ", token: " + self.token)
        try:
            self.slack = Slacker(self.token)
        except:
            if verbose:
                msg = "Not a valid token: " + self.token
                print(msg)

    def _chat(self, message, verbose=False):
        try:
            if verbose:
                print("Sending message to ")
            msg = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%d %H:%M:%S  " + message)
            self.slack.chat.post_message(self.channel, msg, as_user=True)
        except "not_in_channel":
            if verbose:
                msg = "The Bot is not in channel " + self.channel
                print(msg)
            pass
        except:
            if verbose:
                msg = "Slack Exception: Channel: " + self.channel + ", Msg: " + message + ", Token: " + self.token
                print(msg)
            pass

    def info(self, m="", v=False):
        self._chat(message=" - INFO - "+m, verbose=v)

    def warning(self, m="", v=False):
        self._chat(message=" - WARNING - "+m, verbose=v)

    def error(self, m="", v=False):
        self._chat(message=" - ERROR - "+m, verbose=v)

