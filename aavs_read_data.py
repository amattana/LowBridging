from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import sys
import matplotlib
if not 'matplotlib.backends' in sys.modules:
    matplotlib.use('agg') # not to use X11from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import matplotlib.pyplot as plt
import numpy as np
from pyaavs import station
from time import sleep
import datetime
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from aavs_calibration.common import get_antenna_positions, get_antenna_tile_names

# Global flag to stop the scrpts
FIG_W = 14
TILE_H = 3.2


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

    parser = OptionParser(usage="usage: %monitor_bandpasses [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs1_full_station.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS1)")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data",
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

    plt.ioff()
    nplot = 16
    ind = np.arange(nplot)
    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']
    file_manager = ChannelFormatFileManager(root_path=opts.directory, daq_mode=FileDAQModes.Integrated)
    dic = file_manager.get_metadata(tile_id=int(opts.tile)-1)
    data = file_manager.read_data(tile_id=int(opts.tile)-1, n_samples=dic['n_blocks'])

    assex = np.linspace(0, 400, len(data[0][:, 0, 0, -1]))

    outer_grid = GridSpec(4, 4, hspace=0.4, wspace=0.4, left=0.04, right=0.98, bottom=0.04, top=0.96)
    gs = GridSpecFromSubplotSpec(int(np.ceil(np.sqrt(16))), int(np.ceil(np.sqrt(16))), wspace=0.4, hspace=0.6,
                                 subplot_spec=outer_grid[1:, :])

    base, x, y = get_antenna_positions(station_name)
    ants = []
    for j in range(16*nof_tiles):
        ants += ["ANT-%03d" % int(base[j])]

    print
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
    for en in range(16):
        ax_top_map.plot(float(x[en + (int(opts.tile - 1) * 16)]), float(y[en + (int(opts.tile - 1) * 16)]),
                        marker='+', markersize=4, linestyle='None', color='k')

    for bl in range(dic['n_blocks']):
        try:
            if bl > opts.skip:
                for ant in range(nplot):
                    ax[ant].cla()
                    with np.errstate(divide='ignore'):
                        spettro = 10 * np.log10(data[0][:, ant, 0, bl])
                    ax[ant].plot(assex[2:-1], spettro[2:-1], scaley=True, color='b')
                    with np.errstate(divide='ignore'):
                        spettro = 10 * np.log10(data[0][:, ant, 1, bl])
                    ax[ant].plot(assex[2:-1], spettro[2:-1], scaley=True, color='g')
                    ax[ant].set_ylim(0, 50)
                    ax[ant].set_xlim(0, 400)
                    ax[ant].set_title("IN " + str(ant + 1), fontsize=8)

                ax_top_tile.cla()
                ax_top_tile.set_axis_off()
                ax_top_tile.plot([0.001, 0.002], color='w')
                ax_top_tile.set_xlim(-20, 20)
                ax_top_tile.set_ylim(-20, 20)
                ax_top_tile.annotate("TILE %02d" % (opts.tile), (-12, 6), fontsize=24, color='black')
                orario = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(data[1][bl]), "%Y-%m-%d  %H:%M:%S")
                ax_top_tile.annotate(orario, (-18, -12), fontsize=12, color='black')
                orario = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(data[1][bl]), "%Y-%m-%d_%H%M%S")

                plt.savefig("/storage/monitoring/pictures/TILE-%02d"%(opts.tile) + "/TILE-%02d_"%(opts.tile)+orario+".png")
                sys.stdout.write("\r[%d/%d] Generated picture for TILE-%02d timestamp "%(bl+1, int(dic['n_blocks']), opts.tile) + orario)
                sys.stdout.flush()
        except:
            print "Tile-%02d "%(opts.tile), orario, "exception raised...\n"

    print
