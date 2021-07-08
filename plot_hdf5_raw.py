from pydaq.persisters import FileDAQModes, RawFormatFileManager
from pyaavs import station
import glob
import datetime

import aavs_utils
from aavs_utils import dt_to_timestamp, fname_to_tstamp, dB2Linear, linear2dB
import numpy as np
#import matplotlib
#matplotlib.use("tkagg")
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec

# Antenna mapping
antenna_mapping = [0, 1, 2, 3, 8, 9, 10, 11, 15, 14, 13, 12, 7, 6, 5, 4]
#antenna_mapping = range(16)
nof_samples = 20000000
COLORE=['b', 'g']

def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S.%s"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


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


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


def calcSpectra(vett):
    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett * window)
    N = len(spettro)
    acf = 2  # amplitude correction factor
    cplx = ((acf * spettro) / N)
    spettro[:] = abs((acf * spettro) / N)
    # print len(vett), len(spettro), len(np.real(spettro))
    return np.real(spettro)


def calcolaspettro(dati, nsamples=32768):
    n = int(nsamples)  # split and average number, from 128k to 16 of 8k # aavs1 federico
    sp = [dati[x:x + n] for x in range(0, len(dati), n)]
    mediato = np.zeros(len(calcSpectra(sp[0])))
    for k in sp:
        singolo = calcSpectra(k)
        mediato[:] += singolo
    mediato[:] /= (2 ** 15 / nsamples)  # federico
    with np.errstate(divide='ignore', invalid='ignore'):
        mediato[:] = 20 * np.log10(mediato / 127.0)
    d = np.array(dati, dtype=np.float64)
    adu_rms = np.sqrt(np.mean(np.power(d, 2), 0))
    volt_rms = adu_rms * (1.7 / 256.)
    with np.errstate(divide='ignore', invalid='ignore'):
        power_adc = 10 * np.log10(np.power(volt_rms, 2) / 400.) + 30
    power_rf = power_adc + 12
    return mediato, power_rf


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %aavs_check_available_data [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs2.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS1)")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data/",
                      help="Directory where plots will be generated (default: /storage/monitoring/integrated_data)")
    parser.add_option("--tile", action="store", dest="tile", type=int,
                      default=1, help="Tile Number")
    parser.add_option("--skip", action="store", dest="skip", type=int,
                      default=-1, help="Skip N blocks")
    parser.add_option("--start", action="store", dest="start",
                      default="", help="Start time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--stop", action="store", dest="stop",
                      default="", help="Stop time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--startfreq", action="store", dest="startfreq",
                      default=0, help="Plot Start Frequency")
    parser.add_option("--stopfreq", action="store", dest="stopfreq",
                      default=400, help="Plot Stop Frequency")
    parser.add_option("--date", action="store", dest="date",
                      default="", help="Stop time for filter (YYYY-mm-DD)")
    parser.add_option("--inputlist", action="store", dest="inputlist",
                      default="0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15", help="List of TPM input to save")
    parser.add_option("--resolution", dest="resolution", default=1000, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")
    parser.add_option("--power", dest="power", default="",
                      help="Compute and Plot Total Power of the given frequency")
    parser.add_option("--spectrogram", action="store_true", dest="spectrogram",
                      default=False, help="Plot Spectrograms")
    parser.add_option("--average", action="store_true", dest="average",
                      default=False, help="Compute the averaged Spectrum")
    parser.add_option("--yticks", action="store_true", dest="yticks",
                      default=False, help="Maximize Y Ticks in Spectrograms")
    parser.add_option("--pol", action="store", dest="pol",
                      default="x", help="Spectrograms Polarization")
    parser.add_option("--save", action="store_true", dest="save",
                      default=False, help="Save txt data")
    parser.add_option("--outfile", action="store", dest="outfile",
                      default="", help="Destination file")
    parser.add_option("--saveraw", action="store_true", dest="saveraw",
                      default=False, help="Save Raw data in files")
    parser.add_option("--outpath", action="store", dest="outpath",
                      default="/storage/monitoring/saved_data/", help="Destination folder")

    (opts, args) = parser.parse_args(argv[1:])

    t_date = None
    t_start = None
    t_stop = None
    t_cnt = 0

    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 15)
    rbw = int(closest(resolutions, opts.resolution))
    avg = 2 ** rbw
    nsamples = int(2 ** 15 / avg)
    RBW = (avg * (400000.0 / 16384.0))
    asse_x = np.arange(nsamples/2 + 1) * RBW * 0.001
    #remap = [0, 1, 2, 3, 8, 9, 10, 11, 15, 14, 13, 12, 7, 6, 5, 4]
    #remap = [0, 1, 2, 3, 12, 13, 14, 15, 7, 6, 5, 4, 11, 10, 9, 8]
    remap = range(16)
    print("Frequency resolution set %3.1f KHz" % resolutions[rbw])

    if opts.date:
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
            t_start = dt_to_timestamp(t_date)
            t_stop = dt_to_timestamp(t_date) + (60 * 60 * 24)
        except:
            print("Bad date format detected (must be YYYY-MM-DD)")
    else:
        if opts.start:
            try:
                t_start = dt_to_timestamp(datetime.datetime.strptime(opts.start, "%Y-%m-%d_%H:%M:%S"))
                print("Start Time:  " + ts_to_datestring(t_start))
            except:
                print("Bad t_start time format detected (must be YYYY-MM-DD_HH:MM:SS)")
        if opts.stop:
            try:
                t_stop = dt_to_timestamp(datetime.datetime.strptime(opts.stop, "%Y-%m-%d_%H:%M:%S"))
                print("Stop  Time:  " + ts_to_datestring(t_stop))
            except:
                print("Bad t_stop time format detected (must be YYYY-MM-DD_HH:MM:SS)")

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']
    print("\nStation Name: ", station_name)
    print("Checking directory: ", opts.directory + "\n")

    file_manager = RawFormatFileManager(root_path=opts.directory, daq_mode=FileDAQModes.Burst)

    lista = sorted(glob.glob(opts.directory + "/raw_burst_%d_*hdf5" % (int(opts.tile)-1)))
    nof_tiles = 16
    print("\nFound %d hdf5 files for Tile-%02d\n" % (len(lista), int(opts.tile)))

    #plt.ioff()
    if len(lista):
        if len(opts.inputlist.split(",")) == 1:
            rows = 1
            cols = 1
        elif len(opts.inputlist.split(",")) == 2:
            rows = 2
            cols = 1
        else:
            rows = int(np.ceil(np.sqrt(len(opts.inputlist.split(",")))))
            cols = int(np.ceil(np.sqrt(len(opts.inputlist.split(",")))))
        gs = gridspec.GridSpec(rows, cols, wspace=0.4, hspace=0.6, top=0.9, bottom=0.09, left=0.08, right=0.96)
        fig = plt.figure(figsize=(14, 9), facecolor='w')

        meas = {}
        if opts.spectrogram:
            p = 0
            if opts.pol.lower() == "y":
                p = 1
            band = str(opts.startfreq) + "-" + str(opts.stopfreq)
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
                ystep = 50
            if opts.yticks:
                ystep = 1
            xmin = closest(asse_x, int(opts.startfreq))
            xmax = closest(asse_x, int(opts.stopfreq))
            wclim = (-100, -10)
            fig.suptitle("Tile-%02d Spectrograms (RBW: %3.1f KHz)" % (int(opts.tile), RBW), fontsize=16)
            allspgram = []
            ax = []
            for num, tpm_input in enumerate(opts.inputlist.split(",")):
                ant = int(tpm_input)
                ax += [fig.add_subplot(gs[num])]
                allspgram += [[]]
                allspgram[num] = np.empty((10, xmax - xmin + 1,))
                allspgram[num][:] = np.nan

                ax[num].cla()
                ax[num].set_title("Input-%02d" % (ant), fontsize=12)
                ax[num].imshow(allspgram[num], interpolation='none', aspect='auto', extent=[xmin, xmax, 60, 0], cmap='jet', clim=wclim)
                ax[num].set_ylabel("MHz")
                ax[num].set_xlabel('time')

        else:
            if opts.power == "":
                fig.suptitle("Tile-%02d Spectra (RBW: %3.1f KHz)" % (int(opts.tile), RBW), fontsize=16)
                ax = []
                for num, tpm_input in enumerate(opts.inputlist.split(",")):
                    ant = int(tpm_input)
                    ax += [fig.add_subplot(gs[num])]
                    ax[num].set_title("Input-%02d" % (ant), fontsize=12)
                    ax[num].set_xlim(asse_x[closest(asse_x, float(opts.startfreq))],
                                     asse_x[closest(asse_x, float(opts.stopfreq))])
                    ax[num].set_ylim(-100, 20)
                    ax[num].set_ylabel("dB", fontsize=10)
                    ax[num].set_xlabel("MHz", fontsize=10)
                    ax[num].tick_params(axis='both', which='major', labelsize=8)
                    ax[num].grid()

            else:
                fig.suptitle("Tile-%02d Power of Frequency Channel %3.1f MHz (RBW: %3.1f KHz)  -  from %s  to  %s" %
                             (int(opts.tile), float(opts.power), RBW,
                              ts_to_datestring(fname_to_tstamp(lista[0][-21:-7]), formato="%Y-%m-%d %H:%M:%S"),
                              ts_to_datestring(fname_to_tstamp(lista[-1][-21:-7]), formato="%Y-%m-%d %H:%M:%S")),
                             fontsize=14)
                ax = []
                for num, tpm_input in enumerate(opts.inputlist.split(",")):
                    ant = int(tpm_input)
                    ax += [fig.add_subplot(gs[num])]
                    ax[num].set_title("Input-%02d" % (ant), fontsize=12)
                    ax[num].set_ylim(-20, 20)
                    ax[num].set_xlim(0, len(lista))
                    ax[num].set_ylabel("dB", fontsize=10)
                    ax[num].set_xlabel("timestamp", fontsize=10)
                    ax[num].tick_params(axis='both', which='major', labelsize=8)
                    ax[num].grid()
                    for npol, pol in enumerate(["Pol-X", "Pol-Y"]):
                        meas["Input-%02d_%s" % (ant, pol)] = []
                norm_factor = []

        for nn, l in enumerate(lista):
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(int(opts.tile)-1))
            if file_manager.file_partitions(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(int(opts.tile)-1)) == 0:
                total_samples = file_manager.n_samples * file_manager.n_blocks
            else:
                total_samples = file_manager.n_samples * file_manager.n_blocks * \
                                (file_manager.file_partitions(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(int(opts.tile)-1)))
            nof_blocks = total_samples
            nof_antennas = file_manager.n_antennas * nof_tiles

            data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), n_samples=total_samples,
                                                      tile_id=(int(opts.tile) - 1))
            timestamps = int(dic['timestamp'])
            dtimestamp = ts_to_datestring(timestamps, formato="%Y-%m-%d %H:%M:%S")
            data = data[antenna_mapping, :, :].transpose((0, 1, 2))

            if opts.spectrogram:
                for num, tpm_input in enumerate(opts.inputlist.split(",")):
                    ant = int(tpm_input) - 1
                    print("%s Processing Input-%02d" % (dtimestamp, ant))
                    spettro, rms = calcolaspettro(data[remap[ant], p, :], nsamples)
                    allspgram[num] = np.concatenate((allspgram[num], [spettro[xmin:xmax + 1]]), axis=0)
            else:
                if opts.power == "":
                    for num, tpm_input in enumerate(opts.inputlist.split(",")):
                        ant = int(tpm_input) - 1
                        print("%s Processing Input-%02d" % (dtimestamp, ant))
                        for npol, pol in enumerate(["Pol-X", "Pol-Y"]):
                            if opts.average:
                                spettro, rms = calcolaspettro(data[remap[ant], npol, :], nsamples)
                                if not nn:
                                    meas["Input-%02d_%s" % (ant, pol)] = dB2Linear(spettro)
                                else:
                                    meas["Input-%02d_%s" % (ant, pol)][:] += dB2Linear(spettro)
                            else:
                                meas["Input-%02d_%s" % (ant, pol)], rms = calcolaspettro(data[remap[ant], npol, :], nsamples)
                                ax[num].plot(asse_x[3:], meas["Input-%02d_%s" % (ant, pol)][3:], color=COLORE[npol])
                                if (nn == (len(lista)-1)):
                                    if cols == 1:
                                        if rows == 1:
                                            ax[num].annotate("RF Power: %3.1f dBm" % rms, (300, 15 - (npol * 5)), fontsize=16,
                                                        color=COLORE[npol])
                                        else:
                                            ax[num].annotate("RF Power: %3.1f dBm" % rms, (300, 10 - (npol * 10)), fontsize=16,
                                                        color=COLORE[npol])
                                    else:
                                        ax[num].annotate("RF Power: %3.1f dBm" % rms, (180 - cols * 7, 5 - (npol * 15)),
                                                         fontsize=14 - cols, color=COLORE[npol])
                else:
                    for num, tpm_input in enumerate(opts.inputlist.split(",")):
                        ant = int(tpm_input) - 1
                        print("%s Processing Input-%02d" % (dtimestamp, ant))
                        for npol, pol in enumerate(["Pol-X", "Pol-Y"]):
                            spettro, rms = calcolaspettro(data[remap[ant], npol, :], nsamples)
                            if not nn:
                                norm_factor += [spettro[closest(asse_x, float(opts.power))]]
                            meas["Input-%02d_%s" % (ant, pol)] += [spettro[closest(asse_x, float(opts.power))] - norm_factor[num * 2 + npol]]

            if not opts.power == "":
                for num, tpm_input in enumerate(opts.inputlist.split(",")):
                    ant = int(tpm_input) - 1
                    for npol, pol in enumerate(["Pol-X", "Pol-Y"]):
                        ax[num].plot(meas["Input-%02d_%s" % (ant, pol)], color=COLORE[npol])
        if opts.spectrogram:
            for num, tpm_input in enumerate(opts.inputlist.split(",")):
                first_empty, allspgram[num] = allspgram[num][:10], allspgram[num][10:]
                ax[num].imshow(np.rot90(allspgram[num]), interpolation='none', aspect='auto', cmap='jet', clim=wclim)
                BW = int(band.split("-")[1]) - int(band.split("-")[0])
                ytic = np.array(range(int(BW / ystep) + 1)) * ystep * (len(np.rot90(allspgram[num])) / float(BW))
                ax[num].set_yticks(len(np.rot90(allspgram[num])) - ytic)
                ylabmax = (np.array(range(int(BW / ystep) + 1)) * ystep) + int(band.split("-")[0])
                ax[num].set_yticklabels(ylabmax.astype("str").tolist())

        if opts.average:
            for num, tpm_input in enumerate(opts.inputlist.split(",")):
                ant = int(tpm_input) - 1
                print("%s Processing Input-%02d" % (dtimestamp, ant))
                for npol, pol in enumerate(["Pol-X", "Pol-Y"]):
                    meas["Input-%02d_%s" % (ant, pol)] /= len(lista)
                    ax[num].plot(asse_x[3:], linear2dB(meas["Input-%02d_%s" % (ant, pol)])[3:], color=COLORE[npol])

        plt.show()



