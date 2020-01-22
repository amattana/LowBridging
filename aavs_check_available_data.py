from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import sys
import matplotlib
if not 'matplotlib.backends' in sys.modules:
    matplotlib.use('agg') # not to use X11from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import matplotlib.pyplot as plt
import numpy as np
from pyaavs import station
import time
import glob
import datetime
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from aavs_calibration.common import get_antenna_positions, get_antenna_tile_names


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


# def totimestamp(dt, epoch=datetime.datetime(1970, 1, 1, 8, 0, 0)):
#     h = int(int(dt[9:]) / 3600)
#     m = int((int(dt[9:]) % 3600) / 60)
#     s = int((int(dt[9:]) % 3600) % 60)
#     a = datetime.datetime(int(dt[0:4]), int(dt[4:6]), int(dt[6:8]), h, m, s)
#     td = a - epoch
#     return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6


def totstamp(date_time_string):
    time_parts = date_time_string.split('_')
    d = datetime.datetime.strptime(time_parts[0], "%Y%m%d")  # "%d/%m/%Y %H:%M:%S"
    timestamp = time.mktime(d.timetuple())
    timestamp += int(time_parts[1])
    return timestamp


def todatestring(tstamp):
    return datetime.datetime.strftime(datetime.datetime.fromtimestamp(tstamp), "%Y-%m-%d %H:%M:%S")


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
    parser.add_option("--date", action="store", dest="date",
                      default="", help="Stop time for filter (YYYY-mm-DD)")

    (opts, args) = parser.parse_args(argv[1:])

    t_date = None
    t_start = None
    t_stop = None
    t_cnt = 0

    if opts.date:
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
            t_start = totstamp(datetime.datetime.strftime(t_date, "%Y%m%d_00000"))
            t_stop = totstamp(datetime.datetime.strftime(t_date, "%Y%m%d_00000")) + (60 * 60 * 24)
        except:
            print "Bad date format detected (must be YYYY-MM-DD)"
    else:
        if opts.start:
            try:
                t_start = totstamp(datetime.datetime.strptime(opts.start, "%Y-%m-%d_%H:%M:%S"))
            except:
                print "Bad t_start time format detected (must be YYYY-MM-DD_HH:MM:SS)"
        if opts.stop:
            try:
                t_stop = totstamp(datetime.datetime.strptime(opts.stop, "%Y-%m-%d_%H:%M:%S"))
            except:
                print "Bad t_stop time format detected (must be YYYY-MM-DD_HH:MM:SS)"

    # print t_date, t_start, t_stop

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']
    print "\nStation Name: ", station_name
    print "Checking directory: ", opts.directory+station_name.lower() + "\n"
    file_manager = ChannelFormatFileManager(root_path=opts.directory+station_name.lower(), daq_mode=FileDAQModes.Integrated)
    #file_manager = ChannelFormatFileManager(root_path="/storage/monitoring/integrated_data/aavs2", daq_mode=FileDAQModes.Integrated)
    lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d_*hdf5"%(int(opts.tile)-1)))
    for l in lista:
        dic = file_manager.get_metadata(timestamp=totstamp(l[-21:-7]), tile_id=(int(opts.tile)-1))
        if dic:
            data, timestamps = file_manager.read_data(timestamp=totstamp(l[-21:-7]), tile_id=int(opts.tile)-1,
                                                      n_samples=dic['n_blocks'])
            cnt = 0
            for i, t in enumerate(timestamps):
                if t_start <= t[0] <= t_stop:
                    cnt = cnt + 1
                    t_cnt = t_cnt + 1
                    #print l[-21:-7], t[0], todatestring(t[0]), cnt
            print l[-21:-7], "\t", todatestring(timestamps[0][0]), "\t", todatestring(timestamps[-1][0]), "\t", cnt
        else:
            print l[-21:-7], ": no metadata available"

    print "\nFound %d measurements\n" % t_cnt



