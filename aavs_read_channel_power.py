import matplotlib
# if 'matplotlib.backends' not in sys.modules:
matplotlib.use('agg') # not to use X11
from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import sys, os, glob
import numpy as np
from pyaavs import station
from time import sleep
import datetime
from aavs_utils import tstamp_to_fname, dt_to_timestamp, ts_to_datestring, fname_to_tstamp, closest

POWER_PATH = "/storage/monitoring/power/station_power/"
ERASE_LINE = '\x1b[2K'


def get_ant_map():
    adu_remap = [0, 1, 2, 3, 8, 9, 10, 11, 15, 14, 13, 12, 7, 6, 5, 4]
    with open("aavs_map.txt") as fmap:
        records = fmap.readlines()
    ant_map = []
    for r in records:
        if len(r.split()) > 2:
            ant_map += [[int(r.split()[0]), adu_remap[int(r.split()[1])-1], int(r.split()[2])]]
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
    parser.add_option("--tile", action="store", dest="tile",
                      default="", help="Stop Frequency")
    parser.add_option("--channel", action="store", dest="channel",
                      default="", help="Frequency channel")
    parser.add_option("--lab", action="store_true", dest="lab",
                      default=False, help="Lab data does not require station name in directory path")

    (opts, args) = parser.parse_args(argv[1:])

    t_date = None
    t_start = None
    t_stop = None
    print

    if not opts.date == "":
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m")
            t_start = dt_to_timestamp(t_date)
            if not t_date.month == 12:
                t_stop = dt_to_timestamp(datetime.datetime(t_date.year, t_date.month + 1, 1))
            else:
                t_stop = dt_to_timestamp(datetime.datetime(t_date.year + 1, 1, 1))
            print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
            print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
        except:
            print "Bad date format detected (must be YYYY-MM)"
            exit()
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
        if opts.tile == "":
            tiles = range(16)
        else:
            tiles = [int(t) for t in opts.tile.split(",")]

    directory = opts.directory
    if not opts.lab:
        directory += station_name.lower()
    print "\nStation Name: ", station_name
    print "Checking directory: ", directory + "\n"
    print "Looking for tiles: ", tiles, "\n"

    file_manager = ChannelFormatFileManager(root_path=directory,
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
        #sys.stdout.write(datetime.datetime.strftime(datetime.datetime.utcnow(), "\n%Y-%m-%d %H:%M:%S - ") +
        #                 "Processing Tile-%02d" % (tile + 1))
        #sys.stdout.flush()
        #print "Processing Tile-%02d" % (tile + 1)
        lista = sorted(glob.glob(directory + "/channel_integ_%d_*_0.hdf5" % (tile)))
        t_stamps = {}
        acc_power_x = {}
        acc_power_y = {}
        for a in range(16):
            t_stamps["ANT-%03d" % ant_map[(tile * 16) + a][2]] = []
            acc_power_x["ANT-%03d" % ant_map[(tile * 16) + a][2]] = []
            acc_power_y["ANT-%03d" % ant_map[(tile * 16) + a][2]] = []

        for cnt_l, l in enumerate(lista):
            if cnt_l < len(lista) - 1:
                t_file = fname_to_tstamp(lista[cnt_l + 1][-21:-7])
                if t_file < t_start:
                    continue
            #print l[-21:-7], " --> ", fname_to_tstamp(l[-21:-7])
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile))
            #dic = file_manager.get_metadata(tile_id=(tile))
            if dic:
                data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile, n_samples=2000000)
                #data, timestamps = file_manager.read_data(tile_id=tile, n_samples=2000000)
                #print "LEN DATA: ", len(data)
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
                                                t_stamps["ANT-%03d" % ant_map[(tile * 16) + sb_in][2]] += [t[0]]
                                                with np.errstate(divide='ignore'):
                                                    acc_power_x["ANT-%03d" % ant_map[(tile * 16) + sb_in][2]] += \
                                                        [10 * np.log10(np.sum(spettro_x[xmin:xmax + 1]))]
                                                    acc_power_y["ANT-%03d" % ant_map[(tile * 16) + sb_in][2]] += \
                                                        [10 * np.log10(np.sum(spettro_y[xmin:xmax + 1]))]
                                msg = "\rProcessing Tile-%02d - " % (tile + 1) + ts_to_datestring(t[0])
                                #print msg
                                sys.stdout.write(ERASE_LINE + msg)
                                sys.stdout.flush()

            # msg = "\r[%d/%d] File: %s" % (cnt_l + 1, len(lista), l.split("/")[-1]) + "   " + ts_to_datestring(
            #     timestamps[0][0]) + "   " + ts_to_datestring(timestamps[-1][0])
            # sys.stdout.write(ERASE_LINE + msg)
            # sys.stdout.flush()

        opath = POWER_PATH + station_name
        if not os.path.exists(opath):
            os.makedirs(opath)
        opath += "/" + opts.date
        if not os.path.exists(opath):
            os.makedirs(opath)
        t_freq = "FREQ-" + str("%03d" % int(asse_x[xmin])) + "MHz"
        opath += "/" + t_freq
        if not os.path.exists(opath):
            os.makedirs(opath)
        opath += "/"

        for sb_in in range(16):
            if int(asse_x[xmin]) == int(asse_x[xmax]):
                data_fname = opath + station_name + "_POWER_" + opts.date + "_TILE-%02d_ANT-%03d_%s.txt" % \
                             (int(tile + 1), ant_map[(tile * 16) + sb_in][2], t_freq)
            else:
                data_fname = opath + station_name + "_POWER_" + opts.date + "_TILE-%02d_ANT-%03d_BAND-%d-%dMHz.txt" % \
                            (int(tile + 1), ant_map[(tile * 16) + sb_in][2], int(asse_x[xmin]), int(asse_x[xmax]))
            with open(data_fname, "w") as ft:
                ft.write("Tstamp\tDate\tTime\tPol-X\tPol-Y\n")
                for n, q in enumerate(acc_power_x["ANT-%03d" % ant_map[(tile * 16) + sb_in][2]]):
                    ft.write("%d\t%s\t%6.3f\t%6.3f\n" % (t_stamps["ANT-%03d" % ant_map[(tile * 16) + sb_in][2]][n],
                                                         ts_to_datestring(t_stamps["ANT-%03d" % ant_map[(tile * 16) +
                                                                                                        sb_in][2]][n],
                                                                          "%Y-%m-%d\t%H:%M:%S"), q,
                                                         acc_power_y["ANT-%03d" % ant_map[(tile * 16) + sb_in][2]][n]))
            #sys.stdout.write(ERASE_LINE + "\rOutput File: " + data_fname)
            #sys.stdout.flush()

        sys.stdout.write(ERASE_LINE + datetime.datetime.strftime(datetime.datetime.utcnow(), "\r%Y-%m-%d %H:%M:%S - ") +
                         "Processed Tile-%02d in %s\n" % ((tile + 1), opath))
        sys.stdout.flush()







