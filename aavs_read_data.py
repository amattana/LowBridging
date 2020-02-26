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
from aavs_utils import tstamp_to_fname, dt_to_timestamp, ts_to_datestring, fname_to_tstamp, find_ant_by_name, \
    find_ant_by_tile, find_pos_by_name, closest, mro_daily_weather, diclist_to_array, calc_value

# Global flag to stop the scrpts
FIG_W = 14
TILE_H = 3.2
PIC_PATH = "/storage/monitoring/pictures"
SPGR_PATH = "/storage/monitoring/spectrograms"
TEXT_PATH = "/storage/monitoring/text_data"
ERASE_LINE = '\x1b[2K'


def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)


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
    parser.add_option("--single", action="store_true", dest="single",
                      default=False, help="Produces pictures for specific antenna")
    parser.add_option("--spectrogram", action="store_true", dest="spectrogram",
                      default=False, help="Produces a spectrogram for a specific antenna")
    parser.add_option("--weather", action="store_true", dest="weather",
                      default=False, help="Add weather info (if available)")
    parser.add_option("--startfreq", action="store", dest="startfreq", type="int",
                      default=0, help="Start Frequency")
    parser.add_option("--stopfreq", action="store", dest="stopfreq", type="int",
                      default=400, help="Stop Frequency")
    parser.add_option("--pol", action="store", dest="pol",
                      default="x", help="Polarization [x (default)| y]")

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
            print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
            print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
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

    w_data = []
    if opts.weather:
        w_units, w_data = mro_daily_weather(start=ts_to_datestring(t_start, formato="%Y-%m-%d_%H:%M:%S"),
                                             stop=ts_to_datestring(t_stop, formato="%Y-%m-%d_%H:%M:%S"))
        if len(w_data):
            w_time = diclist_to_array(w_data, 'time')
            w_temp = diclist_to_array(w_data, 'temp')
            w_wind = diclist_to_array(w_data, 'wind')
            w_wdir = diclist_to_array(w_data, 'wdir')
            w_rain = diclist_to_array(w_data, 'rain')
            print "\nWeather data acquired, %d records"%len(w_temp)#, "  ", w_temp[0:8]
        else:
            print "\nNo weather data available\n"

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
    if opts.antenna:
        tiles = [find_ant_by_name(opts.antenna)[0]]

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
    if opts.antenna:
        antenne = [remap[find_ant_by_name(opts.antenna)[1] - 1]]
        print "Antenna: ", opts.antenna
    else:
        if nplot == 16:
            antenne = range(16)
        else:
            antenne = [remap[opts.input - 1]]
    print "Tile Inputs: ", (np.array(antenne) + 1).tolist(), "\n"

    plot_mode = 0
    if opts.single:
        if opts.input or opts.antenna:
            plot_mode = 1
        else:
            print "Missing antenna argument"
            exit(1)
    if opts.spectrogram:
        if opts.antenna:
            plot_mode = 2
        else:
            print "Missing antenna argument"
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

            msg = "\r" + datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%d %H:%M:%S ") \
                  + "TILE-%02d - written %d files in %s\n" % (int(tile_names[en_tile]), t_cnt, PIC_PATH + "/" +
                                            station_name + "/" + date_path + "/TILE-%02d" % (int(tile_names[en_tile])))
            sys.stdout.write(ERASE_LINE + msg)
            sys.stdout.flush()

    elif plot_mode == 1:

        tile = tiles[0]
        if not opts.antenna:
            skala_name = find_ant_by_tile(tile, antenne[0])
        else:
            skala_name = opts.antenna

        if not os.path.exists(PIC_PATH):
            os.makedirs(PIC_PATH)
        if not os.path.exists(PIC_PATH + "/" + station_name):
            os.makedirs(PIC_PATH + "/" + station_name)
        if not os.path.exists(PIC_PATH + "/" + station_name + "/" + date_path):
            os.makedirs(PIC_PATH + "/" + station_name + "/" + date_path)
        if not os.path.exists(
                PIC_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d_ANT-%03d" % (int(tile), int(skala_name))):
            os.makedirs(PIC_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d_ANT-%03d" % (int(tile), int(skala_name)))

        grid = GridSpec(15, 8, hspace=0.8, wspace=0.4, left=0.08, right=0.98, bottom=0.1, top=0.98)
        fig = plt.figure(figsize=(11, 7), facecolor='w')

        ax_top_map = fig.add_subplot(grid[0:3, 7])
        ax_top_map.set_axis_off()
        ax_top_map.plot([0.001, 0.002], color='wheat')
        ax_top_map.set_xlim(-26.2, 26.2)
        ax_top_map.set_ylim(-26.2, 26.2)
        circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
        ax_top_map.add_artist(circle1)
        ax_top_map.annotate("E", (21, -1), fontsize=10, color='black')
        ax_top_map.annotate("W", (-26, -1), fontsize=10, color='black')
        ax_top_map.annotate("N", (-1, 21), fontsize=10, color='black')
        ax_top_map.annotate("S", (-1, -25.5), fontsize=10, color='black')
        zx, zy = find_pos_by_name(skala_name)
        ax_top_map.plot(zx, zy, marker='+', markersize=4,
                        linestyle='None', color='k')


        ax_top_label = fig.add_subplot(grid[0:3, 4:6])
        ax_top_label.set_axis_off()
        ax_top_label.set_xlim(-20, 20)
        ax_top_label.set_ylim(-20, 20)
        time_label = ax_top_label.annotate("timestamp", (-16, 0), fontsize=16, color='black')

        ax_top_tile = fig.add_subplot(grid[0:3, 0:4])
        ax_top_tile.cla()
        ax_top_tile.plot([0.001, 0.002], color='w')
        ax_top_tile.set_xlim(-20, 20)
        ax_top_tile.set_ylim(-20, 20)
        title = ax_top_tile.annotate("TILE: "+str(tile) + "    Antenna: " + str(skala_name), (-20, 0), fontsize=22, color='black')
        ax_top_tile.set_axis_off()

        ax_xpol = fig.add_subplot(grid[3:9, :])
        ax_xpol.tick_params(axis='both', which='both', labelsize=10)
        ax_xpol.set_ylim(0, 50)
        ax_xpol.set_xlim(0, 512)
        ax_xpol.set_xlabel("MHz", fontsize=12)
        ax_xpol.set_ylabel("dB", fontsize=12)
        ax_xpol.set_xticks([x*64 for x in range(9)])
        ax_xpol.set_xticklabels([x*50 for x in range(9)], fontsize=10)
        ax_xpol.grid()
        xl, = ax_xpol.plot(range(512), range(512), color='b')

        ax_ypol = fig.add_subplot(grid[10:, :])
        ax_ypol.tick_params(axis='both', which='both', labelsize=10)
        ax_ypol.set_ylim(0, 50)
        ax_ypol.set_xlim(0, 512)
        ax_ypol.set_xlabel("MHz", fontsize=12)
        ax_ypol.set_ylabel("dB", fontsize=12)
        ax_ypol.set_xticks([x*64 for x in range(9)])
        ax_ypol.set_xticklabels([x*50 for x in range(9)], fontsize=10)
        ax_ypol.grid()
        yl, = ax_ypol.plot(range(512), range(512), color='g')

        lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d_*hdf5" % (tile - 1)))
        t_cnt = 0
        for cnt_l, l in enumerate(lista):
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile - 1))
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
                                for sb_in in antenne:
                                    with np.errstate(divide='ignore'):
                                        spettro = 10 * np.log10(data[:, sb_in, 0, i])
                                    xl.set_ydata(spettro)
                                    with np.errstate(divide='ignore'):
                                        spettro = 10 * np.log10(data[:, sb_in, 1, i])
                                    yl.set_ydata(spettro)
                                time_label.set_text(ts_to_datestring(t[0]))
                                plt.savefig(PIC_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d_ANT-%03d/TILE-%02d_ANT-%03d_" %
                                            (int(tile), int(skala_name), int(tile), int(skala_name)) + orario + ".png")
                                msg = "\r[%d/%d] TILE-%02d   File: %s" % (cnt_l + 1, len(lista), int(tile),
                                                                          l.split("/")[-1]) + \
                                      " --> Writing " + "TILE-%02d_" % int(tile) + orario + ".png"
                                sys.stdout.write(ERASE_LINE + msg)
                                sys.stdout.flush()
                msg = "\r[%d/%d] TILE-%02d   File: %s" % (cnt_l+1, len(lista), int(tile),
                    l.split("/")[-1]) + "   " + ts_to_datestring(timestamps[0][0]) + "   " + \
                    ts_to_datestring(timestamps[-1][0])
                sys.stdout.write(ERASE_LINE + msg)
                sys.stdout.flush()
        print "\n" + datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%d %H:%M:%S ") + "Written", t_cnt, "files.\n"

    # SPECTROGRAM
    elif plot_mode == 2:

        da = tstamp_to_fname(t_start)[:-6]
        date_path = da[:4] + "-" + da[4:6] + "-" + da[6:]

        band = str("%03d" % int(opts.startfreq)) + "-" + str("%03d" % int(opts.stopfreq))
        if opts.pol.lower() == "x":
            pol = 0
        elif opts.pol.lower() == "y":
            pol = 1
        else:
            print "\nWrong value passed for argument pol, using default X pol"
            pol = 0

        row = 4
        if len(w_data):
            row = row + 1

        gs = GridSpec(row, 1, hspace=0.8, wspace=0.4, left=0.06, right=0.92, bottom=0.1, top=0.95)
        fig = plt.figure(figsize=(14, 9), facecolor='w')

        fig.subplots_adjust(right=0.75)

        ax_water = fig.add_subplot(gs[0:4])
        asse_x = np.linspace(0, 400, 512)
        xmin = closest(asse_x, int(opts.startfreq))
        xmax = closest(asse_x, int(opts.stopfreq))

        dayspgramma = np.empty((10, xmax - xmin + 1,))
        dayspgramma[:] = np.nan

        wclim = (10, 35)
        ax_water.cla()
        ax_water.imshow(dayspgramma, interpolation='none', aspect='auto', extent=[xmin, xmax, 60, 0], cmap='jet', clim=wclim)
        ax_water.set_ylabel("Time (minutes)")
        ax_water.set_xlabel('MHz')

        if len(w_data):
            ax_weather = fig.add_subplot(gs[-1, :])

        tile = find_ant_by_name(opts.antenna)[0]
        lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d_*hdf5" % (tile - 1)))
        t_cnt = 0
        orari = []
        t_stamps = []
        for cnt_l, l in enumerate(lista):
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile - 1))
            if dic:
                data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile - 1,
                                                          n_samples=dic['n_blocks'])
                cnt = 0
                if not t_start >= timestamps[-1]:
                    if not t_stop <= timestamps[0]:
                        for i, t in enumerate(timestamps):
                            if t_start <= t[0] <= t_stop:
                                t_stamps += [t[0]]
                                orari += [datetime.datetime.utcfromtimestamp(t[0])]
                                for sb_in in antenne:
                                    with np.errstate(divide='ignore'):
                                        spettro = 10 * np.log10(data[:, sb_in, pol, i])
                                if xmin == 0:
                                    dayspgramma = np.concatenate((dayspgramma, [spettro[:xmax + 1]]), axis=0)
                                else:
                                    dayspgramma = np.concatenate((dayspgramma, [spettro[xmin:xmax + 1]]), axis=0)
                                msg = "\rProcessing " + ts_to_datestring(t[0])
                                sys.stdout.write(ERASE_LINE + msg)
                                sys.stdout.flush()

            msg = "\r[%d/%d] File: %s" % (cnt_l + 1, len(lista), l.split("/")[-1]) + "   " + ts_to_datestring(
                timestamps[0][0]) + "   " + ts_to_datestring(timestamps[-1][0])
            sys.stdout.write(ERASE_LINE + msg)
            sys.stdout.flush()

        x_tick = []
        step = 0
        for z in range(len(orari)):
            if orari[z].hour == step:
                #print str(orari[z])
                x_tick += [z]
                step = step + 3
        #print str(orari[-1])
        x_tick += [len(dayspgramma[10:])]

        first_empty, dayspgramma = dayspgramma[:10], dayspgramma[10:]
        ax_water.cla()
        ax_water.imshow(np.rot90(dayspgramma), interpolation='none', aspect='auto', cmap='jet', clim=wclim)
        ax_water.set_title("Spectrogram of Ant-%03d"%(opts.antenna) + " Pol-" + opts.pol.upper() + " " + date_path, fontsize=14)
        ax_water.set_ylabel("MHz")
        ax_water.set_xlabel('Time (UTC)')
        ax_water.set_xticks(x_tick)
        ax_water.set_xticklabels(np.array(range(0, 3*9, 3)).astype("str").tolist())
        ystep = 10
        if int(band.split("-")[1]) <= 100:
            ystep = 10
        elif int(band.split("-")[1]) <= 200:
            ystep = 20
        elif int(band.split("-")[1]) > 200:
            ystep = 50
        BW = int(band.split("-")[1]) - int(band.split("-")[0])
        ytic = np.array(range(( BW / ystep) + 1 )) * ystep * (len(np.rot90(dayspgramma)) / float(BW))
        ax_water.set_yticks(len(np.rot90(dayspgramma)) - ytic)
        ylabmax = (np.array(range((BW / ystep) + 1 )) * ystep) + int(band.split("-")[0])
        ax_water.set_yticklabels(ylabmax.astype("str").tolist())

        if len(w_data):
            z_temp = []
            z_wind = []
            z_wdir = []
            z_rain = []
            for n, t in enumerate(t_stamps):
                #print len(t_stamps), n, t, ts_to_datestring(t)
                #sleep(1)
                #if not closest(np.array(w_time), t) == w_time[-1]:
                z_temp += [calc_value(w_time, w_temp, t)]
                #print " * ", ts_to_datestring(t), calc_value(w_time, w_temp, t)
                z_wind += [calc_value(w_time, w_wind, t)]
                z_wdir += [calc_value(w_time, w_wdir, t)]
                z_rain += [calc_value(w_time, w_rain, t)]
            #ax_weather.plot(t_stamps[:len(z_temp)], z_temp, color='r')
            ax_weather.set_ylabel('Temperature (C)', color='r')
            ax_weather.set_xlim(t_stamps[0], t_stamps[-1])
            ax_weather.set_ylim(15, 45)
            ax_weather.set_yticks(np.arange(15, 50, 5))
            ax_weather.set_yticklabels(np.arange(15, 50, 5), color='r')
            ax_weather.grid()
            x_tick = []
            step = 0
            for z in range(len(orari)):
                if orari[z].hour == step:
                    #print str(orari[z])
                    x_tick += [t_stamps[z]]
                    step = step + 3
            #print str(orari[-1])
            x_tick += [t_stamps[len(dayspgramma[10:])]]
            ax_weather.set_xticks(x_tick)
            ax_weather.set_xticklabels(np.array(range(0, 3*9, 3)).astype("str").tolist())

            ax_wind = ax_weather.twinx()
            ax_wind.plot(t_stamps[:len(z_temp)], z_wind, color='b')
            ax_wind.set_ylim(0, 60)
            ax_wind.set_ylabel('Wind (Km/h)', color='b')
            ax_wind.tick_params(axis='y', labelcolor='b')

            ax_rain = ax_weather.twinx()
            ax_rain.plot(t_stamps[:len(z_temp)], z_rain, color='b')
            ax_rain.set_ylim(0, 20)
            ax_rain.set_ylabel('Rain (mm)', color='g')
            ax_rain.tick_params(axis='y', labelcolor='g')
            ax_rain.spines["right"].set_position(("axes", 1.2))
            make_patch_spines_invisible(ax_rain)
            ax_rain.spines["right"].set_visible(True)
            ax_weather.plot(t_stamps[:len(z_temp)], z_temp, color='r')

            # ax_wind.annotate("", xy=(0.5, 0.5), xytext=(0, 0), arrowprops = dict(arrowstyle="->")) # use this for wind direction
            #print z_temp[0:10]

        if not os.path.exists(SPGR_PATH):
            os.makedirs(SPGR_PATH)
        if not os.path.exists(SPGR_PATH + "/" + station_name):
            os.makedirs(SPGR_PATH + "/" + station_name)
        if not os.path.exists(SPGR_PATH + "/" + station_name + "/" + date_path):
            os.makedirs(SPGR_PATH + "/" + station_name + "/" + date_path)
        if not os.path.exists(
                SPGR_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d_ANT-%03d" % (int(tile), int(opts.antenna))):
            os.makedirs(SPGR_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d_ANT-%03d" % (int(tile), int(opts.antenna)))

        fname = SPGR_PATH + "/" + station_name + "/" + date_path + \
                "/TILE-%02d_ANT-%03d/SPGR_"%(int(tile), int(opts.antenna)) + \
                date_path + "_TILE-%02d_ANT-%03d.png"%(int(tile), int(opts.antenna))

        plt.savefig(fname)

    print










