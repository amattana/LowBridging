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

    assex = np.linspace(0, 400, 512)

    print

    #date_path = tstamp_to_fname(t_start)[:-6]

    plt.ioff()
    nplot = 1
    ant = 0
    tile = 0

    #ind = np.arange(nplot)

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']

    print "\nStation Name: ", station_name
    print "Checking directory: ", opts.directory+station_name.lower() + "\n"
    print "Looking for tiles/antenna: ", tile, ant, "\n"

    file_manager = ChannelFormatFileManager(root_path=opts.directory+station_name.lower(),
                                            daq_mode=FileDAQModes.Integrated)

    # Store number of tiles
    nof_tiles = len(station.configuration['tiles'])

    base, x, y = get_antenna_positions(station_name)
    ants = []
    for j in base:
        ants += ["ANT-%03d" % int(j)]

    fig = plt.figure(figsize=(11, 7), facecolor='w')
    ax = fig.add_subplot(1,1,1)
    all_data = np.zeros((512, nof_tiles * 16, 2, 1))

    xl, = ax.plot(range(512), range(512), color='b')
    yl, = ax.plot(range(512), range(512), color='g')
    title = ax.set_title("Warming up...")

    while True:

        tile_rms = []

        for i in range(nof_tiles):
            # Grab tile data
            data, timestamps = file_manager.read_data(tile_id=i, n_samples=1, sample_offset=-1)

            all_data[:, i * 16 : (i + 1) * 16, :, :] = data

        # Generate picture
        orario = ts_to_datestring(t[0], formato="%Y-%m-%d_%H%M%S")
        with np.errstate(divide='ignore'):
            spettro = 10 * np.log10(all_data[:, ant, 0, tile])
        xl.set_ydata(spettro)
        with np.errstate(divide='ignore'):
            spettro = 10 * np.log10(all_data[:, ant, 1, tile])
        yl.set_ydata(spettro)
        title.set_text(orario)

        plt.draw()
        plt.show()






