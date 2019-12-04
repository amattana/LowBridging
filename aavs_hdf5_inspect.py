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

def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


def plotting_thread(directory, cadence):
    """ PLotting thread
    :param cadence: Sleeps between plot generations """
    global stop_plotting

    station_name = station.configuration['station']['name']

    tile_name = []
    for i in range(16):
        tile_name += ["TILE-%02d"%(i+1)]
    if not station_name == "AAVS1":
        tile_name = ["TILE-07", "TILE-11", "TILE-16"]

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
    tile_names = get_antenna_tile_names(station_name)

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

        for i in range(nof_tiles):
            # Grab tile data
            data, timestamps = file_manager.read_data(tile_id=i, n_samples=1, sample_offset=-1)

            all_data[:, i * 16 : (i + 1) * 16, :, :] = data

            # Grab antenna RMS
            tile_rms.extend(aavs_station.tiles[i].get_adc_rms())

        # ...... Create plot
        #logging.info("Time to plot")

        timestamp_day = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(timestamps[0][0]), "%Y-%m-%d")
        if not current_day == timestamp_day:
            current_day = timestamp_day
            tile_acq_timestamp = [int(timestamps[0][0])]
            potenza_rf = []
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

            prf = []

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

                ax_spectra[pol].set_ylim(-80, 0)
                #ax_spectra[pol].set_yticks(np.arange(6)*10)
                #ax_spectra[pol].set_yticklabels(np.arange(6)*10, fontsize=8)
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
                ax_rms[pol].bar(ind+0.65, tile_rms[(tile*32)+(16*pol):(tile*32)+(16*pol)+16], 0.8, color=col)
                ax_rms[pol].set_title("ADC RMS "+pols, fontsize=10)

                for k in range(16):
                    prf += [linear2dB(np.sum(dB2Linear(spectrum[:, k]))/1000000.)+12]

            potenza_rf += prf
            ax_total_power.cla()
            for j in range(32):
                serie = potenza_rf[(tile*32) + j::nof_tiles*32]
                if j < 16:
                    ax_total_power.plot(asse_x_secs, serie, color='b')
                else:
                    ax_total_power.plot(asse_x_secs, serie, color='g')
            ax_total_power.set_xlim(0, 86400)
            ax_total_power.set_xlabel("Hours", fontsize=10)
            ax_total_power.set_ylim(-15, 15)
            ax_total_power.set_ylabel("dBm", fontsize=10)
            ax_total_power.set_xticks(np.arange(0,  3 * 9 * 60 * 60, 3 * 60 * 60))
            ax_total_power.set_xticklabels(np.array(range(0, 3 * 9, 3)).astype("str").tolist())
            ax_total_power.set_title("Total Power")
            ax_total_power.grid()

            ax_title.cla()
            ax_title.set_axis_off()
            ax_title.plot([0.001, 0.002], color='w')
            ax_title.set_xlim(-20, 20)
            ax_title.set_ylim(-20, 20)
            ax_title.annotate(station_name, (-15, 10), fontsize=32, color='blue')
            ax_title.annotate(tile_names[tile * 16], (-5, -8), fontsize=28, color='green')
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
            fname = img_dir + station_name + "/" + current_day + "/" + tile_name[tile] + "_" + f_timestamp + ".png"
            fig.savefig(fname)
        logging.info("Generated plots for timestamp "+t_timestamp)


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %monitor_bandpasses [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs1_full_station.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS1)")
    parser.add_option("--dir", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data",
                      help="Directory where plots will be generated (default: /storage/monitoring/integrated_data)")

    parser.add_option("--tile", action="store", dest="tile",
                      default=16, help="Tile number [1-16]")

    (opts, args) = parser.parse_args(argv[1:])

    # Instantiate a file manager
    file_manager = ChannelFormatFileManager(root_path=opts.directory, daq_mode=FileDAQModes.Integrated)
    dic = file_manager.get_metadata(tile_id=int(opts.tile)-1)
    print "\nKEY\t\tValue\n---------------------------------------------------"
    for k in sorted(dic.keys()):
        print k, "\t", dic[k]


