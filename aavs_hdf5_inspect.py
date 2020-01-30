from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
from aavs_calibration.common import get_antenna_positions, get_antenna_tile_names
from pyaavs import station
import time
import datetime
import glob
import sys


# Global flag to stop the scrpts
stop_plotting = False
img_dir = "/storage/monitoring/phase1/"


def dt_to_timestamp(d):
    return time.mktime(d.timetuple())


def fname_to_tstamp(date_time_string):
    time_parts = date_time_string.split('_')
    d = datetime.datetime.strptime(time_parts[0], "%Y%m%d")  # "%d/%m/%Y %H:%M:%S"
    timestamp = time.mktime(d.timetuple())
    timestamp += int(time_parts[1])
    return timestamp


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.fromtimestamp(tstamp), formato)


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %monitor_bandpasses [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs1_full_station.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS1)")
    parser.add_option("--dir", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data",
                      help="Directory where plots will be generated (default: /storage/monitoring/integrated_data)")

    parser.add_option("--tile", action="store", dest="tile",
                      default=16, help="Tile number [1-16]")
    parser = OptionParser(usage="usage: %aavs_read_data [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs2.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS1)")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data/",
                      help="Directory where plots will be generated (default: /storage/monitoring/integrated_data)")
    parser.add_option("--tile", action="store", dest="tile", type=str,
                      default="1", help="Tile Number")
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
    trovato = None

    if opts.date:
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
            t_start = dt_to_timestamp(t_date)
            t_stop = dt_to_timestamp(t_date) + (60 * 60 * 24)
            print "Start Time:  " + ts_to_datestring(t_start)
            print "Stop  Time:  " + ts_to_datestring(t_stop)
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

    if "all" in opts.tile.lower():
        tiles = [i+1 for i in range(16)]
    else:
        tiles = [int(i) for i in opts.tile.split(",")]

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']

    if station_name == "AAVS1.5":
        if "all" in opts.tile.lower():
            tiles = [1, 2, 3]

    print "\nStation Name: ", station_name
    print "Checking directory: ", opts.directory+station_name.lower() + "\n"
    print "Looking for tiles: ", tiles, "\n"

    # Instantiate a file manager
    file_manager = ChannelFormatFileManager(root_path=opts.directory+station_name.lower(),
                                            daq_mode=FileDAQModes.Integrated)

    base, x, y = get_antenna_positions(station_name)
    #print len(base), len(x), len(y)
    ants = []
    for j in base:
        ants += ["ANT-%03d" % int(j)]

    for tile in tiles:

        t_cnt = 0
        lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d_*hdf5" % (tile-1)))

        for cnt_l, l in enumerate(lista):
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile-1))
            if dic:
                data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile - 1,
                                                          n_samples=dic['n_blocks'])
                cnt = 0
                if not t_start >= timestamps[-1]:
                    if not t_stop <= timestamps[0]:
                        for i, t in enumerate(timestamps):
                            if t_start <= t[0] <= t_stop:
                                cnt = cnt + 1
                                t_cnt = t_cnt + 1

                                msg = "\r[%d/%d] TILE-%02d   File: %s" % (cnt_l+1, len(lista), tile, l.split("/")[-1]) + \
                                      " --> Writing " + "TILE-%02d_" % tile + orario + ".png"
                                sys.stdout.write(ERASE_LINE + msg)
                                sys.stdout.flush()

                                trovato = l

                msg = "\r[%d/%d] TILE-%02d   File: %s" % (cnt_l+1, len(lista), tile, l.split("/")[-1]) + "   " + \
                      ts_to_datestring(timestamps[0][0]) + "   " + ts_to_datestring(timestamps[-1][0])
                sys.stdout.write(ERASE_LINE + msg)
                sys.stdout.flush()
            else:
                msg = "\r[%d/%d] TILE-%02d   File: %s" % (cnt_l+1, len(lista), tile, l.split("/")[-1]) + \
                      "   " + ": no metadata available"
                sys.stdout.write(msg)
                sys.stdout.flush()

        msg = "\rTILE-%02d - written %d files   \n" % (tile, t_cnt)
        sys.stdout.write(ERASE_LINE + msg)
        sys.stdout.flush()

    if trovato:
        for tile in tiles:
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(trovato[-21:-7]), tile_id=(tile-1))
            print "File: ", trovato[-21:-7]
            print "\nKEY\t\tValue\n---------------------------------------------------"
            for k in sorted(dic.keys()):
                print k, "\t", dic[k]


