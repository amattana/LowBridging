from pydaq.persisters import ChannelFormatFileManager, FileDAQModes, RawFormatFileManager
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
from aavs_utils import ts_to_datestring, tstamp_to_fname, dt_to_timestamp, fname_to_tstamp
import os


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


# def dt_to_timestamp(d):
#     return time.mktime(d.timetuple())
#
#
# def fname_to_tstamp(date_time_string):
#     time_parts = date_time_string.split('_')
#     d = datetime.datetime.strptime(time_parts[0], "%Y%m%d")  # "%d/%m/%Y %H:%M:%S"
#     timestamp = time.mktime(d.timetuple())
#     timestamp += int(time_parts[1])
#     return timestamp
#
#
# def ts_to_datestring(tstamp):
#     return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), "%Y-%m-%d %H:%M:%S")
#
#
# def tstamp_to_fname(timestamp=None):
#     """
#     Returns a string date/time from a UNIX timestamp.
#     :param timestamp: A UNIX timestamp.
#     :return: A date/time string of the form yyyymmdd_secs
#     """
#     if timestamp is None:
#         timestamp = 0
#
#     datetime_object = datetime.datetime.fromtimestamp(timestamp)
#     hours = datetime_object.hour
#     minutes = datetime_object.minute
#     seconds = datetime_object.second
#     full_seconds = seconds + (minutes * 60) + (hours * 60 * 60)
#     full_seconds_formatted = format(full_seconds, '05')
#     base_date_string = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d')
#     full_date_string = base_date_string + '_' + str(full_seconds_formatted)
#     return str(full_date_string)


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %aavs_check_available_data [options]")
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
    parser.add_option("--type", action="store", dest="type",
                      default="channel", help="File Manager Format (channel, raw)")
    parser.add_option("--mode", action="store", dest="mode",
                      default="integ", help="FileDAQ Mode (integ, cont, burst, null)")

    (opts, args) = parser.parse_args(argv[1:])

    t_date = None
    t_start = None
    t_stop = None
    t_cnt = 0

    modo = FileDAQModes.Integrated
    if opts.mode == "cont":
        modo = FileDAQModes.Continuous
    elif opts.mode == "burst":
        modo = FileDAQModes.Burst
    elif opts.mode == "null":
        modo = FileDAQModes.Null

    if opts.date:
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
            t_start = dt_to_timestamp(t_date)
            t_stop = dt_to_timestamp(t_date) + (60 * 60 * 24)
        except:
            print "Bad date format detected (must be YYYY-MM-DD)"
    else:
        if opts.start:
            try:
                t_start = dt_to_timestamp(datetime.datetime.strptime(opts.start, "%Y-%m-%d_%H:%M:%S"))
                print "Start Time:  " + ts_to_datestring(t_start)
            except:
                print "Bad t_start time format detected (must be YYYY-MM-DD_HH:MM:SS)"
        if opts.stop:
            try:
                t_stop = dt_to_timestamp(datetime.datetime.strptime(opts.stop, "%Y-%m-%d_%H:%M:%S"))
                print "Stop  Time:  " + ts_to_datestring(t_stop)
            except:
                print "Bad t_stop time format detected (must be YYYY-MM-DD_HH:MM:SS)"

    #print t_date, t_start, t_stop

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']
    print "\nStation Name: ", station_name
    print "Checking directory: ", opts.directory + "\n"

    if opts.type == "channel":
        file_manager = ChannelFormatFileManager(root_path=opts.directory, daq_mode=modo)
    elif opts.type == "raw":
        file_manager = RawFormatFileManager(root_path=opts.directory, daq_mode=modo)
    else:
        print "\n Please specify a data format (channel, raw)"
        exit()
    print "\tFILE\t\t TIMESTAMP\t\tSTART\t\t\tSTOP\t\tSIZE (MB)\tBLOCKS"
    print "---------------------+-----------------+------------------+--------------------------+--------------+-----------"
    if opts.mode == "null":
        lista = sorted(glob.glob(opts.directory + "/" + opts.type + "_%d_*hdf5" % (int(opts.tile)-1)))
    else:
        lista = sorted(glob.glob(opts.directory + "/" + opts.type + "_" + opts.mode + "_%d_*hdf5" % (int(opts.tile)-1)))
    for l in lista:
        dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(int(opts.tile)-1))
        if dic:
            #data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=int(opts.tile)-1, n_samples=dic['n_blocks'])
            data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=int(opts.tile)-1, n_samples=20000000)
            if len(timestamps):
                if not t_start and not t_stop:
                    print " ", l[-21:-5], "\t", int(timestamps[0][0]), "\t", ts_to_datestring(timestamps[0][0]), "\t", \
                        ts_to_datestring(timestamps[-1][0]), "\t%6s"%(str(os.path.getsize(l)/1000000)), "\t\t", "%6s"%(str(len(timestamps)))
                else:
                    if timestamps[0] > t_stop:
                        break
                    cnt = 0
                    if not t_start >= timestamps[-1]:
                        if not t_stop <= timestamps[0]:
                            for i, t in enumerate(timestamps):
                                if t_start <= t[0] <= t_stop:
                                    cnt = cnt + 1
                                    t_cnt = t_cnt + 1
                    if cnt:
                        print " ", l[-21:-5], "\t", int(timestamps[0][0]), "\t", ts_to_datestring(timestamps[0][0]), "\t", \
                            ts_to_datestring(timestamps[-1][0]), "\t%6s\t"%(str(os.path.getsize(l)/1000000)), "\t", "%6s"%(str(cnt))
        else:
            print l[-21:-5], "\t", fname_to_tstamp(l[-21:-7]), "\t", \
                ts_to_datestring(fname_to_tstamp(l[-21:-7])), "\t", ": no metadata available"
    if t_cnt:
        print "\nFound %d measurements\n" % t_cnt
    print



