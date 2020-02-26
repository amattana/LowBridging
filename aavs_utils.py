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


def eq_retta(x1, y1, x2, y2):
    m = float((y2 - y1) / ( x2 - x1))
    q = y1 - (m * x1)

    def retta(x):
        return m * x + q
    return retta


def calc_value(serie_x, serie_y, x):
    print "   -  ", ts_to_datestring(serie_x[0]), serie_x[0]
    x1 = closest(np.array(serie_x), x)
    if x1 >= len(serie_x)-1:
        x1 = len(serie_x)-2
    x2 = x1 + 1
    print " * ", len(serie_x), len(serie_y), x1, x2, ts_to_datestring(serie_x[x1]), serie_x[x1]
    return eq_retta(x1, serie_y[x1], x2, serie_y[x2])(x)


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


def mro_daily_weather(fname="/storage/monitoring/weather/MRO_WEATHER.csv", date="", start="", stop=""):
    records = []
    units = {}

    try:
        if date:
            t_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            t_start = int(time.mktime(t_date.timetuple())) + (60 * 60 * 8) # Fix Weather data written in WA Local Time
            t_stop = int(time.mktime(t_date.timetuple()) + (60 * 60 * 24)) + (60 * 60 * 8) # Fix Weather data written in WA Local Time

        elif start and stop:
            t_start = int(time.mktime(datetime.datetime.strptime(start, "%Y-%m-%d_%H:%M:%S").timetuple())) + (60 * 60 * 8)  # Fix Weather data written in WA Local Time
            t_stop = int(time.mktime(datetime.datetime.strptime(stop, "%Y-%m-%d_%H:%M:%S").timetuple())) + (60 * 60 * 8)  # Fix Weather data written in WA Local Time
        else:
            print "Missing time argument (date | start,stop)"
            return units, records

    except ValueError:
        print "Wrong date format, expected %Y-%m-%d"
        return units, records

    #print "Looking for data between", t_start, "and", t_stop
    if os.path.exists(fname):
        with open(fname) as f:
            data = f.readlines()
        if len(data) > 4:
            units['time'] = "sec"
            units['temp'] = data[3].split(",")[1][1:].split(" ")[-1][1:-1]
            units['wind'] = data[3].split(",")[3][1:].split(" ")[-1][1:-1]
            units['wdir'] = "deg"
            units['rain'] = data[3].split(",")[6][1:].split(" ")[-1][1:-1]
            for d in data[4:]:
                t_stamp = int(time.mktime(datetime.datetime.strptime(d.split(",")[0],
                               "%Y-%m-%d %H:%M:%S").timetuple()))
                if t_start <= t_stamp <= t_stop:
                    dati = {}
                    dati['time'] = t_stamp
                    dati['temp'] = float(d.split(",")[1])
                    dati['wind'] = float(d.split(",")[3])
                    dati['wdir'] = int(d.split(",")[5])
                    dati['rain'] = float(d.split(",")[6])
                    records += [dati]
    return units, records


def diclist_to_array(dic, key):
    lista = []
    for d in dic:
        lista += [d[key]]
    return lista

