#!/usr/bin/env python
"""

  Send Slack Messages

  example:
        from aavsSlack import aavsSlack
        slack = aavsSlack()
        slack.chat("Hello world!")

"""
from slacker import Slacker
import os
import urllib3
urllib3.disable_warnings()

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2020, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

defaultPath = "/opt/aavs/slack/"


class aavsSlack():
    def __init__(self, token="", channel="#aavs-notifications", station="AAVS2", verbose=False):
        if not token:
            if os.path.exists(defaultPath + station):
                with open(defaultPath + station) as f:
                    tok = f.readline()
                if tok[-1] == "\n":
                    tok = tok[:-1]
            self.token = tok
        else:
            self.token = token
        self.channel = channel
        if verbose:
            print("Slack object created, channel: " + self.channel + ", token: " + self.token)
        try:
            self.slack = Slacker(self.token)
        except:
            if verbose:
                msg = "Not a valid token: " + self.token
                print(msg)

    def chat(self, message, verbose=False):
        try:
            if verbose:
                print("Sending message to ")
            self.slack.chat.post_message(self.channel, message, as_user=True)
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
