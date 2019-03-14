#!/usr/bin/env python

'''

  Send Slack Messages to #ska-low-bridging

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import urllib3
# Test application, security unimportant:
urllib3.disable_warnings()


from slacker import Slacker
slack = Slacker("xoxb-576613474708-574252753088-sSeV7bNIQoq2AswUVr4YFzhE")
slack.chat.post_message("ska-low-bridging", "A message from me :grin: (ciao)", as_user=True)

