import matplotlib
# if 'matplotlib.backends' not in sys.modules:
matplotlib.use('agg') # not to use X11
from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import sys, os, glob
import numpy as np
from pyaavs import station
from time import sleep
import datetime
from aavs_calibration.common import get_antenna_positions
from aavs_utils import tstamp_to_fname, dt_to_timestamp, ts_to_datestring, fname_to_tstamp, find_ant_by_name, closest

POWER_PATH = "/storage/monitoring/power/station_power/"
ERASE_LINE = '\x1b[2K'


def get_ant_map():
    adu_remap = [0, 1, 2, 3, 8, 9, 10, 11, 15, 14, 13, 12, 7, 6, 5, 4]
    with open("aavs_map.txt") as fmap:
        records = fmap.readlines()
    ant_map = []
    for r in records:
        if len(r.split()) > 2:
            ant_map += [int(r.split()[0]), adu_remap[int(r.split()[1])], int(r.split()[2])]
    return ant_map


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


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv

    parser = OptionParser(usage="usage: %aavs_read_data [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs2.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS1)")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data/",
                      help="Directory where plots will be generated (default: /storage/monitoring/integrated_data)")
    parser.add_option("--date", action="store", dest="date",
                      default="", help="Date time for filter (YYYY-mm, a month will be processed)")
    parser.add_option("--startfreq", action="store", dest="startfreq", type="float",
                      default=0, help="Start Frequency")
    parser.add_option("--stopfreq", action="store", dest="stopfreq", type="float",
                      default=400, help="Stop Frequency")
    parser.add_option("--channel", action="store", dest="channel",
                      default="", help="Frequency channel")

    (opts, args) = parser.parse_args(argv[1:])

    t_date = None
    t_start = None
    t_stop = None
    print

    if not opts.date == "":
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m")
            t_start = dt_to_timestamp(t_date)
            if not t_date.month == 11:
                t_stop = datetime.datetime(t_date.year, t_date.month + 1, 1)
            else:
                t_stop = datetime.datetime(t_date.year + 1, 1, 1)
            print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
            print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
        except:
            print "Bad date format detected (must be YYYY-MM-DD)"
    else:
        print "Missing Argument 'date'\n"
        exit()

    date_path = tstamp_to_fname(t_start)[:-6]

    asse_x = np.arange(512) * 400/512.

    ant_map = get_ant_map()

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']

    if station_name == "AAVS1.5":
        if "all" in opts.tile.lower():
            tiles = [1, 2, 3]
            tile_names = ["7", "11", "16"]
    else:
        tiles = range(16)

    print "\nStation Name: ", station_name
    print "Checking directory: ", opts.directory+station_name.lower() + "\n"
    print "Looking for tiles: ", tiles, "\n"

    file_manager = ChannelFormatFileManager(root_path=opts.directory+station_name.lower(),
                                            daq_mode=FileDAQModes.Integrated)

    da = tstamp_to_fname(t_start)[:-6]
    date_path = da[:4] + "-" + da[4:6] + "-" + da[6:]

    if opts.channel == "":
        xmin = closest(asse_x, float(opts.startfreq))
        xmax = closest(asse_x, float(opts.stopfreq))
    else:
        xmin = int(opts.channel)
        xmax = int(opts.channel)
    if xmin == xmax:
        print "Using channel #" + str(xmin) + " (Freq: " + str(asse_x[xmin]) + ")"
    else:
        print "Using channels from #" + str(xmin) + " (Freq: " + str(asse_x[xmin]) + ") to #" + str(xmax) + \
              " (Freq: " + str(asse_x[xmax]) + ")"

    for tile in tiles:
        print datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%d %H:%M:%S - ") + "Processing Tile-%02d\n" % (tile + 1)
        lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d_*hdf5" % (tile)))
        t_stamps = {}
        acc_power_x = {}
        acc_power_y = {}
        for a in range(16):
            t_stamps["ANT-%03d" % ant_map[(tile * 16) + a]] = []
            acc_power_x["ANT-%03d" % ant_map[(tile * 16) + a]] = []
            acc_power_y["ANT-%03d" % ant_map[(tile * 16) + a]] = []

        for cnt_l, l in enumerate(lista):
            if cnt_l < len(lista) - 1:
                t_file = fname_to_tstamp(lista[cnt_l + 1][-21:-7])
                if t_file < t_start:
                    continue
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile))
            if dic:
                data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile,
                                                          n_samples=200000)
                cnt = 0
                if timestamps[0] > t_stop:
                    break
                if not t_start >= timestamps[-1]:
                    if not t_stop <= timestamps[0]:
                        for i, t in enumerate(timestamps):
                            if t_start <= t[0] <= t_stop:
                                for sb_in in range(16):
                                    spettro_x = data[:, sb_in, 0, i]
                                    spettro_y = data[:, sb_in, 1, i]
                                    if not np.sum(spettro_x[20:50]) == 0:
                                    #if True: # syncbox patch
                                        if not np.sum(spettro_x[20:210]) == 0:
                                        #if True: # syncbox patch
                                            if not np.sum(spettro_x[300:350]) == 0:
                                            #if True: # syncbox patch
                                                t_stamps["ANT-%03d" % ant_map[(tile * 16) + sb_in]] += [t[0]]
                                                with np.errstate(divide='ignore'):
                                                    acc_power_x["ANT-%03d" % ant_map[(tile * 16) + sb_in]] += \
                                                        [10 * np.log10(np.sum(spettro_x[xmin:xmax + 1]))]
                                                    acc_power_y["ANT-%03d" % ant_map[(tile * 16) + sb_in]] += \
                                                        [10 * np.log10(np.sum(spettro_y[xmin:xmax + 1]))]
                                msg = "\rProcessing " + ts_to_datestring(t[0])
                                sys.stdout.write(ERASE_LINE + msg)
                                sys.stdout.flush()

            msg = "\r[%d/%d] File: %s" % (cnt_l + 1, len(lista), l.split("/")[-1]) + "   " + ts_to_datestring(
                timestamps[0][0]) + "   " + ts_to_datestring(timestamps[-1][0])
            sys.stdout.write(ERASE_LINE + msg)
            sys.stdout.flush()

        opath = POWER_PATH + station_name
        if not os.path.exists(opath):
            os.makedirs(opath)
        t_date = datetime.datetime.strftime(datetime.datetime.strptime(opts.start, "%Y-%m-%d_%H:%M:%S"), "%Y-%m")
        opath = POWER_PATH + "/" + t_date
        if not os.path.exists(opath):
            os.makedirs(opath)
        t_freq = "FREQ-" + str("%03d" % int(asse_x[xmin])) + "MHz"
        opath += "/" + t_freq
        if not os.path.exists(opath):
            os.makedirs(opath)
        opath += "/"

        for sb_in in range(16):
            if int(asse_x[xmin]) == int(asse_x[xmax]):
                data_fname = opath + station_name + "_POWER_" + t_date + "_TILE-%02d_ANT-%03d_%s.txt" % \
                             (int(tile + 1), int(opts.antenna), t_freq)
            else:
                data_fname = opath + station_name + "_POWER_" + t_date + "_TILE-%02d_ANT-%03d_BAND-%d-%dMHz.txt" % \
                            (int(tile + 1), int(opts.antenna), int(asse_x[xmin]), int(asse_x[xmax]))
            with open(data_fname, "w") as ft:
                ft.write("Tstamp\tDate\tTime\tPol-X\tPol-Y\n")
                for n, q in enumerate(acc_power_x["ANT-%03d" % ant_map[(tile * 16) + sb_in]]):
                    ft.write("%d\t%s\t%6.3f\t%6.3f\n" % (t_stamps["ANT-%03d" % ant_map[(tile * 16) + sb_in]][n],
                                                         ts_to_datestring(t_stamps[n], "%Y-%m-%d\t%H:%M:%S"),
                                                         q, acc_power_y["ANT-%03d" % ant_map[(tile * 16) + sb_in]][n]))
            sys.stdout.write(ERASE_LINE + "\nOutput File: " + data_fname + "\n")
            sys.stdout.flush()

        print datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%d %H:%M:%S - ") + "Processed Tile-%02d\n" % (tile + 1)







