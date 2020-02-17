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


def find_ant_by_name(antenna):
    with open("aavs_map.txt") as fmap:
        records = fmap.readlines()
    for r in records:
        if int(r.split()[2]) == antenna:
            return int(r.split()[0]), int(r.split()[1])
    return 0, 0


def find_pos_by_name(antenna):
    with open("aavs_map.txt") as fmap:
        records = fmap.readlines()
    for r in records:
        if int(r.split()[2]) == antenna:
            return float(r.split()[4]), float(r.split()[3])
    return -20, -20


def find_ant_by_tile(gruppo, inp):
    with open("aavs_map.txt") as fmap:
        records = fmap.readlines()
    for r in records:
        if int(r.split()[0]) == gruppo and int(r.split()[1]) == inp:
            return int(r.split()[2])
    return 0


def find_ants_by_tile(gruppo):
    antenne = []
    with open("aavs_map.txt") as fmap:
        records = fmap.readlines()
    for r in records:
        if int(r.split()[0]) == gruppo:
            antenne += [int(r.split()[2])]
    return antenne


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


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


def dB2Linear(valueIndB):
    """
    Convert input from dB to linear scale.
    Parameters
    ----------
    valueIndB : float | np.ndarray
        Value in dB
    Returns
    -------
    valueInLinear : float | np.ndarray
        Value in Linear scale.
    Examples
    --------
    #>>> dB2Linear(30)
    1000.0
    """
    return pow(10, valueIndB / 10.0)


def linear2dB(valueInLinear):
    """
    Convert input from linear to dB scale.
    Parameters
    ----------
    valueInLinear : float | np.ndarray
        Value in Linear scale.
    Returns
    -------
    valueIndB : float | np.ndarray
        Value in dB scale.
    Examples
    --------
    #>>> linear2dB(1000)
    30.0
    """
    return 10.0 * np.log10(valueInLinear)


def dBm2Linear(valueIndBm):
    """
    Convert input from dBm to linear scale.
    Parameters
    ----------
    valueIndBm : float | np.ndarray
        Value in dBm.
    Returns
    -------
    valueInLinear : float | np.ndarray
        Value in linear scale.
    Examples
    --------
    #>>> dBm2Linear(60)
    1000.0
    """
    return dB2Linear(valueIndBm) / 1000.


def linear2dBm(valueInLinear):
    """
    Convert input from linear to dBm scale.
    Parameters
    ----------
    valueInLinear : float | np.ndarray
        Value in Linear scale
    Returns
    -------
    valueIndBm : float | np.ndarray
        Value in dBm.
    Examples
    --------
    #>>> linear2dBm(1000)
    60.0
    """
    return linear2dB(valueInLinear * 1000.)

def calcSpectra(vett):
    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett * window)
    N = len(spettro)
    acf = 2  # amplitude correction factor
    spettro[:] = abs((acf * spettro) / N)
    # print len(vett), len(spettro), len(np.real(spettro))
    return (np.real(spettro))


def calcolaspettro(dati, nsamples=131072):
    n = nsamples  # split and average number, from 128k to 16 of 8k # aavs1 federico
    sp = [dati[x:x + n] for x in xrange(0, len(dati), n)]
    mediato = np.zeros(len(calcSpectra(sp[0])))
    for k in sp:
        singolo = calcSpectra(k)
        mediato[:] += singolo
    # singoli[:] /= 16 # originale
    mediato[:] /= (2 ** 17 / nsamples)  # federico
    with np.errstate(divide='ignore', invalid='ignore'):
        mediato[:] = 20 * np.log10(mediato / 127.0)
    return mediato


