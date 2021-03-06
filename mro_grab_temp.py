#!/usr/bin/env python

'''

   MRO Grab Temperatures from OZ Forecast website that prints MRO Weather Station Data

'''

__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

from urllib2 import urlopen
import datetime, time, os
from BeautifulSoup import BeautifulSoup
epoch = datetime.datetime(1970, 1, 1)


def toTimestamp(t):
    dt = t - epoch
    return (dt.microseconds + (dt.seconds + dt.days * 86400) * 10**6) / 10**6

BASE_DIR = "/data/data_2/2018-11-LOW-BRIDGING/"
TEMP_DIR = "WEATHER/TEMP/"
url = "http://ozforecast.com.au/cgi-bin/weatherstation.cgi?station=11004"
if not os.path.isdir(BASE_DIR):
    os.makedirs(BASE_DIR)

if not os.path.isdir(BASE_DIR+"WEATHER"):
    os.makedirs(BASE_DIR+"WEATHER")

if not os.path.isdir(BASE_DIR+TEMP_DIR):
    os.makedirs(BASE_DIR+TEMP_DIR)

while True:
    soup = BeautifulSoup(urlopen(url).read())
    table = soup.findAll("table", "ozf")

    record = table[2].findAll('tr')[1:][0].findAll("td")
    d = str(soup.findAll("b")[2].text.split()[-2])
    t = int(record[0].text.split()[1].split(":")[0]) * 60 * 60 + int(record[0].text.split()[1].split(":")[1]) * 60
    data = datetime.datetime.strptime(d, "%Y-%m-%d") + datetime.timedelta(0, t)
    data = data - datetime.timedelta(0, 3600*8) # Converting in UTC (GMT+8)
    temp = float(record[1].text)
    fname = "/data/data_2/2018-11-LOW-BRIDGING/WEATHER/TEMP/"
    fname += datetime.datetime.strftime(data, "%Y-%m-%d.txt")
    with open(fname, "a") as f:
        f.write("%d\t%3.1f\n"%(toTimestamp(data), temp))
    print "%d\t%3.1f"%(toTimestamp(data), temp)
    time.sleep(15*60)

