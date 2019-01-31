#!/usr/bin/env python

'''

   Phase-0 Daily data process

'''

__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import os, time, datetime

yesterday = datetime.datetime.utcfromtimestamp(time.time())

while True:
    today = datetime.datetime.utcfromtimestamp(time.time())
    if not yesterday.day == today.day:
        data = yesterday.strftime("%Y-%m-%d")
        yesterday = datetime.datetime.utcfromtimestamp(time.time())
        os.system("./transfer.py --data=" + data)
        for band in range(0, 400, 50):
            os.system("./transfer.py --data=" + data + "  --notrigger --novideo --start-freq=" + str(
                band) + " --stop-freq=" + str(band + 50))
    else:
        print "Actual time is " + str(today) + ", waiting for the next day..."
        time.sleep(60 * 60)
