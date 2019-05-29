from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
from aavs_calibration.common import get_antenna_positions
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

# Global flag to stop the scrpts
stop_plotting = False
img_dir = "/storage/monitoring/phase1/"


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

    # Create station instance
    aavs_station = station.Station(station.configuration)
    aavs_station.connect()
    _connect_station(aavs_station)

    # Grab antenna base numbers and positions
    base, x, y = get_antenna_positions(station_name)



    # Instantiate a file manager
    file_manager = ChannelFormatFileManager(root_path=opts.directory, daq_mode=FileDAQModes.Integrated)

    plt.ioff()
    gs = gridspec.GridSpec(5, 3)
    fig = plt.figure(figsize=(16, 9), facecolor='w')

    ax_title = fig.add_subplot(gs[0, 0])
    ax_geo_map = fig.add_subplot(gs[1:3, 0])

    potenza_rf = []
    ax_total_power = fig.add_subplot(gs[3:5, 0])

    potenza_airplane = []
    ax_airplane = []
    ax_airplane += [fig.add_subplot(gs[0, 1])]
    ax_airplane += [fig.add_subplot(gs[0, 2])]

    potenza_orbcomm = []
    ax_orbcomm = []
    ax_orbcomm += [fig.add_subplot(gs[1, 1])]
    ax_orbcomm += [fig.add_subplot(gs[1, 2])]

    ax_rms = []
    ax_rms += [fig.add_subplot(gs[2, 1])]
    ax_rms += [fig.add_subplot(gs[2, 2])]
    ind = np.arange(16)

    ax_spectra = []
    ax_spectra += [fig.add_subplot(gs[3:5, 1])]
    ax_spectra += [fig.add_subplot(gs[3:5, 2])]
    print len(ax_spectra)

    asse_x = np.linspace(0, 400, 512)

    all_data = np.zeros((512, nof_tiles * 16, 2, 1))

    while not stop_plotting:

        # Wait for a while
        sleep(cadence)

        # Connect to the station
        _connect_station(aavs_station)

        # Read latest spectra
        tile_rms = []
        tile_acq_timestamp = []


        for i in range(nof_tiles):
            # Grab tile data
            data, timestamps = file_manager.read_data(tile_id=i, n_samples=1, sample_offset=-1)

            all_data[:, i * 16 : (i + 1) * 16, :, :] = data

            tile_acq_timestamp += [timestamps]

            # Grab antenna RMS
            tile_rms.extend(aavs_station.tiles[i].get_adc_rms())

        # ...... Create plot
        logging.info("Time to plot")


        for tile in range(nof_tiles):
            porbcomm = []
            pairplane = []

            for pol, (pols, col) in enumerate([("POL-X", "b"), ("POL-Y", "g")]):
                ax_spectra[pol].cla()
                for rx in range(16):

                    #print len(np.array(all_data[:,  tile * 16 : (tile + 1) * 16, rx, 0]).astype("float"))
                    ax_spectra[pol].plot(asse_x, 10*np.log10(np.array(all_data[:,  tile * 16 : (tile + 1) * 16, pol, 0])))
                    ax_spectra[pol].grid(True)

                ax_spectra[pol].set_xlim(0, 400)
                ax_spectra[pol].set_xticks([50, 100, 150, 200, 250, 300, 350, 400])
                ax_spectra[pol].set_xticklabels([50, 100, 150, 200, 250, 300, 350, 400], fontsize=8)#, rotation=45)
                ax_spectra[pol].set_xlabel("MHz", fontsize=10)

                ax_spectra[pol].set_ylim(0, 50)
                #ax_spectra[pol].set_yticks([0, -20, -40, -60, -80])
                #ax_spectra[pol].set_yticklabels([0, -20, -40, -60, -80], fontsize=8)
                ax_spectra[pol].set_ylabel("dB", fontsize=10)
                ax_spectra[pol].set_title(pols + " Spectra", fontsize=12)

            fig.tight_layout()#rect=[0, 0.03, 1, 0.95])
            fig.canvas.draw()
            fig.savefig(img_dir + station_name + "/" + str(tile+1) + ".svg")


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
