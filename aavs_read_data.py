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
from aavs_utils import tstamp_to_fname, dt_to_timestamp, ts_to_datestring, fname_to_tstamp, find_ant_by_name

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
    parser.add_option("--input", action="store", dest="input", type=int,
                      default=0, help="Tile Input Number")
    parser.add_option("--antenna", action="store", dest="antenna", type=int,
                      default=0, help="Antenna Name")
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
    parser.add_option("--spectrogram", action="store_true", dest="spectrogram",
                      default=False, help="Produce an antenna (required argument) spectrogram")

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

    date_path = tstamp_to_fname(t_start)[:-6]

    plt.ioff()
    if not opts.input:
        nplot = 16
    else:
        nplot = 1

    ind = np.arange(nplot)
    remap = [0, 1, 2, 3, 8, 9, 10, 11, 15, 14, 13, 12, 7, 6, 5, 4]

    if "all" in opts.tile.lower():
        tiles = [i+1 for i in range(16)]
        tile_names = [str(i+1) for i in range(16)]
    else:
        tiles = [int(i) for i in opts.tile.split(",")]
        tile_names = [str(i) for i in opts.tile.split(",")]

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']

    if station_name == "AAVS1.5":
        if "all" in opts.tile.lower():
            tiles = [1, 2, 3]
            tile_names = ["7", "11", "16"]

    print "\nStation Name: ", station_name
    print "Checking directory: ", opts.directory+station_name.lower() + "\n"
    print "Looking for tiles: ", tiles, "\n"

    file_manager = ChannelFormatFileManager(root_path=opts.directory+station_name.lower(),
                                            daq_mode=FileDAQModes.Integrated)

    base, x, y = get_antenna_positions(station_name)
    ants = []
    for j in base:
        ants += ["ANT-%03d" % int(j)]

    antenne = []
    if nplot == 16:
        antenne = range(16)
    else:
        antenne = [remap[opts.input - 1]]
    print "Antennas: ", (np.array(antenne) + 1).tolist()

    plot_mode = 0
    if opts.spectrogram:
        if opts.input or opts.antenna:
            plot_mode = 1
        else:
            print "Spectrogram mode requires antenna argument"
            exit(1)

    if plot_mode == 0:
        outer_grid = GridSpec(4, 4, hspace=0.4, wspace=0.4, left=0.04, right=0.98, bottom=0.04, top=0.96)
        gs = GridSpecFromSubplotSpec(int(np.ceil(np.sqrt(nplot))), int(np.ceil(np.sqrt(nplot))), wspace=0.4, hspace=0.6,
                                     subplot_spec=outer_grid[1:, :])

        fig = plt.figure(figsize=(11, 7), facecolor='w')
        ax_top_map = fig.add_subplot(outer_grid[1])
        ax_top_tile = fig.add_subplot(outer_grid[0])
        ax = []
        for i in xrange(nplot):
            ax += [fig.add_subplot(gs[i])]

        for en_tile, tile in enumerate(tiles):

            t_cnt = 0
            lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d_*hdf5" % (tile-1)))

            ax_top_map.cla()
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

            # Draw antenna positions
            for en in range(nplot):
                #print en, en + ((tile - 1) * 16), float(x[en + ((tile - 1) * 16)]), float(y[en + ((tile - 1) * 16)])
                ax_top_map.plot(float(x[en + ((tile - 1) * 16)]), float(y[en + ((tile - 1) * 16)]), marker='+', markersize=4, linestyle='None', color='k')

            ax_top_tile.cla()
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
            x_lines = []
            y_lines = []
            antenne = []
            if nplot == 16:
                antenne = range(16)
            else:
                antenne = [remap[opts.input - 1]]

            for i, sb_in in enumerate(antenne):
                ax[i].cla()
                ax[i].tick_params(axis='both', which='both', labelsize=8)
                ax[i].set_ylim([0, 50])
                ax[i].set_xlim([0, 512])
                ax[i].set_xticks([0, 128, 256, 384, 512])
                ax[i].set_xticklabels([0, 100, 200, 300, 400], fontsize=8)
                #ax[i].set_xlabel("MHz", fontsize=10)

                #ax[i].set_title("IN " + str(i + 1), fontsize=8) # scrivere nomi delle antenne al posto di questa
                ax[i].set_title(ants[sb_in + 16 * (tile - 1)], fontsize=8)
                xl, = ax[i].plot(range(512), range(512), color='b')
                x_lines += [xl]
                yl, = ax[i].plot(range(512), range(512), color='g')
                y_lines += [yl]
            #print x_lines[0]

            ax_top_tile.cla()
            ax_top_tile.set_axis_off()
            ax_top_tile.plot([0.001, 0.002], color='w')
            ax_top_tile.set_xlim(-20, 20)
            ax_top_tile.set_ylim(-20, 20)
            ax_top_tile.annotate("TILE %02d" % int(tile_names[en_tile]), (-12, 6), fontsize=24, color='black')
            tstamp_picture = ax_top_tile.annotate(" ", (-18, -12), fontsize=12, color='black')

            if not os.path.exists(PIC_PATH):
                os.makedirs(PIC_PATH)
            if not os.path.exists(PIC_PATH + "/" + station_name):
                os.makedirs(PIC_PATH + "/" + station_name)
            if not os.path.exists(PIC_PATH + "/" + station_name + "/" + date_path):
                os.makedirs(PIC_PATH + "/" + station_name + "/" + date_path)
            if not os.path.exists(PIC_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d" % int(tile_names[en_tile])):
                os.makedirs(PIC_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d" % int(tile_names[en_tile]))

            if opts.save:
                if not os.path.exists(TEXT_PATH):
                    os.makedirs(TEXT_PATH)
                if not os.path.exists(TEXT_PATH + "/" + station_name):
                    os.makedirs(TEXT_PATH + "/" + station_name)
                if not os.path.exists(TEXT_PATH + "/" + station_name + "/" + date_path):
                    os.makedirs(TEXT_PATH + "/" + station_name + "/" + date_path)
                if not os.path.exists(TEXT_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d" % int(tile_names[en_tile])):
                    os.makedirs(TEXT_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d" % int(tile_names[en_tile]))

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

                                    # Generate picture
                                    orario = ts_to_datestring(t[0], formato="%Y-%m-%d_%H%M%S")
                                    for ant, sb_in in enumerate(antenne):
                                        #ax[ant].cla()
                                        with np.errstate(divide='ignore'):
                                            spettro = 10 * np.log10(data[:, sb_in, 0, i])
                                        if opts.save:
                                            with open(TEXT_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d" %
                                                      int(tile_names[en_tile]) + "/TILE-%02d_" % int(tile_names[en_tile]) +
                                                      ants[sb_in + 16 * (tile - 1)] + "_POL-X_" + orario + ".txt", "w") as f:
                                                for s in data[:, sb_in, 0, i]:
                                                    f.write("%d\n" % s)
                                        x_lines[ant].set_ydata(spettro)
                                        #x_lines[ant].set_color('b')
                                        #ax[ant].plot(assex[2:-1], spettro[2:-1], scaley=True, color='b')
                                        with np.errstate(divide='ignore'):
                                            spettro = 10 * np.log10(data[:, sb_in, 1, i])
                                        if opts.save:
                                            with open(TEXT_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d" %
                                                      int(tile_names[en_tile]) + "/TILE-%02d_" % int(tile_names[en_tile]) +
                                                      ants[sb_in + 16 * (tile - 1)] + "_POL-Y_" + orario + ".txt", "w") as f:
                                                for s in data[:, sb_in, 1, i]:
                                                    f.write("%d\n" % s)
                                        y_lines[ant].set_ydata(spettro)
                                        #y_lines[ant].set_color('g')
                                        #ax[ant].plot(assex[2:-1], spettro[2:-1], scaley=True, color='g')
                                        #ax[ant].set_ylim(0, 50)
                                        #ax[ant].set_xlim(0, 400)
                                        #ax[ant].set_title(ants[ant + 16 * (tile - 1)], fontsize=8)
                                    #plt.draw()

                                    tstamp_picture.set_text(ts_to_datestring(t[0]))
                                    orario = ts_to_datestring(t[0], formato="%Y-%m-%d_%H%M%S")

                                    #plt.draw()
                                    #plt.show()
                                    plt.savefig(PIC_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d/TILE-%02d_" %
                                                (int(tile_names[en_tile]), int(tile_names[en_tile])) + orario + ".png")
                                    msg = "\r[%d/%d] TILE-%02d   File: %s" % (cnt_l+1, len(lista), int(tile_names[en_tile]),
                                                                              l.split("/")[-1]) + \
                                          " --> Writing " + "TILE-%02d_" % int(tile_names[en_tile]) + orario + ".png"
                                    sys.stdout.write(ERASE_LINE + msg)
                                    sys.stdout.flush()
                    msg = "\r[%d/%d] TILE-%02d   File: %s" % (cnt_l+1, len(lista), int(tile_names[en_tile]),
                        l.split("/")[-1]) + "   " + ts_to_datestring(timestamps[0][0]) + "   " + \
                        ts_to_datestring(timestamps[-1][0])
                    sys.stdout.write(ERASE_LINE + msg)
                    sys.stdout.flush()
                else:
                    msg = "\r[%d/%d] TILE-%02d   File: %s" % (cnt_l+1, len(lista),
                                            int(tile_names[en_tile]), l.split("/")[-1]) + "   " + ": no metadata available"
                    sys.stdout.write(msg)
                    sys.stdout.flush()

            msg = "\rTILE-%02d - written %d files in %s\n" % (int(tile_names[en_tile]), t_cnt, PIC_PATH + "/" +
                                            station_name + "/" + date_path + "/TILE-%02d" % (int(tile_names[en_tile])))
            sys.stdout.write(ERASE_LINE + msg)
            sys.stdout.flush()

    elif plot_mode == 1:
        if opts.antenna:
            print opts.antenna, find_ant_by_name(opts.antenna)
        #fig = plt.figure(figsize=(11, 7), facecolor='w')
        #ax = fig.add_subplot()





