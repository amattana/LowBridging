from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import sys, os, glob
import matplotlib
if not 'matplotlib.backends' in sys.modules:
    matplotlib.use('agg') # not to use X11from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import matplotlib.pyplot as plt
import numpy as np
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
    return time.mktime(d.timetuple())


def fname_to_tstamp(date_time_string):
    time_parts = date_time_string.split('_')
    d = datetime.datetime.strptime(time_parts[0], "%Y%m%d")  # "%d/%m/%Y %H:%M:%S"
    timestamp = time.mktime(d.timetuple())
    timestamp += int(time_parts[1])
    return timestamp


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.fromtimestamp(tstamp), formato)


def tstamp_to_fname(timestamp=None):
    """
    Returns a string date/time from a UNIX timestamp.
    :param timestamp: A UNIX timestamp.
    :return: A date/time string of the form yyyymmdd_secs
    """
    if timestamp is None:
        timestamp = 0

    datetime_object = datetime.datetime.fromtimestamp(timestamp)
    hours = datetime_object.hour
    minutes = datetime_object.minute
    seconds = datetime_object.second
    full_seconds = seconds + (minutes * 60) + (hours * 60 * 60)
    full_seconds_formatted = format(full_seconds, '05')
    base_date_string = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d')
    full_date_string = base_date_string + '_' + str(full_seconds_formatted)
    return str(full_date_string)


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

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
    parser.add_option("--save", action="store_true", dest="save",
                      default=False, help="Save single antenna measurements in text files")

    (opts, args) = parser.parse_args(argv[1:])

    t_date = None
    t_start = None
    t_stop = None
    assex = np.linspace(0, 400, 512)

    print

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

    plt.ioff()
    nplot = 16
    ind = np.arange(nplot)

    if "all" in opts.tile.lower():
        tiles = [i+1 for i in range(16)]
    else:
        tiles = [int(i) for i in opts.tile.split(",")]

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']

    print "\nStation Name: ", station_name
    print "Checking directory: ", opts.directory+station_name.lower() + "\n"
    print "Looking for tiles: ", tiles, "\n"

    file_manager = ChannelFormatFileManager(root_path=opts.directory+station_name.lower(),
                                            daq_mode=FileDAQModes.Integrated)

    for tile in tiles:

        t_cnt = 0
        lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d_*hdf5" % (tile-1)))

        outer_grid = GridSpec(4, 4, hspace=0.4, wspace=0.4, left=0.04, right=0.98, bottom=0.04, top=0.96)
        gs = GridSpecFromSubplotSpec(int(np.ceil(np.sqrt(16))), int(np.ceil(np.sqrt(16))), wspace=0.4, hspace=0.6,
                                     subplot_spec=outer_grid[1:, :])

        base, x, y = get_antenna_positions(station_name)
        ants = []
        for j in base:
            ants += ["ANT-%03d" % int(j)]
        ax = []
        fig = plt.figure(figsize=(11, 7), facecolor='w')
        ax_top_map = fig.add_subplot(outer_grid[1])
        ax_top_map.set_axis_off()
        ax_top_map.plot([0.001, 0.002], color='wheat')
        ax_top_map.set_xlim(-25, 25)
        ax_top_map.set_ylim(-25, 25)
        circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
        ax_top_map.add_artist(circle1)
        ax_top_map.annotate("E", (21, -1), fontsize=10, color='black')
        ax_top_map.annotate("W", (-25, -1), fontsize=10, color='black')
        ax_top_map.annotate("N", (-1, 21), fontsize=10, color='black')
        ax_top_map.annotate("S", (-1, -24), fontsize=10, color='black')

        ax_top_tile = fig.add_subplot(outer_grid[0])
        ax_top_tile.plot([0.001, 0.002], color='w')
        ax_top_tile.set_xlim(-20, 20)
        ax_top_tile.set_ylim(-20, 20)
        ax_top_tile.annotate("TILE 1", (-12, 6), fontsize=24, color='black')

        ax_top_tile.set_axis_off()
        # ax_top_x = fig.add_subplot(outer_grid[2])
        # ax_top_y = fig.add_subplot(outer_grid[3])

        # ax_top_x.cla()
        # ax_top_x.tick_params(axis='both', which='both', labelsize=6)
        # ax_top_x.set_xticks(xrange(1, 17))
        # ax_top_x.set_xticklabels(np.array(range(1, 17)).astype("str").tolist(), fontsize=6)
        # ax_top_x.set_yticks([10, 20])
        # ax_top_x.set_yticklabels(["10", "20"], fontsize=7)
        # ax_top_x.set_ylim([0, 30])
        # ax_top_x.set_xlim([0, 17])
        # ax_top_x.set_ylabel("RMS", fontsize=10)
        # #ax_top_x.grid()
        # ax_top_x.bar(ind + 0.8, (np.zeros(32)-10)[0:32:2], 0.8, color='b')
        # ax_top_x.set_title("Pol X", fontsize=10)
        #
        # ax_top_y.cla()
        # ax_top_y.tick_params(axis='both', which='both', labelsize=6)
        # ax_top_y.set_xticks(xrange(1, 17))
        # ax_top_y.set_xticklabels(np.array(range(1, 17)).astype("str").tolist(), fontsize=6)
        # ax_top_y.set_yticks([-15, 0])
        # ax_top_y.set_yticklabels(["10", "20"], fontsize=7)
        # ax_top_y.set_ylim([10, 40])
        # ax_top_y.set_xlim([0, 17])
        # ax_top_y.set_ylabel("RMS", fontsize=10)
        # #.ax_top_y.grid()
        # ax_top_y.bar(ind + 1, (np.zeros(32)-10)[1:32:2], 0.8, color='g')
        # ax_top_y.set_title("Pol Y", fontsize=10)
        #
        #print self.nplot,math.sqrt(self.nplot)
        for i in xrange(nplot):
            ax += [fig.add_subplot(gs[i])]
            ax[i].tick_params(axis='both', which='both', labelsize=8)
            ax[i].set_ylim([-80, -20])
            ax[i].set_xlim([0, 400])
            ax[i].set_title("IN " + str(i + 1), fontsize=8)

        # Draw antenna positions
        for en in range(nplot):
            ax_top_map.plot(float(x[en + ((tile - 1) * 16)]), float(y[en + ((tile - 1) * 16)]),
                            marker='+', markersize=4, linestyle='None', color='k')

        if not os.path.exists(PIC_PATH):
            os.makedirs(PIC_PATH)
        if not os.path.exists(PIC_PATH + "/TILE-%02d" % tile):
            os.makedirs(PIC_PATH + "/TILE-%02d" % tile)

        if opts.save:
            if not os.path.exists(TEXT_PATH):
                os.makedirs(TEXT_PATH)
            if not os.path.exists(TEXT_PATH + "/TILE-%02d" % tile):
                os.makedirs(TEXT_PATH + "/TILE-%02d" % tile)

        for y, l in enumerate(lista):
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

                                # Generate picture
                                orario = ts_to_datestring(t[0], formato="%Y-%m-%d_%H%M%S")
                                for ant in range(nplot):
                                    ax[ant].cla()
                                    with np.errstate(divide='ignore'):
                                        spettro = 10 * np.log10(data[:, ant, 0, i])
                                    if opts.save:
                                        with open(TEXT_PATH + "/TILE-%02d_" % tile +
                                                  ants[ant + 16 * (tile - 1)] + "_POL-X_" + orario + ".txt") as f:
                                            for s in spettro:
                                                f.write("%f\n" % s)
                                    ax[ant].plot(assex[2:-1], spettro[2:-1], scaley=True, color='b')
                                    with np.errstate(divide='ignore'):
                                        spettro = 10 * np.log10(data[:, ant, 1, i])
                                    if opts.save:
                                        with open(TEXT_PATH + "/TILE-%02d_" % tile +
                                                  ants[ant + 16 * (tile - 1)] + "_POL-Y_" + orario + ".txt") as f:
                                            for s in spettro:
                                                f.write("%f\n" % s)
                                    ax[ant].plot(assex[2:-1], spettro[2:-1], scaley=True, color='g')
                                    ax[ant].set_ylim(0, 50)
                                    ax[ant].set_xlim(0, 400)
                                    ax[ant].set_title(ants[ant + 16 * (tile - 1)], fontsize=8)

                                ax_top_tile.cla()
                                ax_top_tile.set_axis_off()
                                ax_top_tile.plot([0.001, 0.002], color='w')
                                ax_top_tile.set_xlim(-20, 20)
                                ax_top_tile.set_ylim(-20, 20)
                                ax_top_tile.annotate("TILE %02d" % tile, (-12, 6), fontsize=24, color='black')
                                orario = ts_to_datestring(t[0])
                                ax_top_tile.annotate(orario, (-18, -12), fontsize=12, color='black')
                                orario = ts_to_datestring(t[0], formato="%Y-%m-%d_%H%M%S")

                                plt.savefig(PIC_PATH + "/TILE-%02d/TILE-%02d_" % (tile, tile) + orario + ".png")
                                msg = "\r[%d/%d] TILE-%02d   File: %s" % (y+1, len(lista), tile, l.split("/")[-1]) + \
                                      "--> Writing " + "TILE-%02d_" % tile + orario + ".png"
                                sys.stdout.write(ERASE_LINE + msg)
                                sys.stdout.flush()
                msg = "\r[%d/%d] TILE-%02d   File: %s" % (y+1, len(lista), tile, l.split("/")[-1]) + "   " + \
                      ts_to_datestring(timestamps[0][0]) + "   " + ts_to_datestring(timestamps[-1][0])
                sys.stdout.write(ERASE_LINE + msg)
                sys.stdout.flush()
                time.sleep(0.2)
            else:
                msg = "\r[%d/%d] TILE-%02d   File: %s" % (y+1, len(lista), tile, l.split("/")[-1]) + \
                      "   " + ": no metadata available"
                sys.stdout.write(msg)
                sys.stdout.flush()

        msg = "\rTILE-%02d - written %d files   " % (tile, t_cnt)
        sys.stdout.write(ERASE_LINE + msg)
        sys.stdout.flush()


