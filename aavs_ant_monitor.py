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
from aavs_utils import tstamp_to_fname, dt_to_timestamp, ts_to_datestring, fname_to_tstamp

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

    parser = OptionParser(usage="usage: %aavs_ant_monitor [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs2.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS1)")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data/",
                      help="Directory where plots will be generated (default: /storage/monitoring/integrated_data)")
    parser.add_option("--tile", action="store", dest="tile", type=int,
                      default="1", help="Tile Number")
    parser.add_option("--antenna", action="store", dest="antenna", type=int,
                      default="1", help="TPM/SmartBox Input number")

    (opts, args) = parser.parse_args(argv[1:])

    assex = np.linspace(0, 400, 512)

    print

    #date_path = tstamp_to_fname(t_start)[:-6]

    plt.ion()
    nplot = 1
    ant = opts.antenna - 1
    tile = opts.tile - 1

    #remap = [0,1,2,3,15,14,13,12,4,5,6,7,11,10,9,8]
    remap = [0, 1, 2, 3, 8, 9, 10, 11, 15, 14, 13, 12, 7, 6, 5, 4]

    #ind = np.arange(nplot)

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']

    # Store number of tiles
    nof_tiles = len(station.configuration['tiles'])

    print "\nStation Name: ", station_name
    print "\nNumber of Tiles: ", nof_tiles
    print "Checking directory: ", opts.directory+station_name.lower() + "\n"
    print "Looking for tiles/antenna: ", opts.tile, "/", opts.antenna, "\n"

    file_manager = ChannelFormatFileManager(root_path=opts.directory+station_name.lower(),
                                            daq_mode=FileDAQModes.Integrated)

    base, x, y = get_antenna_positions(station_name)
    ants = []
    for j in base:
        ants += ["ANT-%03d" % int(j)]

    fig = plt.figure(figsize=(11, 7), facecolor='w')
    ax = fig.add_subplot(1,1,1)
    all_data = np.zeros((512, nof_tiles * 16, 2, 1))

    xl, = ax.plot(range(512), range(512), color='b')
    yl, = ax.plot(range(512), range(512), color='g')
    ax.tick_params(axis='both', which='both', labelsize=12)
    ax.set_ylim(0, 50)
    ax.set_xlim(0, 512)
    ax.set_xticks([0, 128, 256, 384, 512])
    ax.set_xticklabels([0, 100, 200, 300, 400])
    ax.set_xlabel("MHz", fontsize=12)
    ax.set_ylabel("dB", fontsize=12)
    title = ax.set_title("Warming up...")

    while True:

        tile_rms = []

        for i in range(nof_tiles):
            # Grab tile data
            data, timestamps = file_manager.read_data(tile_id=i, n_samples=1, sample_offset=-1)

            all_data[:, i * 16 : (i + 1) * 16, :, :] = data

        # Generate picture
        orario = ts_to_datestring(timestamps[0][0], formato="%Y-%m-%d    %H:%M:%S  UTC")
        with np.errstate(divide='ignore'):
            spettro = 10 * np.log10(all_data[:, remap[ant] + tile * 16, 0, 0])
        xl.set_ydata(spettro)
        with np.errstate(divide='ignore'):
            spettro = 10 * np.log10(all_data[:, remap[ant] + tile * 16, 1, 0])
        yl.set_ydata(spettro)
        title.set_text(ants[remap[ant] + tile * 16] + "     " + orario)
        fig.canvas.draw()
        fig.canvas.flush_events()








