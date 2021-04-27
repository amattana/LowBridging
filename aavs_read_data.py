import matplotlib
# if 'matplotlib.backends' not in sys.modules:
matplotlib.use('agg') # not to use X11
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
    find_ant_by_tile, find_pos_by_name, closest, mro_daily_weather, diclist_to_array, calc_value, get_sbtemp
from matplotlib.markers import MarkerStyle

# Global flag to stop the scrpts
FIG_W = 14
TILE_H = 3.2
PIC_PATH = "/storage/monitoring/pictures"
OPLOT_PATH = "/storage/monitoring/oplot"
SPGR_PATH = "/storage/monitoring/spectrograms"
SPEC_PATH = "/storage/monitoring/spectrum_analyzer"
POWER_PATH = "/storage/monitoring/power/station_power/"
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
    parser.add_option("--average", action="store_true", dest="avg",
                      default=False, help="Produces an average spectrum of a specific antenna")
    parser.add_option("--maxhold", action="store_true", dest="maxhold",
                      default=False, help="Add MaxHold axes")
    parser.add_option("--minhold", action="store_true", dest="minhold",
                      default=False, help="Add MinHold axes")
    parser.add_option("--oplot", action="store_true", dest="oplot",
                      default=False, help="Plot spectra in sequence in the same plot for a specific antenna")
    parser.add_option("--weather", action="store_true", dest="weather",
                      default=False, help="Plot all the weather info if available (Temp, Wind, Rain)")
    parser.add_option("--over", action="store_true", dest="over",
                      default=False, help="Plot weather over waterfall")
    parser.add_option("--startfreq", action="store", dest="startfreq", type="float",
                      default=0, help="Start Frequency")
    parser.add_option("--stopfreq", action="store", dest="stopfreq", type="float",
                      default=400, help="Stop Frequency")
    parser.add_option("--channel", action="store", dest="channel",
                      default="", help="Frequency channel")
    parser.add_option("--pol", action="store", dest="pol",
                      default="x", help="Polarization [x (default)| y]")
    parser.add_option("--power", action="store_true", dest="power",
                      default=False, help="Total Power of channels")
    parser.add_option("--rms", action="store_true", dest="rms",
                      default=False, help="RMS Station Map")
    parser.add_option("--equalize", action="store_true", dest="eq",
                      default=False, help="Equalize antennas power")
    parser.add_option("--noline", action="store_true", dest="noline",
                      default=False, help="Do not plot lines but just markers")
    parser.add_option("--sbtemp", action="store_true", dest="sbtemp",
                      default=False, help="Plot the SmartBox Temperature if available")
    parser.add_option("--temp", action="store_true", dest="temp",
                      default=False, help="Plot the Temperature if available")
    parser.add_option("--wind", action="store_true", dest="wind",
                      default=False, help="Plot the Wind data if available")
    parser.add_option("--rain", action="store_true", dest="rain",
                      default=False, help="Plot the Rain data if available")
    parser.add_option("--last", action="store_true", dest="last",
                      default=False, help="Plot last saved spectrum")
    parser.add_option("--xticks", action="store_true", dest="xticks",
                      default=False, help="Maximize X axis ticks")
    parser.add_option("--yticks", action="store_true", dest="yticks",
                      default=False, help="Maximize Y axis ticks")
    parser.add_option("--yrange", action="store", dest="yrange",
                      default="", help="Comma separated Y range limits")
    parser.add_option("--wclim", action="store", dest="wclim",
                      default="10,35", help="Waterfall Color limits (def: 10,35)")
    parser.add_option("--rangetemp", action="store", dest="rangetemp",
                      default="10,70", help="min,max temperature range")
    parser.add_option("--rangepower", action="store", dest="rangepower",
                      default="12,28", help="min,max rf power range")
    parser.add_option("--scp_server", action="store", dest="scp_server",
                      default="amattana@192.167.189.30", help="scp to a server (user@ip)")
    parser.add_option("--scp_port", action="store", dest="scp_port", type=int,
                      default=5122, help="scp port (default: 5122)")
    parser.add_option("--scp_dir", action="store", dest="scp_dir",
                      default="/home/amattana/scp/", help="scp path (/home/blablabla/)")
    parser.add_option("--scp", action="store_true", dest="scp",
                      default=False, help="scp output file")
    parser.add_option("--test", action="store_true", dest="test",
                      default=False, help="Test arguments and exit")
    parser.add_option("--noplot", action="store_true", dest="noplot",
                      default=False, help="Skip the plot, just save data files")
    parser.add_option("--syncbox", action="store_true", dest="syncbox",
                      default=False, help="For syncbox data ignore zeros test")

    (opts, args) = parser.parse_args(argv[1:])

    t_date = None
    t_start = None
    t_stop = None
    #assex = np.linspace(0, 400, 512)
    asse_x = np.arange(512) * 400/512.
    range_temp_min = int(opts.rangetemp.split(",")[0])
    range_temp_max = int(opts.rangetemp.split(",")[1])
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
                print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
            except:
                print "Bad t_start time format detected (must be YYYY-MM-DD_HH:MM:SS)"
        if opts.stop:
            try:
                t_stop = dt_to_timestamp(datetime.datetime.strptime(opts.stop, "%Y-%m-%d_%H:%M:%S"))
                print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
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
    # if (t_start > datetime.datetime(2020, 3, 1)) and (station_name == "AAVS2"):
    #     print "Patching antenna name and positions"
    #     base = base[:16*13] + base[16*14:]
    #     x = x[:16*13] + x[16*14:]
    #     y = y[:16*13] + y[16*14:]
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
    #print "Tile Inputs: ", (np.array(antenne) + 1).tolist(), "\n"

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

    if opts.power:
        if opts.antenna:
            plot_mode = 3
        else:
            print "Missing antenna argument"
            exit(1)

    if opts.avg:
        if opts.antenna:
            plot_mode = 4
        else:
            print "Missing antenna argument"
            exit(1)

    if opts.oplot:
        if opts.antenna:
            plot_mode = 5
        else:
            print "Missing antenna argument"
            exit(1)

    if opts.rms:
        plot_mode = 6

    if opts.scp:
        print "Enabled Data Transfer: " + opts.scp_server + ":" + str(opts.scp_port) + " dest: " + opts.scp_dir

    if opts.test:
        exit()

    # tile images for videos
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
            lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d*_0.hdf5" % (tile-1)))

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
                if cnt_l < len(lista) - 1:
                    t_file = fname_to_tstamp(lista[cnt_l + 1][-21:-7])
                    if t_file < t_start:
                        continue
                dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile-1))
                if dic:
                    #data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile - 1,
                    #                                          n_samples=dic['n_blocks'])
                    data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile - 1,
                                                              n_samples=200000)
                    cnt = 0
                    if timestamps[0] > t_stop:
                        break
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

                                    scp_fname = PIC_PATH + "/" + station_name + "/" + date_path + \
                                                "/TILE-%02d/TILE-%02d_" % (int(tile_names[en_tile]),
                                                                           int(tile_names[en_tile])) + orario + ".png"
                                    plt.savefig(scp_fname)
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

    # Single antenna plot images for videos
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
        if opts.xticks:
            ax_xpol.set_xticks(np.arange(len(asse_x)))
            ax_xpol.set_xticklabels(["%3.1f"%s for s in asse_x], fontsize=5, rotation=45)
        else:
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
        if opts.xticks:
            ax_ypol.set_xticks(np.arange(len(asse_x)))
            ax_ypol.set_xticklabels(["%3.1f"%s for s in asse_x], fontsize=5, rotation=45)
        else:
            ax_ypol.set_xticks([x*64 for x in range(9)])
            ax_ypol.set_xticklabels([x*50 for x in range(9)], fontsize=10)
        ax_ypol.grid()
        yl, = ax_ypol.plot(range(512), range(512), color='g')

        if not opts.last:
            lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d*_0.hdf5" % (tile - 1)))
            t_cnt = 0
            for cnt_l, l in enumerate(lista):
                if cnt_l < len(lista) - 1:
                    t_file = fname_to_tstamp(lista[cnt_l + 1][-21:-7])
                    if t_file < t_start:
                        continue
                dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile - 1))
                if dic:
                    data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile - 1,
                                                              n_samples=200000)
                    cnt = 0
                    if timestamps[0] > t_stop:
                        break
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
                                    scp_fname = PIC_PATH + "/" + station_name + "/" + \
                                                date_path + "/TILE-%02d_ANT-%03d/TILE-%02d_ANT-%03d_" \
                                                %(int(tile), int(skala_name), int(tile),
                                                  int(skala_name)) + orario + ".png"
                                    plt.savefig(scp_fname)
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
        else:
            # plot just last measurement
            data, timestamps = file_manager.read_data(tile_id=tile - 1, n_samples=1, sample_offset=-1)
            orario = ts_to_datestring(timestamps[0], formato="%Y-%m-%d_%H%M%S")
            for sb_in in antenne:
                with np.errstate(divide='ignore'):
                    spettro = 10 * np.log10(data[:, sb_in, 0, 0])
                xl.set_ydata(spettro)
                with np.errstate(divide='ignore'):
                    spettro = 10 * np.log10(data[:, sb_in, 1, 0])
                yl.set_ydata(spettro)
            time_label.set_text(ts_to_datestring(timestamps[0]))
            plt.savefig(PIC_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d_ANT-%03d/TILE-%02d_ANT-%03d_" %
                        (int(tile), int(skala_name), int(tile), int(skala_name)) + orario + ".png")

    # SPECTROGRAM
    elif plot_mode == 2:

        POL = "Z"

        da = tstamp_to_fname(t_start)[:-6]
        date_path = da[:4] + "-" + da[4:6] + "-" + da[6:]

        band = str("%03d" % int(opts.startfreq)) + "-" + str("%03d" % int(opts.stopfreq))
        if opts.pol.lower() == "x":
            pol = 0
            POL = "X"
        elif opts.pol.lower() == "y":
            pol = 1
            POL = "Y"
        else:
            print "\nWrong value passed for argument pol, using default X pol"
            pol = 0

        row = 4
        if len(w_data) and not opts.over:
            row = row + 1

        gs = GridSpec(row, 1, hspace=0.8, wspace=0.4, left=0.06, bottom=0.1, top=0.95)
        fig = plt.figure(figsize=(14, 9), facecolor='w')

        ax_water = fig.add_subplot(gs[0:4])
        xmin = closest(asse_x, int(opts.startfreq))
        xmax = closest(asse_x, int(opts.stopfreq))

        dayspgramma = np.empty((10, xmax - xmin + 1,))
        dayspgramma[:] = np.nan

        wclim = (10, 35)
        ax_water.cla()
        ax_water.imshow(dayspgramma, interpolation='none', aspect='auto', extent=[xmin, xmax, 60, 0], cmap='jet', clim=wclim)
        ax_water.set_ylabel("Time (minutes)")
        ax_water.set_xlabel('MHz')

        if len(w_data) and not opts.over:
            ax_weather = fig.add_subplot(gs[-1, :])

        tile = find_ant_by_name(opts.antenna)[0]
        lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d*_0.hdf5" % (tile - 1)))
        t_cnt = 0
        orari = []
        t_stamps = []
        for cnt_l, l in enumerate(lista):
            if cnt_l < len(lista) - 1:
                t_file = fname_to_tstamp(lista[cnt_l + 1][-21:-7])
                if t_file < t_start:
                    continue
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile - 1))
            if dic:
                data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile - 1,
                                                          n_samples=200000)
                cnt = 0
                if timestamps[0] > t_stop:
                    break
                if not t_start >= timestamps[-1]:
                    if not t_stop <= timestamps[0]:
                        for i, t in enumerate(timestamps):
                            if t_start <= t[0] <= t_stop:
                                for sb_in in antenne:
                                    with np.errstate(divide='ignore'):
                                        spettro = 10 * np.log10(data[:, sb_in, pol, i])
                                if (not np.sum(data[:, antenne[0], pol, i][120:150]) == 0) and \
                                        (not np.sum(data[:, antenne[0], pol, i][300:350]) == 0):
                                    t_stamps += [t[0]]
                                    orari += [datetime.datetime.utcfromtimestamp(t[0])]
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
        z_tick = []
        x_ticklabels = []
        step = orari[0].hour - 1
        for z in range(len(orari)):
            if not orari[z].hour == step:
                #print str(orari[z])
                x_tick += [z]
                if orari[z].hour == 0:
                    x_ticklabels += [datetime.datetime.strftime(orari[z], "%m-%d")]
                else:
                    x_ticklabels += [orari[z].hour]
                #step = (step + 1) % 24
                step = orari[z].hour
                z_tick += [z]

        div = np.array([1, 2, 3, 4, 6, 8, 12, 24])
        decimation = div[closest(div, len(x_tick) / 24)]
        # print decimation, len(xticks)
        x_tick = x_tick[::decimation]
        x_ticklabels = x_ticklabels[::decimation]

        first_empty, dayspgramma = dayspgramma[:10], dayspgramma[10:]
        ax_water.cla()
        wclim = (int(opts.wclim.split(",")[0]), int(opts.wclim.split(",")[1]))
        ax_water.imshow(np.rot90(dayspgramma), interpolation='none', aspect='auto', cmap='jet', clim=wclim)
        ax_water.set_title("Spectrogram of Ant-%03d"%(opts.antenna) + " Pol-" + opts.pol.upper() + " " + date_path, fontsize=14)
        ax_water.set_ylabel("MHz")
        ax_water.set_xlabel('Time (UTC)')
        ax_water.set_xticks(x_tick)
        ax_water.set_xticklabels(x_ticklabels, rotation=90, fontsize=8)
        ystep = 1
        if int(band.split("-")[1]) <= 20:
            ystep = 1
        elif int(band.split("-")[1]) <= 50:
            ystep = 5
        elif int(band.split("-")[1]) <= 100:
            ystep = 10
        elif int(band.split("-")[1]) <= 200:
            ystep = 20
        elif int(band.split("-")[1]) > 200:
            ystep = 25
        if opts.yticks:
            ystep = 1
        BW = int(band.split("-")[1]) - int(band.split("-")[0])
        ytic = np.array(range(( BW / ystep) + 1 )) * ystep * (len(np.rot90(dayspgramma)) / float(BW))
        ax_water.set_yticks(len(np.rot90(dayspgramma)) - ytic)
        ylabmax = (np.array(range((BW / ystep) + 1 )) * ystep) + int(band.split("-")[0])
        ax_water.set_yticklabels(ylabmax.astype("str").tolist())
        #ax_water.set_xlim(x_tick[0], x_tick[-1])
        ax_water.set_xlim(0, len(orari)-1)

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

            if opts.over:
                x_tick = []
                y_wdir = []
                angle_wdir = []
                step = orari[0].hour
                for z in range(len(orari)):
                    if orari[z].hour == step:
                        x_tick += [t_stamps[z]]
                        y_wdir += [z_wind[z]]
                        angle_wdir += [z_wdir[z]]
                        step = step + 1
                #print str(orari[-1])
                x_tick += [t_stamps[len(dayspgramma[10:])]]

                if opts.temp:
                    ax_weather = ax_water.twinx()
                    ax_weather.plot(z_temp, color='r', lw=1.2)
                    ax_weather.set_ylabel('Temperature (C)', color='r')
                    ax_weather.set_ylim(range_temp_min, range_temp_max)
                    ax_weather.set_yticks(np.arange(range_temp_min, range_temp_max+5, 5))
                    ax_weather.set_yticklabels(np.arange(range_temp_min, range_temp_max+5, 5), color='r')
                    ax_weather.tick_params(axis='y', labelcolor='r')
                    ax_weather.spines["right"].set_position(("axes", 1.))

                if opts.wind:
                    ax_wind = ax_water.twinx()
                    ax_wind.plot(z_wind, color='b', lw=1.2)
                    ax_wind.set_ylim(0, 60)
                    ax_wind.set_ylabel('Wind (Km/h)', color='b')
                    ax_wind.tick_params(axis='y', labelcolor='b')
                    ax_wind.spines["right"].set_position(("axes", 1.08))

                    for a, y in enumerate(y_wdir):
                    #     xs = r * np.cos(np.deg2rad(angle_wdir[a]))
                    #     ys = r * np.sin(np.deg2rad(angle_wdir[a]))
                    #     ax_wind.annotate("", xy=(x_tick[a] + xs, y + ys), xytext=(x_tick[a], y), arrowprops=dict(arrowstyle="->"))
                    #     print a, angle_wdir[a], x_tick[a], y, x_tick[a] + xs, y + ys, r
                        m = MarkerStyle(">")
                        m._transform.rotate_deg(angle_wdir[a])
                        ax_wind.scatter(z_tick[a], y, marker=m, s=100, color='gray')
                        m = MarkerStyle("_")
                        m._transform.rotate_deg(angle_wdir[a])
                        ax_wind.scatter(z_tick[a], y, marker=m, s=400, color='gray')

                if opts.rain:
                    ax_rain = ax_water.twinx()
                    ax_rain.plot(z_rain, color='g', lw=1.2)
                    ax_rain.set_ylim(0, 20)
                    ax_rain.set_ylabel('Rain (mm)', color='g')
                    ax_rain.tick_params(axis='y', labelcolor='g')
                    ax_rain.spines["right"].set_position(("axes", 1.16))
                fig.subplots_adjust(right=0.8)

            else:
                if opts.temp:
                    #ax_weather.plot(t_stamps[:len(z_temp)], z_temp, color='r')
                    ax_weather.set_ylabel('Temperature (C)', color='r')
                    ax_weather.set_xlim(t_stamps[0], t_stamps[-1])
                    ax_weather.set_ylim(range_temp_min, range_temp_max)
                    ax_weather.set_yticks(np.arange(range_temp_min, range_temp_max+5, 5))
                    ax_weather.set_yticklabels(np.arange(range_temp_min, range_temp_max+5, 5), color='r')
                    ax_weather.grid()
                    x_tick = []
                    y_wdir = []
                    angle_wdir = []
                    step = orari[0].hour
                    for z in range(len(orari)):
                        if orari[z].hour == step:
                            x_tick += [t_stamps[z]]
                            y_wdir += [z_wind[z]]
                            angle_wdir += [z_wdir[z]]
                            step = step + 1
                    #print str(orari[-1])
                    x_tick += [t_stamps[len(dayspgramma[10:])]]
                    ax_weather.set_xticks(x_tick)
                    ax_weather.set_xticklabels((np.array(range(0, len(x_tick), 1)) + orari[0].hour).astype("str").tolist())
                    ax_weather.plot(t_stamps[:len(z_temp)], z_temp, color='r', lw=1.5)

                if opts.rain:
                    ax_wind = ax_weather.twinx()
                    ax_wind.plot(t_stamps[:len(z_temp)], z_wind, color='b', lw=1.5)
                    ax_wind.set_ylim(0, 60)
                    ax_wind.set_ylabel('Wind (Km/h)', color='b')
                    ax_wind.tick_params(axis='y', labelcolor='b')

                    # Draw wind direction
                    # r = 20
                    for a, y in enumerate(w_wdir):
                    #     xs = r * np.cos(np.deg2rad(angle_wdir[a]))
                    #     ys = r * np.sin(np.deg2rad(angle_wdir[a]))
                    #     ax_wind.annotate("", xy=(x_tick[a] + xs, y + ys), xytext=(x_tick[a], y), arrowprops=dict(arrowstyle="->"))
                    #     print a, angle_wdir[a], x_tick[a], y, x_tick[a] + xs, y + ys, r
                        if not a % 4:
                            m = MarkerStyle(">")
                            m._transform.rotate_deg(angle_wdir[a])
                            ax_wind.scatter(w_time[a], y, marker=m, s=100, color='g')
                            m = MarkerStyle("_")
                            m._transform.rotate_deg(angle_wdir[a])
                            ax_wind.scatter(w_time[a], y, marker=m, s=500, color='g')

                if opts.rain:
                    ax_rain = ax_weather.twinx()
                    ax_rain.plot(t_stamps[:len(z_temp)], z_rain, color='g', lw=1.5)
                    ax_rain.set_ylim(0, 20)
                    ax_rain.set_ylabel('Rain (mm)', color='g')
                    ax_rain.tick_params(axis='y', labelcolor='g')
                    ax_rain.spines["right"].set_position(("axes", 1.06))
                #make_patch_spines_invisible(ax_rain)
                #ax_rain.spines["right"].set_visible(True)

                # ax_wind.annotate("", xy=(0.5, 0.5), xytext=(0, 0), arrowprops = dict(arrowstyle="->")) # use this for wind direction
                #print z_temp[0:10]

                fig.subplots_adjust(right=0.9)

        if not os.path.exists(SPGR_PATH):
            os.makedirs(SPGR_PATH)
        if not os.path.exists(SPGR_PATH + "/" + station_name):
            os.makedirs(SPGR_PATH + "/" + station_name)
        if not os.path.exists(
                SPGR_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d" % (int(tile), int(opts.antenna))):
            os.makedirs(SPGR_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d" % (int(tile), int(opts.antenna)))
        if not os.path.exists(
                SPGR_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d/POL-%s" % (int(tile), int(opts.antenna), POL)):
            os.makedirs(SPGR_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d/POL-%s" % (int(tile), int(opts.antenna), POL))

        scp_fname = SPGR_PATH + "/" + station_name + \
                "/TILE-%02d_ANT-%03d/POL-%s/SPGR_"%(int(tile), int(opts.antenna), POL) + \
                date_path + "_TILE-%02d_ANT-%03d_POL-%s.png"%(int(tile), int(opts.antenna), POL)

        plt.savefig(scp_fname)
        sys.stdout.write(ERASE_LINE + "\nOutput File: " + scp_fname + "\n")
        sys.stdout.flush()

    # Channel POWER
    elif plot_mode == 3:

        POL = "Z"

        da = tstamp_to_fname(t_start)[:-6]
        date_path = da[:4] + "-" + da[4:6] + "-" + da[6:]

        #band = str("%03d" % int(opts.startfreq)) + "-" + str("%03d" % int(opts.stopfreq))
        if opts.pol.lower() == "x":
            pol = 0
            POL = "X"
        elif opts.pol.lower() == "y":
            pol = 1
            POL = "Y"
        else:
            print "\nWrong value passed for argument pol, using default X pol"
            pol = 0

        if not opts.noplot:
            gs = GridSpec(1, 1, left=0.06, bottom=0.1, top=0.95)
            fig = plt.figure(figsize=(14, 9), facecolor='w')

            ax_power = fig.add_subplot(gs[0, 0])
            if "all" in opts.date.lower():
                delta = (dt_to_timestamp(datetime.datetime.utcnow().date() + datetime.timedelta(1)) -
                         dt_to_timestamp(datetime.datetime(2020, 03, 01)))
                delta_h = delta / 3600
                x = np.array(range(delta)) + t_start
            else:
                delta_h = (t_stop - t_start) / 3600
                x = np.array(range(t_stop - t_start)) + t_start

            xticks = np.array(range(delta_h)) * 3600 + t_start
            xticklabels = [f if f != 0 else datetime.datetime.strftime(
                datetime.datetime.utcfromtimestamp(t_start) + datetime.timedelta(n / 24), "%m-%d") for n, f in
                           enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) % 24)]

            div = np.array([1, 2, 3, 4, 6, 8, 12, 24])
            decimation = div[closest(div, len(xticks) / 24)]
            # print decimation, len(xticks)
            xticks = xticks[::decimation]
            xticklabels = xticklabels[::decimation]

            ax_power.plot(x, x, color='w')
            ax_power.set_xticks(xticks)
            ax_power.set_xticklabels(xticklabels, rotation=90, fontsize=8)

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

        if not opts.noplot:
            if len(w_data) and not opts.over:
                ax_weather = ax_power.twinx()

        tile = find_ant_by_name(opts.antenna)[0]
        lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d*_0.hdf5" % (tile - 1)))
        t_cnt = 0
        orari = []
        t_stamps = []
        acc_power_x = []
        acc_power_y = []
        for cnt_l, l in enumerate(lista):
            if cnt_l < len(lista) - 1:
                t_file = fname_to_tstamp(lista[cnt_l + 1][-21:-7])
                if t_file < t_start:
                    continue
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile - 1))
            if dic:
                data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile - 1,
                                                          n_samples=200000)
                cnt = 0
                if timestamps[0] > t_stop:
                    break
                if not t_start >= timestamps[-1]:
                    if not t_stop <= timestamps[0]:
                        for i, t in enumerate(timestamps):
                            if t_start <= t[0] <= t_stop:
                                for sb_in in antenne:
                                    spettro_x = data[:, sb_in, 0, i]
                                    spettro_y = data[:, sb_in, 1, i]
                                if opts.syncbox:
                                    t_stamps += [t[0]]
                                    orari += [datetime.datetime.utcfromtimestamp(t[0])]
                                    if xmin == 0:
                                        with np.errstate(divide='ignore'):
                                            acc_power_x += [10 * np.log10(np.sum(spettro_x[:xmax + 1]))]
                                            acc_power_y += [10 * np.log10(np.sum(spettro_y[:xmax + 1]))]
                                    else:
                                        with np.errstate(divide='ignore'):
                                            acc_power_x += [10 * np.log10(np.sum(spettro_x[xmin:xmax + 1]))]
                                            acc_power_y += [10 * np.log10(np.sum(spettro_y[xmin:xmax + 1]))]
                                else:
                                    if not np.sum(spettro_x[20:50]) == 0:
                                        if not np.sum(spettro_x[20:210]) == 0:
                                            if not np.sum(spettro_x[300:350]) == 0:
                                                t_stamps += [t[0]]
                                                orari += [datetime.datetime.utcfromtimestamp(t[0])]
                                                if xmin == 0:
                                                    with np.errstate(divide='ignore'):
                                                        acc_power_x += [10 * np.log10(np.sum(spettro_x[:xmax + 1]))]
                                                        acc_power_y += [10 * np.log10(np.sum(spettro_y[:xmax + 1]))]
                                                else:
                                                    with np.errstate(divide='ignore'):
                                                        acc_power_x += [10 * np.log10(np.sum(spettro_x[xmin:xmax + 1]))]
                                                        acc_power_y += [10 * np.log10(np.sum(spettro_y[xmin:xmax + 1]))]
                                msg = "\rProcessing " + ts_to_datestring(t[0])
                                sys.stdout.write(ERASE_LINE + msg)
                                sys.stdout.flush()

            msg = "\r[%d/%d] File: %s" % (cnt_l + 1, len(lista), l.split("/")[-1]) + "   " + ts_to_datestring(
                timestamps[0][0]) + "   " + ts_to_datestring(timestamps[-1][0])
            sys.stdout.write(ERASE_LINE + msg)
            sys.stdout.flush()

        # y_wdir = []
        # angle_wdir = []
        # for z in range(len(orari)):
        #     if orari[z].hour == step:
        #         if len(w_data):
        #             y_wdir += [w_wind[int(closest(np.array(w_time), t_stamps[z]))]]
        #             angle_wdir += [w_wdir[int(closest(np.array(w_time), t_stamps[z]))]]

        if not opts.noplot:
            ax_power.set_xlim(t_stamps[0], t_stamps[-1])
            if opts.noline:
                ax_power.plot(t_stamps, acc_power_x, color='b', label='Pol-X', linestyle='None', marker=".", markersize=2)
                ax_power.plot(t_stamps, acc_power_y, color='g', label='Pol-Y', linestyle='None', marker=".", markersize=2)
            else:
                ax_power.plot(t_stamps, acc_power_x, color='b', label='Pol-X')
                ax_power.plot(t_stamps, acc_power_y, color='g', label='Pol-Y')
            ax_power.set_xlabel("Time", fontsize=14)
            ax_power.set_ylabel("dB", fontsize=14)
            ax_power.set_yticks(np.arange(0, 101, 1))
            #print "\nDEBUG:", acc_power_x[0:6], "\n"
            #ax_power.set_ylim(int(np.mean(np.array(acc_power_x)[np.array(acc_power_x) != -np.inf])) - 6,
            #                  int(np.mean(np.array(acc_power_x)[np.array(acc_power_x) != -np.inf])) + 10)
            ax_power.set_ylim(int(opts.rangepower.split(",")[0]), int(opts.rangepower.split(",")[1]))
            ax_power.grid()
            ax_power.legend(fancybox=True, framealpha=1, shadow=True, borderpad=1, ncol=8, #bbox_to_anchor=(-0.02, -0.2),
                              loc='lower left', fontsize='small', markerscale=4)
            title = station_name + "  Power of Ant-%03d"%(opts.antenna) + " from " + ts_to_datestring(t_start) + " to " + ts_to_datestring(t_stop)
            if not xmin == xmax:
                title += "  Frequencies: " + str(opts.startfreq) + "-" + str(opts.stopfreq) + " MHz  (channels %d-%d)" % (xmin,xmax)
            else:
                title += "  Frequency: %3.1f MHz  (channel %d)" % (asse_x[xmin], xmin)

            ax_power.set_title(title, fontsize=14)

            if len(w_data):
                if opts.temp:
                    ax_weather.set_ylabel('Temperature (C)', color='r')
                    #ax_weather.set_xlim(t_stamps[0], t_stamps[-1])
                    ax_weather.set_ylim(range_temp_max, range_temp_min)
                    ax_weather.set_yticks(np.arange(range_temp_min, range_temp_max, 5))
                    ax_weather.set_yticklabels(np.arange(range_temp_min, range_temp_max, 5), color='r')
                    ax_weather.plot(w_time, w_temp, color='r', lw=1.5, label='External Temp')

                    if opts.sbtemp:
                        sb_tempi, sb_dati = get_sbtemp(t_start, t_stop)
                        if sb_dati:
                            #ax_weather.plot(sb_tempi, sb_dati, color='purple', linestyle='None', marker=".", markersize=2, label='SmartBox Internal Temp')
                            ax_weather.plot(sb_tempi, sb_dati, color='purple', label='SmartBox Internal Temp')
                        else:
                            print "\nNo SmartBox Temperature available!"
                    ax_weather.legend(fancybox=True, framealpha=1, shadow=True, borderpad=1, ncol=8,#bbox_to_anchor=(1-0.2, 1-0.2)
                                      loc="lower right", fontsize='small')

                if opts.wind:
                    ax_wind = ax_power.twinx()
                    ax_wind.plot(w_time, w_wind, color='orange', lw=1.5)
                    ax_wind.set_ylim(80, 0)
                    ax_wind.set_ylabel('Wind (Km/h)', color='orange')
                    ax_wind.tick_params(axis='y', labelcolor='orange')
                    ax_wind.spines["right"].set_position(("axes", 1.06))
                    # Draw wind direction
                    for a in range(len(w_wdir)):
                        if not a % (len(w_wdir)/24):
                            m = MarkerStyle(">")
                            m._transform.rotate_deg(w_wdir[a])
                            # print a, xticks[a], w_wind[a], len(xticks), len(w_wind)
                            ax_wind.scatter(w_time[a], w_wind[a], marker=m, s=100, color='orchid')
                            m = MarkerStyle("_")
                            m._transform.rotate_deg(w_wdir[a])
                            ax_wind.scatter(w_time[a], w_wind[a], marker=m, s=500, color='orchid')

                if opts.rain:
                    ax_rain = ax_power.twinx()
                    ax_rain.plot(w_time, w_rain, color='cyan', lw=3)
                    ax_rain.set_ylim(100, 0)
                    ax_rain.set_ylabel('Rain (mm)', color='cyan')
                    ax_rain.tick_params(axis='y', labelcolor='cyan')
                    ax_rain.spines["right"].set_position(("axes", 1.12))

                fig.subplots_adjust(right=0.86)


        # if not os.path.exists(POWER_PATH):
        #     os.makedirs(POWER_PATH)
        # if not os.path.exists(POWER_PATH + "/" + station_name):
        #     os.makedirs(POWER_PATH + "/" + station_name)
        # if not os.path.exists(
        #         POWER_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d" % (int(tile), int(opts.antenna))):
        #     os.makedirs(POWER_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d" % (int(tile), int(opts.antenna)))
        # if not os.path.exists(
        #         POWER_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d/data" % (int(tile), int(opts.antenna))):
        #     os.makedirs(POWER_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d/data" % (int(tile), int(opts.antenna)))
        # if not os.path.exists(
        #         POWER_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d/pic" % (int(tile), int(opts.antenna))):
        #     os.makedirs(POWER_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d/pic" % (int(tile), int(opts.antenna)))
        # if not os.path.exists(
        #         POWER_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d/POL-%s" % (int(tile), int(opts.antenna), POL)):
        #     os.makedirs(POWER_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d/POL-%s" % (int(tile), int(opts.antenna), POL))

        # data_fname = POWER_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d/data/POWER_"%(int(tile),
        #               int(opts.antenna)) + date_path + "_TILE-%02d_ANT-%03d_POL-X_BAND-%d-%dMHz.txt" % \
        #              (int(tile), int(opts.antenna), int(opts.startfreq), int(opts.stopfreq))
        t_date = datetime.datetime.strftime(datetime.datetime.strptime(opts.start, "%Y-%m-%d_%H:%M:%S"), "%Y-%m-%d")
        opath = POWER_PATH + t_date
        if not os.path.exists(opath):
            os.makedirs(opath)
        opath += "/" + station_name + "_" + str("%03d" % int(asse_x[xmin])) + "MHz"
        if not os.path.exists(opath):
            os.makedirs(opath)
        if not os.path.exists(opath + "/power_data/"):
            os.makedirs(opath + "/power_data/")
        data_fname = opath + "/power_data/" + station_name + "_POWER_" + date_path + \
                     "_TILE-%02d_ANT-%03d_POL-X_BAND-%d-%dMHz.txt" % \
                     (int(tile), int(opts.antenna), int(asse_x[xmin]), int(asse_x[xmax]))
        with open(data_fname, "w") as ft:
            ft.write("Tstamp\tDate\tTime\tdB\n")
            for n, q in enumerate(acc_power_x):
                ft.write("%d\t%s\t%6.3f\n" % (t_stamps[n], ts_to_datestring(t_stamps[n], "%Y-%m-%d\t%H:%M:%S"), q))
        sys.stdout.write(ERASE_LINE + "\nOutput File: " + data_fname + "\n")
        sys.stdout.flush()

        # data_fname = POWER_PATH + "/" + station_name + "/TILE-%02d_ANT-%03d/data/POWER_"%(int(tile),
        #               int(opts.antenna)) + date_path + "_TILE-%02d_ANT-%03d_POL-Y_BAND-%d-%dMHz.txt" % \
        #              (int(tile), int(opts.antenna), int(opts.startfreq), int(opts.stopfreq))
        data_fname = opath + "/power_data/" + station_name + "_POWER_" + date_path + \
                     "_TILE-%02d_ANT-%03d_POL-Y_BAND-%d-%dMHz.txt" % \
                     (int(tile), int(opts.antenna), int(asse_x[xmin]), int(asse_x[xmax]))
        with open(data_fname, "w") as ft:
            ft.write("Tstamp\tDate\tTime\tdB\n")
            for n, q in enumerate(acc_power_y):
                ft.write("%d\t%s\t%6.3f\n" % (t_stamps[n], ts_to_datestring(t_stamps[n], "%Y-%m-%d\t%H:%M:%S"), q))
        sys.stdout.write(ERASE_LINE + "\nOutput File: " + data_fname + "\n")
        sys.stdout.flush()

        # scp_fname = POWER_PATH + "/" + station_name + \
        #         "/TILE-%02d_ANT-%03d/pic/" + station_name + "_POWER_"%(int(tile), int(opts.antenna)) + \
        #         date_path + "_TILE-%02d_ANT-%03d.png"%(int(tile), int(opts.antenna))

        if not opts.noplot:
            if not os.path.exists(opath + "/power_pics/"):
                os.makedirs(opath + "/power_pics/")
            scp_fname = opath + "/power_pics/" + station_name + "_POWER_" + date_path + "_TILE-%02d_ANT-%03d.png" % \
                        (int(tile), int(opts.antenna))

            plt.savefig(scp_fname)
            sys.stdout.write(ERASE_LINE + "\nOutput File: " + scp_fname + "\n")
            sys.stdout.flush()

    # AVERAGE
    elif plot_mode == 4:

        POL = "Z"

        da = tstamp_to_fname(t_start)[:-6]
        date_path = da[:4] + "-" + da[4:6] + "-" + da[6:]

        band = str("%03d" % int(opts.startfreq)) + "-" + str("%03d" % int(opts.stopfreq))
        POLs = ["X", "Y"]
        spectra_x = np.zeros(512)
        spectra_y = np.zeros(512)

        tile = find_ant_by_name(opts.antenna)[0]
        lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d*_0.hdf5" % (tile - 1)))
        t_cnt_x = 0
        t_cnt_y = 0
        orari = []
        t_stamps = []
        for cnt_l, l in enumerate(lista):
            if cnt_l < len(lista) - 1:
                t_file = fname_to_tstamp(lista[cnt_l + 1][-21:-7])
                if t_file < t_start:
                    continue
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile - 1))
            if dic:
                data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile - 1,
                                                          n_samples=200000)
                cnt = 0
                if timestamps[0] > t_stop:
                    break
                if not t_start >= timestamps[-1]:
                    if not t_stop <= timestamps[0]:
                        for i, t in enumerate(timestamps):
                            if t_start <= t[0] <= t_stop:
                                # POL-X
                                for sb_in in antenne:
                                    spettro_x = np.array(data[:, sb_in, 0, i])
                                if (not np.sum(spettro_x[120:150]) == 0) and \
                                        (not np.sum(spettro_x[300:350]) == 0):
                                    spectra_x += spettro_x
                                    if not t_cnt_x:
                                        if opts.maxhold:
                                            max_hold_x = spettro_x
                                        if opts.minhold:
                                            min_hold_x = spettro_x
                                    else:
                                        if opts.maxhold:
                                            max_hold_x = np.maximum(max_hold_x, spettro_x)
                                        if opts.minhold:
                                            min_hold_x = np.minimum(min_hold_x, spettro_x)
                                    t_cnt_x = t_cnt_x + 1
                                # POL-Y
                                for sb_in in antenne:
                                    spettro_y = np.array(data[:, sb_in, 1, i])
                                if (not np.sum(spettro_y[120:150]) == 0) and \
                                        (not np.sum(spettro_y[300:350]) == 0):
                                    spectra_y += spettro_y
                                    if not t_cnt_y:
                                        if opts.maxhold:
                                            max_hold_y = spettro_y
                                        if opts.minhold:
                                            min_hold_y = spettro_y
                                    else:
                                        if opts.maxhold:
                                            max_hold_y = np.maximum(max_hold_y, spettro_y)
                                        if opts.minhold:
                                            min_hold_y = np.minimum(min_hold_y, spettro_y)
                                    t_cnt_y = t_cnt_y + 1
                                msg = "\rProcessing " + ts_to_datestring(t[0])
                                sys.stdout.write(ERASE_LINE + msg)
                                sys.stdout.flush()

            msg = "\r[%d/%d] File: %s" % (cnt_l + 1, len(lista), l.split("/")[-1]) + "   " + ts_to_datestring(
                timestamps[0][0]) + "   " + ts_to_datestring(timestamps[-1][0])
            sys.stdout.write(ERASE_LINE + msg)
            sys.stdout.flush()
        sys.stdout.write(ERASE_LINE + "\rAveraging spectra...\n")
        sys.stdout.flush()

        avg_spectrum_x = spectra_x / t_cnt_x
        avg_spectrum_y = spectra_y / t_cnt_y
        with np.errstate(divide='ignore'):
            log_spectrum_x = 10 * np.log10(avg_spectrum_x)
            if opts.maxhold:
                max_hold_x = 10 * np.log10(max_hold_x)
            if opts.minhold:
                min_hold_x = 10 * np.log10(min_hold_x)
            log_spectrum_y = 10 * np.log10(avg_spectrum_y)
            if opts.maxhold:
                max_hold_y = 10 * np.log10(max_hold_y)
            if opts.minhold:
                min_hold_y = 10 * np.log10(min_hold_y)

        if not os.path.exists(SPEC_PATH):
            os.makedirs(SPEC_PATH)
        if not os.path.exists(SPEC_PATH + "/" + station_name):
            os.makedirs(SPEC_PATH + "/" + station_name)
        outpath = SPEC_PATH + "/" + station_name + ts_to_datestring(t_start, formato="/%Y-%m-%d")
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        out_data_path = outpath + "/data"
        if not os.path.exists(out_data_path):
            os.makedirs(out_data_path)
        out_data_path += "/"
        out_img_path = outpath + "/img"
        if not os.path.exists(out_img_path):
            os.makedirs(out_img_path)
        out_img_path += "/"

        sys.stdout.write("\nData directory: " + out_data_path)
        sys.stdout.flush()

        sys.stdout.write("\nImg directory: " + out_img_path)
        sys.stdout.flush()

        gs = GridSpec(1, 1, hspace=0.8, wspace=0.4, left=0.06, right=0.92, bottom=0.1, top=0.95)
        fig = plt.figure(figsize=(12, 7), facecolor='w')
        ax = fig.add_subplot(gs[0])
        #xmin = closest(asse_x, int(opts.startfreq))
        #xmax = closest(asse_x, int(opts.stopfreq))

        if opts.maxhold:
            ax.plot(asse_x, max_hold_x, label="Max Hold", color='r')
        ax.plot(asse_x, log_spectrum_x, label="Average", color='g')
        if opts.minhold:
            ax.plot(asse_x, min_hold_x, label="Min Hold", color='b')
        ax.set_title("Spectrum of Ant-%03d"%(opts.antenna) + "  Pol-X    Time Range from " +
                     opts.start + " to " + opts.stop, fontsize=14)
        ax.set_xlabel("MHz")
        ax.set_ylabel('dB')
        ax.set_yticks(range(0, 55, 5))
        if not opts.yrange == "":
            ax.set_ylim(float(opts.yrange.split(",")[0]), float(opts.yrange.split(",")[1]))
        else:
            ax.set_ylim(0, 50)
        ax.grid()
        if opts.xticks:
            ax.set_xticks(asse_x)
            lab = ["%3.1f"%j for j in asse_x]
            ax.set_xticklabels(lab, rotation=90, fontsize=6)
        else:
            ax.set_xticks(range(0, 450, 50))
        ax.set_xlim(int(opts.startfreq), int(opts.stopfreq))
        ax.legend(fancybox=True, framealpha=1, shadow=True, borderpad=1, ncol=8,#bbox_to_anchor=(1-0.2, 1-0.2)
                                  loc="lower center", fontsize='small', markerscale=8)

        scp_fname = "SPECTRUM_TILE-%02d_ANT-%03d_Pol-X_Start_%s_Stop_%s.png" % \
                (int(tile), int(opts.antenna), ts_to_datestring(t_start, formato="%Y-%m-%d_%H%M%S"),
                 ts_to_datestring(t_stop, formato="%Y-%m-%d_%H%M%S"))
        scp_fname = out_img_path + scp_fname
        plt.savefig(scp_fname)

        if opts.maxhold:
            data_fname = scp_fname[:-4] + "_maxhold.txt"
            with open(data_fname, "w") as ft:
                for k in max_hold_x:
                    ft.write("%6.3f\n" % (k))

        if opts.maxhold:
            data_fname = scp_fname[:-4] + "_minhold.txt"
            with open(data_fname, "w") as ft:
                for k in min_hold_x:
                    ft.write("%6.3f\n" % (k))

        data_fname = scp_fname[:-4] + "_average.txt"
        with open(data_fname, "w") as ft:
            for k in log_spectrum_x:
                ft.write("%6.3f\n" % (k))

        sys.stdout.write("\n\nAveraged Spectra X " + str(t_cnt_x) + ",  Averaged Spectra Y " + str(t_cnt_y) + "\nSaved file: " + scp_fname)
        sys.stdout.flush()

        ax.cla()
        if opts.maxhold:
            ax.plot(asse_x, max_hold_y, label="Max Hold", color='r')
        ax.plot(asse_x, log_spectrum_y, label="Average", color='g')
        if opts.minhold:
            ax.plot(asse_x, min_hold_y, label="Min Hold", color='b')
        ax.set_title("Spectrum of Ant-%03d"%(opts.antenna) + "  Pol-Y    Time Range from " +
                     opts.start + " to " + opts.stop, fontsize=14)
        ax.set_xlabel("MHz")
        ax.set_ylabel('dB')
        ax.set_yticks(range(0, 55, 5))
        ax.set_ylim(0, 50)
        if not opts.yrange == "":
            ax.set_ylim(float(opts.yrange.split(",")[0]), float(opts.yrange.split(",")[1]))
        ax.grid()
        if opts.xticks:
            ax.set_xticks(asse_x)
            lab = ["%3.1f"%j for j in asse_x]
            ax.set_xticklabels(lab, rotation=90, fontsize=6)
        else:
            ax.set_xticks(range(0, 450, 50))
        ax.set_xlim(int(opts.startfreq), int(opts.stopfreq))
        ax.legend(fancybox=True, framealpha=1, shadow=True, borderpad=1, ncol=8,#bbox_to_anchor=(1-0.2, 1-0.2)
                                  loc="lower center", fontsize='small', markerscale=8)

        scp_fname = "SPECTRUM_TILE-%02d_ANT-%03d_Pol-Y_Start_%s_Stop_%s.png" % \
                (int(tile), int(opts.antenna), ts_to_datestring(t_start, formato="%Y-%m-%d_%H%M%S"),
                 ts_to_datestring(t_stop, formato="%Y-%m-%d_%H%M%S"))
        scp_fname = out_img_path + scp_fname
        plt.savefig(scp_fname)

        if opts.maxhold:
            data_fname = scp_fname[:-4] + "_maxhold.txt"
            with open(data_fname, "w") as ft:
                for k in max_hold_y:
                    ft.write("%6.3f\n" % (k))

        if opts.maxhold:
            data_fname = scp_fname[:-4] + "_minhold.txt"
            with open(data_fname, "w") as ft:
                for k in min_hold_y:
                    ft.write("%6.3f\n" % (k))

        data_fname = scp_fname[:-4] + "_average.txt"
        with open(data_fname, "w") as ft:
            for k in log_spectrum_y:
                ft.write("%6.3f\n" % (k))

        sys.stdout.write("\nSaved file: " + scp_fname)
        sys.stdout.flush()

    # OPLOT
    elif plot_mode == 5:

        tile = tiles[0]
        if not opts.antenna:
            skala_name = find_ant_by_tile(tile, antenne[0])
        else:
            skala_name = opts.antenna
        da = tstamp_to_fname(t_start)[:-6]
        date_path = da[:4] + "-" + da[4:6] + "-" + da[6:]

        if not os.path.exists(OPLOT_PATH):
            os.makedirs(OPLOT_PATH)
        if not os.path.exists(OPLOT_PATH + "/" + station_name):
            os.makedirs(OPLOT_PATH + "/" + station_name)
        if not os.path.exists(OPLOT_PATH + "/" + station_name + "/" + date_path):
            os.makedirs(OPLOT_PATH + "/" + station_name + "/" + date_path)
        if not os.path.exists(
                OPLOT_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d_ANT-%03d" % (int(tile), int(skala_name))):
            os.makedirs(OPLOT_PATH + "/" + station_name + "/" + date_path + "/TILE-%02d_ANT-%03d" % (int(tile), int(skala_name)))

        grid = GridSpec(15, 8, hspace=1.2, wspace=0.4, left=0.08, right=0.98, bottom=0.1, top=0.98)
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
        time_label = ax_top_label.annotate("from " + opts.start + " to " + opts.stop, (-20, 0), fontsize=10, color='black')

        ax_top_tile = fig.add_subplot(grid[0:3, 0:4])
        ax_top_tile.cla()
        ax_top_tile.plot([0.001, 0.002], color='w')
        ax_top_tile.set_xlim(-20, 20)
        ax_top_tile.set_ylim(-20, 20)
        title = ax_top_tile.annotate("TILE: "+str(tile) + "    Antenna: " + str(skala_name), (-20, 0), fontsize=22, color='black')
        ax_top_tile.set_axis_off()

        ax_xpol = fig.add_subplot(grid[3:9, :])
        ax_xpol.tick_params(axis='both', which='both', labelsize=8)
        ax_xpol.set_ylim(0, 50)
        ax_xpol.set_xlim(0, 512)
        ax_xpol.set_title("Pol-X")
        ax_xpol.set_xlabel("MHz", fontsize=10)
        ax_xpol.set_ylabel("dB", fontsize=12)
        if opts.xticks:
            ax_xpol.set_xticks(np.arange(len(asse_x)))
            ax_xpol.set_xticklabels(["%3.1f"%s for s in asse_x], fontsize=3, rotation=90)
        else:
            ax_xpol.set_xticks([x*64 for x in range(9)])
            ax_xpol.set_xticklabels([x*50 for x in range(9)], fontsize=8)
        ax_xpol.grid()
        xl, = ax_xpol.plot(range(512), range(512), color='w')

        ax_ypol = fig.add_subplot(grid[10:, :])
        ax_ypol.tick_params(axis='both', which='both', labelsize=8)
        ax_ypol.set_title("Pol-Y")
        ax_ypol.set_ylim(0, 50)
        ax_ypol.set_xlim(0, 512)
        ax_ypol.set_xlabel("MHz", fontsize=10)
        ax_ypol.set_ylabel("dB", fontsize=12)
        if opts.xticks:
            ax_ypol.set_xticks(np.arange(len(asse_x)))
            ax_ypol.set_xticklabels(["%3.1f"%s for s in asse_x], fontsize=3, rotation=90)
        else:
            ax_ypol.set_xticks([x*64 for x in range(9)])
            ax_ypol.set_xticklabels([x*50 for x in range(9)], fontsize=8)
        ax_ypol.grid()
        yl, = ax_ypol.plot(range(512), range(512), color='w')

        da = tstamp_to_fname(t_start)[:-6]
        date_path = da[:4] + "-" + da[4:6] + "-" + da[6:]

        tile = find_ant_by_name(opts.antenna)[0]
        lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d*_0.hdf5" % (tile - 1)))
        t_cnt_x = 0
        t_cnt_y = 0
        orari = []
        t_stamps = []
        for cnt_l, l in enumerate(lista):
            if cnt_l < len(lista) - 1:
                t_file = fname_to_tstamp(lista[cnt_l + 1][-21:-7])
                if t_file < t_start:
                    continue
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(tile - 1))
            if dic:
                data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=tile - 1,
                                                          n_samples=200000)
                cnt = 0
                if timestamps[0] > t_stop:
                    break
                if not t_start >= timestamps[-1]:
                    if not t_stop <= timestamps[0]:
                        for i, t in enumerate(timestamps):
                            if t_start <= t[0] <= t_stop:
                                # POL-X
                                for sb_in in antenne:
                                    spettro = np.array(data[:, sb_in, 0, i])
                                if (not np.sum(spettro[120:150]) == 0) and \
                                        (not np.sum(spettro[300:350]) == 0):
                                    with np.errstate(divide='ignore'):
                                        spettro = 10 * np.log10(spettro)
                                        ax_xpol.plot(spettro)
                                # POL-Y
                                for sb_in in antenne:
                                    spettro = np.array(data[:, sb_in, 1, i])
                                if (not np.sum(spettro[120:150]) == 0) and \
                                        (not np.sum(spettro[300:350]) == 0):
                                    with np.errstate(divide='ignore'):
                                        spettro = 10 * np.log10(spettro)
                                        ax_ypol.plot(spettro)
                                msg = "\rProcessing " + ts_to_datestring(t[0])
                                sys.stdout.write(ERASE_LINE + msg)
                                sys.stdout.flush()

            msg = "\r[%d/%d] File: %s" % (cnt_l + 1, len(lista), l.split("/")[-1]) + "   " + ts_to_datestring(
                timestamps[0][0]) + "   " + ts_to_datestring(timestamps[-1][0])
            sys.stdout.write(ERASE_LINE + msg)
            sys.stdout.flush()

        xmin = closest(asse_x, int(opts.startfreq))
        xmax = closest(asse_x, int(opts.stopfreq))
        ax_xpol.set_xlim(xmin, xmax)
        ax_ypol.set_xlim(xmin, xmax)
        scp_fname = OPLOT_PATH + "/" + station_name + "/" + date_path + \
                "/TILE-%02d_ANT-%03d/TILE-%02d_ANT-%03d.png"%(int(tile), int(skala_name), int(tile), int(skala_name))

        plt.savefig(scp_fname)
        print "\nSaved file: " + scp_fname

    # RMS MAP
    elif plot_mode == 6:

        antenne = range(16)
        da = tstamp_to_fname(t_start)[:-6]
        date_path = da[:4] + "-" + da[4:6] + "-" + da[6:]

        gs = GridSpec(1, 2, left=0.06, bottom=0.1, top=0.95)
        fig = plt.figure(figsize=(14, 9), facecolor='w')

        ax_polx = fig.add_subplot(gs[0, 0])
        ax_poly = fig.add_subplot(gs[0, 1])
        if "all" in opts.date.lower():
            delta = (dt_to_timestamp(datetime.datetime.utcnow().date() + datetime.timedelta(1)) -
                     dt_to_timestamp(datetime.datetime(2020, 03, 01)))
            delta_h = delta / 3600
            x = np.array(range(delta)) + t_start
        else:
            delta_h = (t_stop - t_start) / 3600
            x = np.array(range(t_stop - t_start)) + t_start

        spettro_x = []
        spettro_y = []
        station_rms_x = {}
        station_rms_y = {}
        station_tiles_tstamp = {}

        for tile in range(16):
            station_tiles_tstamp['TILE-%02d'%(tile+1)] = []
            for sb_in in range(16):
                station_rms_x[ants[sb_in + 16 * tile]] = []
                station_rms_y[ants[sb_in + 16 * tile]] = []
            lista = sorted(glob.glob(opts.directory + station_name.lower() + "/channel_integ_%d*_0.hdf5" % (tile)))
            t_cnt = 0
            orari = []
            t_stamps = []
            tile_rms_x = []
            tile_rms_y = []
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
                                    station_tiles_tstamp['TILE-%02d'%(tile+1)] += [t[0]]
                                    for sb_in in antenne:
                                        spettro_x = data[:, sb_in, 0, i]
                                        spettro_y = data[:, sb_in, 1, i]
                                        t_stamps += [t[0]]
                                        orari += [datetime.datetime.utcfromtimestamp(t[0])]
                                        with np.errstate(divide='ignore'):
                                            pow = 10 * np.log10(np.sum(spettro_x[:]))
                                            if pow == -np.inf:
                                                station_rms_x[ants[sb_in + 16 * tile]] += [0]
                                            else:
                                                station_rms_x[ants[sb_in + 16 * tile]] += [pow]
                                            pow = 10 * np.log10(np.sum(spettro_y[:]))
                                            if pow == -np.inf:
                                                station_rms_y[ants[sb_in + 16 * tile]] += [0]
                                            else:
                                                station_rms_y[ants[sb_in + 16 * tile]] += [pow]
                                    #msg = "\rProcessing Tile " + str(tile + 1) + " " + ts_to_datestring(t[0])
                                    #sys.stdout.write(ERASE_LINE + msg)
                                    #sys.stdout.flush()

                msg = "\r[%d/%d] File: %s" % (cnt_l + 1, len(lista), l.split("/")[-1]) + "   " + \
                      ts_to_datestring(timestamps[0][0]) + "   " + ts_to_datestring(timestamps[-1][0])
                sys.stdout.write(ERASE_LINE + msg)
                sys.stdout.flush()

    print

    if opts.scp:
        sys.stdout.write("\nData transfer: scp -P %d %s %s:%s" % (opts.scp_port,
                                                                  scp_fname,
                                                                  opts.scp_server,
                                                                  opts.scp_dir))
        sys.stdout.flush()
        os.system("scp -P %d %s %s:%s" % (opts.scp_port,
                                          scp_fname,
                                          opts.scp_server,
                                          opts.scp_dir))
        print











