from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import sys, os, glob
#import matplotlib
#if not 'matplotlib.backends' in sys.modules:
#    matplotlib.use('agg') # not to use X11from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import matplotlib.pyplot as plt
import numpy as np
import calendar
from pyaavs import station
from time import sleep
import datetime, time
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from aavs_calibration.common import get_antenna_positions, get_antenna_tile_names

# Global flag to stop the scrpts
FIG_W = 14
TILE_H = 3.2
PIC_PATH = "/storage/monitoring/pictures"
TEXT_PATH = "/storage/monitoring/text_data"
ERASE_LINE = '\x1b[2K'

def _connect_station(aavs_station):
    """ Return a connected station """
    # Connect to station and see if properly formed
    while True:
        try:
            aavs_station.check_station_status()
            if not aavs_station.properly_formed_station:
                raise Exception
            break
        except:
            sleep(60) 
            try:
                aavs_station.connect()
            except:
                continue


def dt_to_timestamp(d):
    return calendar.timegm(d.timetuple())


def fname_to_tstamp(date_time_string):
    time_parts = date_time_string.split('_')
    d = datetime.datetime.strptime(time_parts[0], "%Y%m%d")  # "%d/%m/%Y %H:%M:%S"
    timestamp = calendar.timegm(d.timetuple())
    timestamp += int(time_parts[1]) - (60 * 60 * 8)
    return timestamp


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def tstamp_to_fname(timestamp=None):
    """
    Returns a string date/time from a UNIX timestamp.
    :param timestamp: A UNIX timestamp.
    :return: A date/time string of the form yyyymmdd_secs
    """
    if timestamp is None:
        timestamp = 0

    datetime_object = datetime.datetime.utcfromtimestamp(timestamp)
    hours = datetime_object.hour
    minutes = datetime_object.minute
    seconds = datetime_object.second
    full_seconds = seconds + (minutes * 60) + (hours * 60 * 60)
    full_seconds_formatted = format(full_seconds, '05')
    base_date_string = datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y%m%d')
    full_date_string = base_date_string + '_' + str(full_seconds_formatted)
    return str(full_date_string)

