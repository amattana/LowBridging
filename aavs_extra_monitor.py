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
import datetime

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
    prf = []
    asse_x_secs = []
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

    asse_x = np.linspace(0, 400, 512)

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
        prf = []


        for i in range(nof_tiles):
            # Grab tile data
            data, timestamps = file_manager.read_data(tile_id=i, n_samples=1, sample_offset=-1)

            all_data[:, i * 16 : (i + 1) * 16, :, :] = data

            # Grab antenna RMS
            tile_rms.extend(aavs_station.tiles[i].get_adc_rms())

        # ...... Create plot
        logging.info("Time to plot")

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

        f_timestamp = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]), "%Y%m%d_%H%M%S")
        t_timestamp = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tile_acq_timestamp[-1]), "%Y-%m-%d %H:%M:%S UTC")

        for tile in range(nof_tiles):
            porbcomm = []
            pairplane = []

            for pol, (pols, col) in enumerate([("POL-X", "b"), ("POL-Y", "g")]):
                ax_spectra[pol].cla()

                with np.errstate(divide='ignore', invalid='ignore'):
                    spectrum = 10*np.log10(np.array(all_data[:,  tile * 16 : (tile + 1) * 16, pol, 0]))

                ax_spectra[pol].plot(asse_x, spectrum)
                ax_spectra[pol].grid(True)

                ax_spectra[pol].set_xlim(0, 400)
                ax_spectra[pol].set_xticks([50, 100, 150, 200, 250, 300, 350, 400])
                ax_spectra[pol].set_xticklabels([50, 100, 150, 200, 250, 300, 350, 400], fontsize=8)#, rotation=45)
                ax_spectra[pol].set_xlabel("MHz", fontsize=10)

                ax_spectra[pol].set_ylim(0, 50)
                ax_spectra[pol].set_yticks(np.arange(6)*10)
                ax_spectra[pol].set_yticklabels(np.arange(6)*10, fontsize=8)
                ax_spectra[pol].set_ylabel("dB", fontsize=10)
                ax_spectra[pol].set_title(pols + " Spectra", fontsize=12)

                ax_rms[pol].cla()
                ax_rms[pol].tick_params(axis='both', which='both', labelsize=6)
                ax_rms[pol].set_xticks(xrange(1,17))
                ax_rms[pol].set_xticklabels(np.array(range(1,17)).astype("str").tolist(), fontsize=4)
                ax_rms[pol].set_yticks([15, 20])
                ax_rms[pol].set_yticklabels(["15", "20"], fontsize=7)
                ax_rms[pol].set_ylim([0, 40])
                ax_rms[pol].set_xlim([0, 17])
                ax_rms[pol].set_ylabel("RMS", fontsize=10)
                ax_rms[pol].grid()
                ax_rms[pol].bar(ind+0.65, tile_rms[tile*16:(tile+1)*16], 0.8, color=col)
                ax_rms[pol].set_title("ADC RMS "+pols, fontsize=10)

                for k in range(16):
                    prf += [linear2dB(np.sum(dB2Linear(spectrum[:, k]))/1000000.)]

            potenza_rf += prf
            ax_total_power.cla()
            for j in range(32):
                serie = potenza_rf[j::32]
                print "Plotting ",j,asse_x_secs, serie
                if j < 16:
                    ax_total_power.plot(asse_x_secs, serie, color='b')
                else:
                    ax_total_power.plot(asse_x_secs, serie, color='g')
            ax_total_power.set_xlim(0, 86400)
            ax_total_power.set_xlabel("Hours", fontsize=10)
            ax_total_power.set_ylim(-15, 15)
            ax_total_power.set_ylabel("dBm", fontsize=10)
            ax_total_power.set_xticks(np.arange(0,  3 * 9 * 60 * 60))
            ax_total_power.set_xticklabels(np.array(range(0, 3 * 9, 3)).astype("str").tolist())
            ax_total_power.grid()

            ax_title.cla()
            ax_title.set_axis_off()
            ax_title.plot([0.001, 0.002], color='w')
            ax_title.set_xlim(-20, 20)
            ax_title.set_ylim(-20, 20)
            ax_title.annotate(station_name, (-15, 10), fontsize=32, color='blue')
            ax_title.annotate("TILE-%02d"%(tile+1), (-5, -8), fontsize=28, color='green')
            ax_title.annotate(t_timestamp, (-16, -20), fontsize=16, color='black')

            ax_geo_map.cla()
            ax_geo_map.set_axis_off()
            ax_geo_map.plot([0.001, 0.002], color='w')
            ax_geo_map.set_xlim(-30, 40)
            ax_geo_map.set_ylim(-25.5, 25.5)
            circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
            ax_geo_map.add_artist(circle1)
            for c in range(16):
                ax_geo_map.plot(x[c+(tile*16)], y[c+(tile*16)], marker='+', markersize=7,
                    linestyle='None', color='k')
            ax_geo_map.annotate("E", (23, -1), fontsize=12, color='black')
            ax_geo_map.annotate("W", (-25.1, -1), fontsize=12, color='black')
            ax_geo_map.annotate("N", (-1, 21), fontsize=12, color='black')
            ax_geo_map.annotate("S", (-1, -24.6), fontsize=12, color='black')

            fig.tight_layout()#rect=[0, 0.03, 1, 0.95])
            fig.canvas.draw()
            fname = img_dir + station_name + "/" + current_day + "/TILE-%02d_"%(tile+1) + f_timestamp + ".svg"
            print "Saving ", fname
            fig.savefig(fname)
        logging.info("Generated plots for timestamp "+t_timestamp)


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
