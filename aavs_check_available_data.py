from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import sys
import matplotlib
if not 'matplotlib.backends' in sys.modules:
    matplotlib.use('agg') # not to use X11from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import matplotlib.pyplot as plt
import numpy as np
from pyaavs import station
from time import sleep
import glob
import datetime
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from aavs_calibration.common import get_antenna_positions, get_antenna_tile_names

# Global flag to stop the scrpts
FIG_W = 14
TILE_H = 3.2
DATA_PATH = "/storage/monitoring/integrated_data/"

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


def totimestamp(dt, epoch=datetime.datetime(1970, 1, 1, 8, 0, 0)):
    h = int(int(dt[9:]) / 3600)
    m = int((int(dt[9:]) % 3600) / 60)
    s = int((int(dt[9:]) % 3600) % 60)
    a = datetime.datetime(int(dt[0:4]), int(dt[4:6]), int(dt[6:8]), h, m, s)
    td = a - epoch
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6


def todatestring(tstamp):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), "%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %monitor_bandpasses [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs2.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS1)")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data/",
                      help="Directory where plots will be generated (default: /storage/monitoring/integrated_data)")
    parser.add_option("--tile", action="store", dest="tile", type=int,
                      default=1, help="Tile Number")
    parser.add_option("--skip", action="store", dest="skip", type=int,
                      default=-1, help="Skip N blocks")
    parser.add_option("--start", action="store", dest="start",
                      default="", help="Start time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--stop", action="store", dest="stop",
                      default="", help="Stop time for filter (YYYY-mm-DD_HH:MM:SS)")

    (opts, args) = parser.parse_args(argv[1:])

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']
    print "Station Name: ", station_name
    print "Checking directory: ", opts.directory+station_name
    file_manager = ChannelFormatFileManager(root_path=opts.directory+station_name, daq_mode=FileDAQModes.Integrated)

    lista = glob.glob(DATA_PATH + station_name.lower() + "/channel_integ_%d_*hdf5"%(int(opts.tile)-1))
    for l in lista:
        print l[-21:-7],
        dic = file_manager.get_metadata(timestamp=totimestamp(l[-21:-7]), tile_id=int(opts.tile)-1)
        if not dic == None:
            data, timestamps = file_manager.read_data(timestamp=totimestamp(l[-21:-7]), tile_id=int(opts.tile)-1, n_samples=dic['n_blocks'])
            print "\t", todatestring(timestamps[0][0]), "\t", todatestring(timestamps[-1][0]), "\t", dic['n_blocks']
        else:
            print " no metadata available"


