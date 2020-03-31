from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
from aavs_calibration.common import get_antenna_positions, get_antenna_tile_names
from pydaq import daq_receiver as receiver
import sys
# import matplotlib
# if 'matplotlib.backends' not in sys.modules:
#     matplotlib.use('agg') # not to use X11
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from threading import Thread
from pyaavs import station
from time import sleep
import logging
import signal
import os
import datetime, time


# Global flag to stop the scrpts
stop_plotting = False
img_dir = "/storage/monitoring/phase1/"
FIG_W = 14
TILE_H = 3.2
LOCK_FILE = "/storage/monitoring/monitor.lock"

def _signal_handler(signum, frame):
    global stop_plotting
    # Stop observer and data acqusition
    logging.info("Received interrupt, stopping bandpass generation")
    stop_plotting = True

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


def plotting_thread(directory, cadence):
    """ PLotting thread
    :param cadence: Sleeps between plot generations """
    global stop_plotting

    station_name = station.configuration['station']['name']

    logging.info("Starting plotting threads for station " + station_name)

    remap = [0, 1, 2, 3, 8, 9, 10, 11, 15, 14, 13, 12, 7, 6, 5, 4]
    if not os.path.isdir(img_dir+station_name):
        os.mkdir(img_dir+station_name)

    # Store number of tiles
    nof_tiles = len(station.configuration['tiles'])

    # Create station instance
    aavs_station = station.Station(station.configuration)
    aavs_station.connect()
    _connect_station(aavs_station)

    sleep(16)

    station_dir = ""
    station_file = ""
    if station_name == "AAVS2":
        station_dir = "skala-4/"
        station_file = "STATION_SKALA-4.png"
    elif station_name == "EDA2":
        station_dir = "eda-2/"
        station_file = "STATION_EDA-2.png"

    # Grab antenna base numbers and positions
    base, x, y = get_antenna_positions(station_name)
    # AAVS2 Tile-14 Patch
    if (datetime.datetime.utcnow() > datetime.datetime(2020, 3, 1)) and (station_name == "AAVS2") and \
            (datetime.datetime.utcnow() < datetime.datetime(2020, 3, 16, 18, 00)):
        print "Patching antenna name and positions"
        base = base[:16*13] + base[16*14:]
        x = x[:16*13] + x[16*14:]
        y = y[:16*13] + y[16*14:]

    ants = []
    for j in range(16*nof_tiles):
        ants += ["ANT-%03d" % int(base[j])]

    tile_names = []
    tiles = get_antenna_tile_names(station_name)
    # AAVS2 Tile-14 Patch
    if (datetime.datetime.utcnow() > datetime.datetime(2020, 3, 1)) and (station_name == "AAVS2") and \
            (datetime.datetime.utcnow() < datetime.datetime(2020, 3, 16, 18, 00)):
        print "Patching tile names"
        tiles = tiles[:16*13] + tiles[16*14:]
        #print tiles
    for i in tiles:
        if not i.replace("TPM", "Tile") in tile_names:
            tile_names += [i.replace("TPM", "Tile")]

    # Instantiate a file manager
    file_manager = ChannelFormatFileManager(root_path=opts.directory, daq_mode=FileDAQModes.Integrated)

    plt.ioff()
    asse_x = np.linspace(0, 400, 512)

    # gridspec inside gridspec
    outer_grid = gridspec.GridSpec(nof_tiles, 1, hspace=0.8, left=0.02, right=0.98, bottom=0.04, top=0.98)
    fig = plt.figure(figsize=(FIG_W, TILE_H * nof_tiles), facecolor='w')
    t_axes = []
    axes = []

    tstamp_label = []
    x_lines = []
    y_lines = []
    ind = np.arange(16)
    x_bar = []
    y_bar = []

    for i in range(nof_tiles):
        # print tile_active[i]
        gs = gridspec.GridSpecFromSubplotSpec(2, 17, wspace=0.05, hspace=0.5, subplot_spec=outer_grid[i])
        t_axes += [
            [plt.subplot(gs[0:2, 0:3]), plt.subplot(gs[0:2, 3:5]), plt.subplot(gs[0, 6:8]), plt.subplot(gs[1, 6:8])]]

        t_axes[i][0].cla()
        t_axes[i][0].set_axis_off()
        t_axes[i][0].plot([0.001, 0.002], color='w')
        t_axes[i][0].set_xlim(-20, 20)
        t_axes[i][0].set_ylim(-20, 20)
        t_axes[i][0].annotate(tile_names[i], (-11, 5), fontsize=26, color='black')
        t_axes[i][0].annotate("Acquisition Time (UTC)", (-17.7, -6), fontsize=12, color='black')
        tl = t_axes[i][0].annotate("--- UTC", (-17.8, -12), fontsize=12, color='black')
        tstamp_label += [tl]

        t_axes[i][1].cla()
        t_axes[i][1].set_axis_off()
        t_axes[i][1].plot([0.001, 0.002], color='wheat')
        t_axes[i][1].set_xlim(-25, 25)
        t_axes[i][1].set_ylim(-25, 25)
        circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
        t_axes[i][1].add_artist(circle1)
        t_axes[i][1].annotate("E", (21, -1), fontsize=10, color='black')
        t_axes[i][1].annotate("W", (-25, -1), fontsize=10, color='black')
        t_axes[i][1].annotate("N", (-1, 21), fontsize=10, color='black')
        t_axes[i][1].annotate("S", (-1, -24), fontsize=10, color='black')

        t_axes[i][2].cla()
        t_axes[i][2].plot([0.001, 0.002], color='w')
        t_axes[i][2].tick_params(axis='both', which='both', labelsize=6)
        t_axes[i][2].set_xticks(xrange(1, 17))
        t_axes[i][2].set_xticklabels(np.array(range(1, 17)).astype("str").tolist(), fontsize=4)
        if not station_name == "EDA2":
            t_axes[i][2].set_ylim([0, 40])
            t_axes[i][2].set_yticks([15, 20])
            t_axes[i][2].set_yticklabels(["15", "20"], fontsize=7)
        else:
            t_axes[i][2].set_ylim([0, 20])
            t_axes[i][2].set_yticks([0, 5, 10, 15, 20])
            t_axes[i][2].set_yticklabels(["0", "5", "10", "15", "20"], fontsize=7)
        t_axes[i][2].set_xlim([0, 16])
        t_axes[i][2].set_ylabel("RMS", fontsize=10)
        t_axes[i][2].grid()
        t_axes[i][2].set_title("Power Pol X", fontsize=10)
        xb = t_axes[i][2].bar(ind + 0.5, ind, 0.8, color='b')
        x_bar += [xb]

        t_axes[i][3].cla()
        t_axes[i][3].plot([0.001, 0.002], color='w')
        t_axes[i][3].tick_params(axis='both', which='both', labelsize=6)
        t_axes[i][3].set_xticks(xrange(1, 17))
        t_axes[i][3].set_xticklabels(np.array(range(1, 17)).astype("str").tolist(), fontsize=4)
        t_axes[i][3].set_yticks([15, 20])
        t_axes[i][3].set_yticklabels(["15", "20"], fontsize=7)
        if not station_name == "EDA2":
            t_axes[i][3].set_ylim([0, 40])
            t_axes[i][3].set_yticks([15, 20])
            t_axes[i][3].set_yticklabels(["15", "20"], fontsize=7)
        else:
            t_axes[i][3].set_ylim([0, 5])
            t_axes[i][3].set_yticks([0, 5, 10, 15, 20])
            t_axes[i][3].set_yticklabels(["0", "5", "10", "15", "20"], fontsize=7)
        t_axes[i][3].set_xlim([0, 16])
        t_axes[i][3].set_ylabel("RMS", fontsize=10)
        t_axes[i][3].set_xlabel("Power Pol Y", fontsize=10)
        t_axes[i][3].grid()
        yb = t_axes[i][3].bar(ind + 0.5, ind, 0.8, color='g')
        y_bar += [yb]

        for r in range(2):
            for c in range(8):
                ant_index = (16*i) + (8*r) + c
                axes += [plt.subplot(gs[(r, c + 9)])]
                axes[ant_index].cla()
                axes[ant_index].set_xlim(0, 400)
                axes[ant_index].set_ylim(0, 50)
                if c:
                    axes[ant_index].get_yaxis().set_visible(False)
                else:
                    axes[ant_index].set_yticks([0, 10, 20, 30, 40, 50])
                    axes[ant_index].set_yticklabels([0, 10, 20, 30, 40, 50], fontsize=8)
                    axes[ant_index].set_ylabel("dB", fontsize=10)
                if r:
                    axes[ant_index].set_xticks([100, 200, 300, 400])
                    axes[ant_index].set_xticklabels([100, 200, 300, 400], fontsize=8, rotation=45)
                    axes[ant_index].set_xlabel("MHz", fontsize=10)
                else:
                    axes[ant_index].set_xticks([100, 200, 300, 400])
                    axes[ant_index].set_xticklabels(["", "", "", ""], fontsize=1)
                axes[ant_index].set_title(ants[(16*i) + remap[(8*r) + c]], fontsize=10)

                xl, = axes[ant_index].plot(asse_x, range(512), color='b')
                x_lines += [xl]
                yl, = axes[ant_index].plot(asse_x, range(512), color='g')
                y_lines += [yl]

                # Draw antenna positions
                t_axes[i][1].plot(float(x[ant_index]), float(y[ant_index]), marker='+', markersize=4,
                                  linestyle='None', color='k')

    all_data = np.zeros((512, nof_tiles * 16, 2, 1))
    tile_acq_timestamp = []

    current_day = "2019-05-01"

    while not stop_plotting:

        # if not os.path.exists(LOCK_FILE):
        # Wait for a while
        sleep(cadence)

        try:
            # Connect to the station
            _connect_station(aavs_station)

            # Read latest spectra
            tile_rms = []

            for i in range(nof_tiles):
                # Grab tile data
                data, timestamps = file_manager.read_data(tile_id=i, n_samples=1, sample_offset=-1)

                all_data[:, i * 16 : (i + 1) * 16, :, :] = data

                # Grab antenna RMS
                tile_rms.extend(aavs_station.tiles[i].get_adc_rms())

            #asse_x_secs = []
            timestamp_day = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(timestamps[0][0]), "%Y-%m-%d")
            if not current_day == timestamp_day:
                current_day = timestamp_day
                tile_acq_timestamp = [int(timestamps[0][0])]
                # asse_x_secs = [(datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]) -
                #                  datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]).replace(hour=0,
                #                                                                                     minute=0,
                #                                                                                     second=0,
                #                                                                                     microsecond=0)).seconds]
                if not os.path.isdir(img_dir + station_name + "/" + current_day):
                    os.mkdir(img_dir + station_name + "/" + current_day)
            else:
                tile_acq_timestamp += [int(timestamps[0][0])]
                # asse_x_secs += [(datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]) -
                #                  datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]).replace(hour=0,
                #                                                                                     minute=0,
                #                                                                                     second=0,
                #                                                                                     microsecond=0)).seconds]

            t_timestamp = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]), "%Y-%m-%d %H:%M:%S UTC")

            for i in range(nof_tiles):
                tstamp_label[i].set_text(t_timestamp)
                for r in range(2):
                    for c in range(8):
                        ant_index = (16*i) + (8*r) + c
                        remapped_ant = (16*i) + remap[(8*r) + c]
                        singolo = all_data[:, remapped_ant: remapped_ant + 1, 0, 0]
                        with np.errstate(divide='ignore'):
                            x_lines[ant_index].set_ydata(10*np.log10(singolo))
                        singolo = all_data[:, remapped_ant: remapped_ant + 1, 1, 0]
                        with np.errstate(divide='ignore'):
                            y_lines[ant_index].set_ydata(10*np.log10(singolo))
                        x_bar[i][(8*r) + c].set_height(tile_rms[remapped_ant * 2])
                        y_bar[i][(8*r) + c].set_height(tile_rms[remapped_ant * 2 + 1])

            fig.canvas.draw()

            fname = img_dir + station_dir + station_file
            fig.savefig(fname)
            logging.info("Generated plots for timestamp " + t_timestamp + " on " + fname)
        except:
            logging.warning("Something went wrong plotting timestamp " + t_timestamp + " ...skipping...")
            logging.warning("Tile RMS len: "+str(len(tile_rms)))
            logging.warning("Wait for a minute to automatic restart...")
            sleep(60)
            pass


def daq_thread(interface, port, nof_tiles, directory):
    """ Start the DAQ instance for this station
    :param interface: Network interface
    :param port: Network port
    :param nof_tiles: Number of tiles in station
    :param directory: Directory where data will temporarily be stored"""
    global stop_plotting

    logging.info("Initialising DAQ")

    # DAQ configuration
    daq_config = {"receiver_interface": interface,
                  "receiver_ports": str(port),
                  "nof_tiles": nof_tiles,
                  'directory': directory}

    # Turn off logging in DAQ
    receiver.LOG = False

    receiver.populate_configuration(daq_config)
    receiver.initialise_daq()
    receiver.start_integrated_channel_data_consumer()

    # Wait until stopped
    while not stop_plotting:
        sleep(1)

    # Stop daq
    receiver.stop_daq()


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
    parser.add_option("--interface", action="store", dest="interface",
                      default="eth3", help="Network interface (default: eth3)")

    (opts, args) = parser.parse_args(argv[1:])

    # Set logging
    logging.Formatter.converter = time.gmtime
    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    line_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    # ch = logging.FileHandler(filename="/opt/aavs/log/integrated_data", mode='w')
    ch = logging.StreamHandler(stdout)
    ch.setFormatter(line_format)
    log.addHandler(ch)

    # Check if a configuration file was defined
    if opts.config is None:
        log.error("A station configuration file is required, exiting")
        exit()

    # Load configuration file
    station.load_configuration_file(opts.config)

    # Start DAQ Thread
    daq = Thread(target=daq_thread, args=(opts.interface, 
                                          station.configuration['network']['lmc']['integrated_data_port'],
                                          len(station.configuration['tiles']), 
                                          opts.directory))
    daq.start()

    # Start plotting thread
    plotter = Thread(target=plotting_thread, args=(opts.directory, 0))
    plotter.start()

    # Wait for exit or termination
    signal.signal(signal.SIGINT, _signal_handler)

    # Wait for stop
    daq.join()
    plotter.join()
