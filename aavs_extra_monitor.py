from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
from aavs_calibration.common import get_antenna_positions, get_antenna_tile_names
from pydaq import daq_receiver as receiver
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from threading import Thread
from pyaavs import station
from time import sleep
import logging
import signal
import os
import datetime


# Global flag to stop the scrpts
stop_plotting = False
img_dir = "/storage/monitoring/phase1/"
FIG_W = 14
TILE_H = 3.2


def calcSpectra(vett):
    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett * window)
    N = len(spettro)
    acf = 2  # amplitude correction factor
    spettro[:] = abs((acf * spettro) / N)
    # print len(vett), len(spettro), len(np.real(spettro))
    return (np.real(spettro))


def calcolaspettro(dati, nsamples=131072):
    n = nsamples  # split and average number, from 128k to 16 of 8k # aavs1 federico
    sp = [dati[x:x + n] for x in xrange(0, len(dati), n)]
    mediato = np.zeros(len(calcSpectra(sp[0])))
    for k in sp:
        singolo = calcSpectra(k)
        mediato[:] += singolo
    # singoli[:] /= 16 # originale
    mediato[:] /= (2 ** 17 / nsamples)  # federico
    with np.errstate(divide='ignore', invalid='ignore'):
        mediato[:] = 20 * np.log10(mediato / 127.0)
    return mediato


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


def dB2Linear(valueIndB):
    """
    Convert input from dB to linear scale.
    Parameters
    ----------
    valueIndB : float | np.ndarray
        Value in dB
    Returns
    -------
    valueInLinear : float | np.ndarray
        Value in Linear scale.
    Examples
    --------
    #>>> dB2Linear(30)
    1000.0
    """
    return pow(10, valueIndB / 10.0)


def linear2dB(valueInLinear):
    """
    Convert input from linear to dB scale.
    Parameters
    ----------
    valueInLinear : float | np.ndarray
        Value in Linear scale.
    Returns
    -------
    valueIndB : float | np.ndarray
        Value in dB scale.
    Examples
    --------
    #>>> linear2dB(1000)
    30.0
    """
    return 10.0 * np.log10(valueInLinear)


def dBm2Linear(valueIndBm):
    """
    Convert input from dBm to linear scale.
    Parameters
    ----------
    valueIndBm : float | np.ndarray
        Value in dBm.
    Returns
    -------
    valueInLinear : float | np.ndarray
        Value in linear scale.
    Examples
    --------
    #>>> dBm2Linear(60)
    1000.0
    """
    return dB2Linear(valueIndBm) / 1000.


def linear2dBm(valueInLinear):
    """
    Convert input from linear to dBm scale.
    Parameters
    ----------
    valueInLinear : float | np.ndarray
        Value in Linear scale
    Returns
    -------
    valueIndBm : float | np.ndarray
        Value in dBm.
    Examples
    --------
    #>>> linear2dBm(1000)
    60.0
    """
    return linear2dB(valueInLinear * 1000.)


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

    if not os.path.isdir(img_dir+station_name):
        os.mkdir(img_dir+station_name)

    # Store number of tiles
    nof_tiles = len(station.configuration['tiles'])
    #print nof_tiles

    # Create station instance
    aavs_station = station.Station(station.configuration)
    aavs_station.connect()
    _connect_station(aavs_station)

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
    ants = []
    for j in range(16*nof_tiles):
        ants += ["ANT-%03d" % int(base[j])]

    tile_names = []
    tiles = get_antenna_tile_names(station_name)
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
    for i in range(nof_tiles):
        # print tile_active[i]
        gs = gridspec.GridSpecFromSubplotSpec(2, 17, wspace=0.05, hspace=0.5, subplot_spec=outer_grid[i])
        t_axes += [
            [plt.subplot(gs[0:2, 0:3]), plt.subplot(gs[0:2, 3:5]), plt.subplot(gs[0, 6:8]), plt.subplot(gs[1, 6:8])]]

        for r in range(2):
            for c in range(8):
                axes += [plt.subplot(gs[(r, c + 9)])]

    all_data = np.zeros((512, nof_tiles * 16, 2, 1))
    tile_acq_timestamp = []

    current_day = "2019-05-01"

    while not stop_plotting:

        # Wait for a while
        sleep(cadence)

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

        # ...... Create plot
        #logging.info("Time to plot")

        asse_x_secs = []
        timestamp_day = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(timestamps[0][0]), "%Y-%m-%d")
        if not current_day == timestamp_day:
            current_day = timestamp_day
            tile_acq_timestamp = [int(timestamps[0][0])]
            asse_x_secs = [(datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]) -
                             datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]).replace(hour=0,
                                                                                                minute=0,
                                                                                                second=0,
                                                                                                microsecond=0)).seconds]
            if not os.path.isdir(img_dir + station_name + "/" + current_day):
                os.mkdir(img_dir + station_name + "/" + current_day)
        else:
            tile_acq_timestamp += [int(timestamps[0][0])]
            asse_x_secs += [(datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]) -
                             datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]).replace(hour=0,
                                                                                                minute=0,
                                                                                                second=0,
                                                                                                microsecond=0)).seconds]

        #f_timestamp = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]), "%Y%m%d_%H%M%S")
        t_timestamp = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]), "%Y-%m-%d %H:%M:%S UTC")

        try:

            ind = np.arange(16)
            for n in range(nof_tiles):

                # print n, len(STATION['TILES'])
                t_axes[n][0].cla()
                t_axes[n][0].set_axis_off()
                t_axes[n][0].plot([0.001, 0.002], color='w')
                t_axes[n][0].set_xlim(-20, 20)
                t_axes[n][0].set_ylim(-20, 20)
                t_axes[n][0].annotate(tile_names[n], (-11, 5), fontsize=26, color='black')

                t_axes[n][1].cla()
                t_axes[n][1].set_axis_off()
                t_axes[n][1].plot([0.001, 0.002], color='wheat')
                t_axes[n][1].set_xlim(-25, 25)
                t_axes[n][1].set_ylim(-25, 25)
                circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
                t_axes[n][1].add_artist(circle1)
                t_axes[n][1].annotate("E", (21, -1), fontsize=10, color='black')
                t_axes[n][1].annotate("W", (-25, -1), fontsize=10, color='black')
                t_axes[n][1].annotate("N", (-1, 21), fontsize=10, color='black')
                t_axes[n][1].annotate("S", (-1, -24), fontsize=10, color='black')

                t_axes[n][2].cla()
                t_axes[n][2].plot([0.001, 0.002], color='w')
                t_axes[n][2].set_xlim(-20, 20)
                t_axes[n][2].set_ylim(-20, 20)
                t_axes[n][2].set_title("Power Pol X", fontsize=10)

                t_axes[n][3].cla()
                t_axes[n][3].plot([0.001, 0.002], color='w')
                t_axes[n][3].set_xlim(-20, 20)
                t_axes[n][3].set_ylim(-20, 20)
                t_axes[n][3].set_title("Power Pol Y", fontsize=10)

                for en in range(16):
                    axes[en + (n * 16)].cla()
                    for pol, (poldir, col) in enumerate([("/POL-X/", "b"), ("/POL-Y/", "g")]):

                        singolo = all_data[:, (n * 16) + en: (n * 16) + en + 1, pol, 0]

                        axes[en + (n * 16)].plot(asse_x[2:-2], 10*np.log10(singolo)[2:-2], color=col)
                    axes[en + (n * 16)].set_xlim(0, 400)
                    axes[en + (n * 16)].set_ylim(0, 50)
                    if not ((en == 0) or (en == 8)):
                        axes[en + (n * 16)].get_yaxis().set_visible(False)
                    else:
                        axes[en + (n * 16)].set_yticks([0, 10, 20, 30, 40, 50])
                        axes[en + (n * 16)].set_yticklabels([0, 10, 20, 30, 40, 50], fontsize=8)
                        axes[en + (n * 16)].set_ylabel("dB", fontsize=10)
                    if (en > 7):
                        axes[en + (n * 16)].set_xticks([100, 200, 300, 400])
                        axes[en + (n * 16)].set_xticklabels([100, 200, 300, 400], fontsize=8, rotation=45)
                        axes[en + (n * 16)].set_xlabel("MHz", fontsize=10)
                    else:
                        axes[en + (n * 16)].set_xticks([100, 200, 300, 400])
                        axes[en + (n * 16)].set_xticklabels(["", "", "", ""], fontsize=1)
                    axes[en + (n * 16)].set_title(ants[en + (n * 16)], fontsize=10)

                    # Draw antenna positions
                    t_axes[n][1].plot(float(x[en + (n * 16)]), float(y[en + (n * 16)]), marker='+', markersize=4,
                                                                                        linestyle='None', color='k')

                # Plot Power X
                t_axes[n][2].cla()
                t_axes[n][2].tick_params(axis='both', which='both', labelsize=6)
                t_axes[n][2].set_xticks(xrange(1, 17))
                t_axes[n][2].set_xticklabels(np.array(range(1, 17)).astype("str").tolist(), fontsize=4)
                t_axes[n][2].set_yticks([15, 20])
                t_axes[n][2].set_yticklabels(["15", "20"], fontsize=7)
                t_axes[n][2].set_ylim([0, 40])
                t_axes[n][2].set_xlim([0, 16])
                t_axes[n][2].set_ylabel("RMS", fontsize=10)
                t_axes[n][2].grid()
                t_axes[n][2].bar(ind + 0.5, tile_rms[n * 32: (n + 1) * 32: 2], 0.8, color='b')
                t_axes[n][2].set_title("Power Pol X", fontsize=10)

                # Plot Power Y
                t_axes[n][3].cla()
                t_axes[n][3].tick_params(axis='both', which='both', labelsize=6)
                t_axes[n][3].set_xticks(xrange(1, 17))
                t_axes[n][3].set_xticklabels(np.array(range(1, 17)).astype("str").tolist(), fontsize=4)
                t_axes[n][3].set_yticks([15, 20])
                t_axes[n][3].set_yticklabels(["15", "20"], fontsize=7)
                t_axes[n][3].set_ylim([0, 40])
                t_axes[n][3].set_xlim([0, 16])
                t_axes[n][3].set_ylabel("RMS", fontsize=10)
                t_axes[n][3].set_xlabel("Power Pol Y", fontsize=10)
                t_axes[n][3].grid()
                t_axes[n][3].bar(ind + 0.5, tile_rms[n * 32 + 1: (n+1) * 32: 2], 0.8, color='g')

                t_axes[n][0].annotate("Acquisition Time (UTC)", (-17.7, -6), fontsize=12, color='black')
                t_axes[n][0].annotate(t_timestamp, (-17.8, -12), fontsize=12, color='black')

            fig.tight_layout()
            fig.canvas.draw()

            fname = img_dir + station_dir + station_file
            fig.savefig(fname)
            logging.info("Generated plots for timestamp " + t_timestamp + " on " + fname)
        except:
            logging.warning("Something went wrong plotting timestamp " + t_timestamp + " ...skipping...")
            logging.warning("Tile RMS len: "+str(len(tile_rms)))
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
    plotter = Thread(target=plotting_thread, args=(opts.directory, 30))
    plotter.start()

    # Wait for exit or termination
    signal.signal(signal.SIGINT, _signal_handler)

    # Wait for stop
    daq.join()
    plotter.join()
