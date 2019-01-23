#!/usr/bin/env python

'''

   TPM Spectra Processing

   Used to plot spectra saved using tpm_dump.py

'''

__copyright__ = "Copyright 2018, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import sys

sys.path.append("../SKA-AAVS1/tools")
sys.path.append("../SKA-AAVS1/tools/board")
sys.path.append("../SKA-AAVS1/tools/pyska")
sys.path.append("../SKA-AAVS1/tools/rf_jig")
sys.path.append("../SKA-AAVS1/tools/config")
sys.path.append("../SKA-AAVS1/tools/repo_utils")

from matplotlib import pyplot as plt
import struct, os, easygui, glob
from optparse import OptionParser
import numpy as np
# from tpm_utils import *
import matplotlib.gridspec as gridspec
import datetime, time
from tqdm import tqdm

BASE_DIR = "/data/data_2/2018-11-LOW-BRIDGING/"
SPG_DIR = "SPECTROGRAMS_BAND_"
FILE_HUMIDITY = "/data/data_2/2018-11-LOW-BRIDGING/WEATHER/Humidity.txt"
FILE_TEMPERATURE = "/data/data_2/2018-11-LOW-BRIDGING/WEATHER/Temperature.txt"
FILE_IRRADIATION = "/data/data_2/2018-11-LOW-BRIDGING/WEATHER/Irradiation.txt"
FILE_WIND_SPEED = "/data/data_2/2018-11-LOW-BRIDGING/WEATHER/WindSpeed.txt"
FILE_WIND_DIR = "/data/data_2/2018-11-LOW-BRIDGING/WEATHER/WindDir.txt"

epoch = datetime.datetime(1970,1,1)


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

def toTimestamp(t):
	dt = t - epoch
	return (dt.microseconds + (dt.seconds + dt.days * 86400) * 10**6) / 10**6

def read_weather(F, giorno):
    with open(F) as f:
        data = f.readlines()
    weather_data = []
    #hours = []
    x = []
    #cnt = 0
    for d in data:
        if d[0] == "#" or d[0] == " " or len(d.split()) == 0:
            pass
        else:
            #dati = d.replace("\n", "").replace("  ", "\t").split("\t")
            t = datetime.datetime.strptime(d.split()[1] + " " + d.split()[2][:-5], "%Y-%m-%d %H:%M:%S")
            if giorno.date() == t.date():
                x += [toTimestamp(t)]
                #hours += [t.hour]
                weather_data += [float(d.split()[3])]
                #cnt = cnt + 1
    return x, weather_data



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


if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("--file",
                      dest="infile",
                      default="",
                      help="Input Time Domain Data file '.tdd' saved using tpm_dump.py")

    parser.add_option("--average",
                      dest="average",
                      default=16,
                      help="Number of time domain segments to be averaged. 1 means NO average")

    parser.add_option("--framerate",
                      dest="framerate",
                      default=60, type="int",
                      help="Frame rate in minutes of saved waterfall pictures")

    parser.add_option("--dir",
                      dest="dir",
                      default="",
                      help="Directory containing tdd files")

    parser.add_option("--raw", action="store_true",
                      dest="raw",
                      default=False,
                      help="Plot also ADC Raw data")

    parser.add_option("--recursive", action="store_true",
                      dest="recursive",
                      default=False,
                      help="Plot recursively all the directory files, sorted by name")

    parser.add_option("--water", action="store_true",
                      dest="water",
                      default=False,
                      help="Plot waterfall, requires recursive mode")

    parser.add_option("--power", action="store_true",
                      dest="power",
                      default=False,
                      help="Plot Power of a channel, requires recursive mode")

    parser.add_option("--maxhold", action="store_true",
                      dest="maxhold",
                      default=False,
                      help="Plot MaxHold")

    parser.add_option("--minhold", action="store_true",
                      dest="minhold",
                      default=False,
                      help="Plot MaxHold")

    parser.add_option("--channel",
                      dest="channel",
                      default=160,
                      help="Frequency channel in MHz to be used to plot the power")

    parser.add_option("--start-freq",
                      dest="startfreq",
                      default=0, type="int",
                      help="Start Frequency for Waterfall")

    parser.add_option("--stop-freq",
                      dest="stopfreq",
                      default=400, type="int",
                      help="Stop Frequency for Waterfall")

    parser.add_option("--band",
                      dest="band",
                      default="0-400",
                      help="Comma separated bands (example: 0-400,0-50,50-100)")

    (options, args) = parser.parse_args()

    plt.ioff()

    nsamples = 2 ** 17 / int(options.average)

    if not options.dir == "":
        datapath = options.dir
        # print "\nListing directory:", datapath
        datafiles = sorted(glob.glob(datapath + "/*.tdd"))
        # print "Found "+str(len(datafiles))+" \"tdd\" files.\n"
        if len(datafiles) > 0:
            fname = datafiles[0]
        else:
            print "No tdd files found in directory: " + datapath + "\nExiting..."
            exit(0)
    else:
        fname = options.infile

    if fname == "":
        fname = easygui.fileopenbox(title="Choose a tdd file", default="/data/data_2/2018-11-LOW-BRIDGING/",
                                    filetypes="tdd")
    if not os.path.isfile(fname):
        print "Invalid file! \n"
        exit(0)

    datapath = fname[:fname.rfind("/")]
    print "\nListing directory:", datapath
    datafiles = sorted(glob.glob(datapath + "/*.tdd"))
    print "Found " + str(len(datafiles)) + " \"tdd\" files.\n"

    if int(options.average) < 1:
        print "Average value must be greater than zero!"
        exit(0)

    RBW = (int(options.average) * (400000.0 / 65536.0))

    # gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 1, 1, 1])
    fig = plt.figure(figsize=(12, 9), facecolor='w')

    ax_water = fig.add_subplot(gs[0])
    ax_wspeed = fig.add_subplot(gs[1])
    ax_wdir = fig.add_subplot(gs[2])
    ax_humidity = fig.add_subplot(gs[3])

    bw = nsamples / 2
    asse_x = np.linspace(0, 400, bw)

    list_spgramma = []
    band_list = options.band.split(",")
    for b in band_list:
        xmin = closest(asse_x, int(b.split("-")[0]))
        xmax = closest(asse_x, int(b.split("-")[1]))
        dic_spgramma = {}
        dayspgramma = np.empty((10, xmax - xmin + 1,))
        dayspgramma[:] = np.nan
        dic_spgramma["dwater"] = dayspgramma
        dic_spgramma["band"] = b
        dic_spgramma["dir"] = SPG_DIR + str("%03d" % int(b.split("-")[0])) + "-" + str("%03d" % int(b.split("-")[1]))
        dic_spgramma["xmin"] = closest(asse_x, int(b.split("-")[0]))
        dic_spgramma["xmax"] = closest(asse_x, int(b.split("-")[1]))
        if "EDA2" in fname:
            dic_spgramma["wclim"] = (-70, -40)
        else:
            dic_spgramma["wclim"] = (-80, -30)
        list_spgramma.append(dic_spgramma)
        #print b, dic_spgramma["xmin"], dic_spgramma["xmax"], asse_x[dic_spgramma["xmin"]],asse_x[dic_spgramma["xmax"]]
    #exit(0)

    fname = datafiles[0]
    plt.ion()
    for b in list_spgramma:
        if not os.path.isdir(datapath + "/" + b["dir"]):
            os.makedirs(datapath + "/" + b["dir"])
    RX_DIR = fname.split("/")[-3] + "/"
    POL_DIR = fname.split("/")[-2] + "/"

    with open(fname, "r") as f:
        a = f.read()
    l = struct.unpack(">d", a[0:8])[0]
    data = struct.unpack(">" + str(int(l)) + "b", a[8:])
    spettro = calcolaspettro(data, nsamples)
    max_hold = np.array(spettro)
    min_hold = np.array(spettro)
    ora_inizio = datetime.datetime.strptime(fname.split("/")[-1][-21:-4], "%Y-%m-%d_%H%M%S")

    if ((options.startfreq == 0) and (options.stopfreq == 400)):
        if "EDA2" in fname:
            wclim = (-70, -40)
            print "Setting waterfall colors for EDA2"
        else:
            wclim = (-80, -30)
            print "Setting waterfall colors for SKALA-4"
    else:
        wclim = (min(spettro[xmin:xmax + 1]), max(spettro[xmin:xmax + 1]))
    ax_water.cla()
    ax_water.imshow(dayspgramma, interpolation='none', aspect='auto', extent=[xmin, xmax, 60, 0], cmap='jet',
               clim=wclim)
    #ax_water.set_title(" Spectrogram of " + str(len(spgramma)) + " spectra")
    ax_water.set_ylabel("Time (minutes)")
    ax_water.set_xlabel('MHz')

    ax_wspeed.cla()
    x = np.linspace(0, 400, len(spettro))
    ax_wspeed.plot(x, spettro, color="b")
    #ax_wspeed.plot(x, max_hold, color="r")
    #ax_wspeed.plot(x, min_hold, color="g")
    # ax_wspeed.set_xlim(0, 400)
    # ax_wspeed.set_ylim(-100, 0)
    # ax_wspeed.set_xlabel('MHz')
    # ax_wspeed.set_ylabel("dBm")
    # ax_wspeed.set_title("Power Spectrum", fontsize=10)
    ax_wspeed.grid(True)

    # plt.title(fname.split("/")[-1][:-4].replace("_", "  "), fontsize=18)

    plt.tight_layout()

    plt.savefig(fname[:fname.rfind("/") + 1] + b["dir"] + "/" + fname.split("/")[-1][:-4] + ".png")
    os.system("rm " + fname[:fname.rfind("/") + 1] + b["dir"] + "/" + fname.split("/")[-1][:-4] + ".png")

    orari = []
    for cnt in tqdm(range(len(datafiles))):

        fname = datafiles[cnt]
        orari += [datetime.datetime.strptime(datafiles[cnt][-21:-4], "%Y-%m-%d_%H%M%S")]
        # print fname.split("/")[-1][-21:-4]
        orario = datetime.datetime.strptime(fname.split("/")[-1][-21:-4], "%Y-%m-%d_%H%M%S")
        with open(fname, "r") as f:
            a = f.read()
        l = struct.unpack(">d", a[0:8])[0]
        data = struct.unpack(">" + str(int(l)) + "b", a[8:])
        spettro = calcolaspettro(data, nsamples)

        adu_rms = np.sqrt(np.mean(np.power(data, 2), 0))
        volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
        power_adc = 10 * np.log10(
            np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
        power_rf = power_adc + 12  # single ended to diff net loose 12 dBm

        # per ognuno
        for b in list_spgramma:
            #last, b["water"] = b["water"][0], b["water"][1:]
            #last, spgramma = spgramma[0], spgramma[1:]
            # print len(spgramma), len(spgramma[0]), bw, len(spettro), len(spettro[xmin:xmax+1])
            if b["xmin"] == 0:
                # se xmin == 0 butto il canale zero
                b["dwater"] = np.concatenate((b["dwater"], [spettro[:b["xmax"] + 1].astype(np.float)]), axis=0)
            else:
                b["dwater"] = np.concatenate((b["dwater"], [spettro[b["xmin"]:b["xmax"] + 1].astype(np.float)]), axis=0)

        #if ((orario - ora_inizio).seconds / 60.) > options.framerate:

            #for b in list_spgramma:
                #while np.isnan(b["water"][0][0]):
                #    last, b["water"] = b["water"][0], b["water"][1:]
                #b["dwater"] = np.concatenate((b["dwater"], b["water"]), axis=0)
            #print len(b["water"]), len(b["dwater"])

        #    ora_inizio = orario

    # for b in list_spgramma:
    #     while np.isnan(b["water"][0][0]):
    #         print "PRIMA", len()
    #         last, b["water"] = b["water"][0], b["water"][1:]
    #     b["dwater"] = np.concatenate((b["dwater"], b["water"]), axis=0)
    # #print len(b["water"]), len(b["dwater"])

    # for b in list_spgramma:
    #     ax_water.cla()
    #     if b["band"] == "0-400":
    #         ax_water.imshow(b["water"], interpolation='none', aspect='auto', extent=[asse_x[b["xmin"]], asse_x[b["xmax"]], 1, 0],
    #                cmap='jet', clim=b["wclim"])
    #     else:
    #         ax_water.imshow(b["water"], interpolation='none', aspect='auto', extent=[asse_x[b["xmin"]], asse_x[b["xmax"]], 1, 0],
    #                cmap='jet')
    #         ax_water.set_title(" Spectrogram of " + str(len(b["water"])) + " spectra")
    #         ax_water.set_ylabel("Time (minutes)")
    #         ax_water.set_xlabel('MHz')
    #
    #     ax_wspeed.cla()
    #     x = np.linspace(0, 400, len(spettro))
    #     ax_wspeed.plot(x, spettro, color="b")
    #     if options.maxhold:
    #         ax_wspeed.plot(x, max_hold, color="r")
    #     if options.minhold:
    #         ax_wspeed.plot(x, min_hold, color="g")
    #     ax_wspeed.set_xlim(asse_x[b["xmin"]], asse_x[b["xmax"]])
    #     # ax2.set_ylim(-90, -40)
    #     # ax_wspeed.set_ylim(-100, 0)
    #     # ax_wspeed.set_xlabel('MHz')
    #     # ax_wspeed.set_ylabel("dBm")
    #     # ax_wspeed.set_title("Power Spectrum", fontsize=10)
    #     # ax_wspeed.annotate("RF Power: " + "%3.1f" % (power_rf) + " dBm", (10, -15), fontsize=16)
    #     # ax_wspeed.annotate("RBW: " + str("%3.1f" % RBW) + "KHz", (320, -15), fontsize=12)
    #     ax_wspeed.grid(True)
    #
    #     # plt.title(fname.split("/")[-1][:-4].replace("_", "  "), fontsize=18)
    #
    #     plt.tight_layout()
    #     # print fname[:fname.rfind("/")+1]+"PNG/"+fname.split("/")[-1][:-4]+".png"
    #     plt.savefig(fname[:fname.rfind("/") + 1] + b["dir"] + "/" + fname.split("/")[-1][:-4] + ".png")
    #
    #     # spgramma = np.empty((1000, bw - 5,))
    #     # spgramma[:] = np.nan
    #     ora_inizio = orario

    print "\nReading Humidity file...",
    humidity_x, humidity_y = read_weather(FILE_HUMIDITY, ora_inizio)
    print "done!\nReading Temperature file...",
    temperature_x, temperature_y = read_weather(FILE_TEMPERATURE, ora_inizio)
    print "done!\nReading Solar Irradiation file...",
    irradiation_x, irradiation_y = read_weather(FILE_IRRADIATION, ora_inizio)
    print "done!\nReading Wind Direction file...",
    wind_dir_x, wind_dir_y = read_weather(FILE_WIND_DIR, ora_inizio)
    print "done!\nReading Wind Speed file...",
    wind_speed_x, wind_speed_y = read_weather(FILE_WIND_SPEED, ora_inizio)
    print "done!\n\nProcessing weather files...\n"
    humidity_x = np.array(humidity_x)
    temperature_x = np.array(temperature_x)
    irradiation_x = np.array(irradiation_x)
    wind_dir_x = np.array(wind_dir_x)
    wind_speed_x = np.array(wind_speed_x)

    x_tick = []
    step = 0
    for z in range(len(orari)):
        if orari[z].hour == step:
            #print str(orari[z])
            x_tick += [z]
            step = step + 3
    #print str(orari[-1])
    x_tick += [len(b["dwater"][10:])]
    #print "ORARI:", len(orari), "D", len(b["dwater"][10:])

    for b in list_spgramma:
        first_empty, b["dwater"] = b["dwater"][:10], b["dwater"][10:]
        ax_water.cla()
        ax_water.imshow(np.rot90(b["dwater"]), interpolation='none', aspect='auto', cmap='jet', clim=b["wclim"])
        ax_water.set_title(" Spectrogram of " + fname.split("/")[-1][:-11].replace("_", "  "), fontsize=14)
        ax_water.set_ylabel("MHz")
        ax_water.set_xlabel('daytime')
        ax_water.set_xticks(x_tick)
        ax_water.set_xticklabels(np.array(range(0, 3*9, 3)).astype("str").tolist())
        if int(b["band"].split("-")[1]) <= 100:
            ystep = 10
        elif int(b["band"].split("-")[1]) <= 200:
            ystep = 20
        elif int(b["band"].split("-")[1]) > 200:
            ystep = 50
        BW = int(b["band"].split("-")[1]) - int(b["band"].split("-")[0])
        #ytic = np.array(range(((int(b["band"].split("-")[1])-int(b["band"].split("-")[0])) / ystep))) * int((len(np.rot90(b["dwater"])) / ((int(b["band"].split("-")[1])-int(b["band"].split("-")[0])) )))
        ytic = np.array(range(( BW / ystep) + 1 )) * ystep * (len(np.rot90(b["dwater"])) / float(BW))
        #ytic = np.concatenate(ytic, len(np.rot90(b["dwater"])))
        ax_water.set_yticks(len(np.rot90(b["dwater"])) - ytic)
        #ylabmax = np.array(range(0,(int(b["band"].split("-")[1])/ystep) +1))*ystep
        ylabmax = np.array(range(( BW / ystep) + 1 )) * ystep
        ax_water.set_yticklabels(ylabmax.astype("str").tolist()[::-1])
        #print x_tick, np.array(range(0, 3*9, 3)).astype("str").tolist()

        # humidity
        ax_humidity.cla()
        serie_humidity = []
        serie_temperature = []
        serie_irradiation = []
        serie_wind_dir = []
        serie_wind_speed = []
        for i in tqdm(range(len(orari))):
            ora_x = toTimestamp(orari[i])
            serie_humidity += [humidity_y[closest(humidity_x, ora_x)]]
            serie_temperature += [temperature_y[closest(temperature_x, ora_x)]]
            serie_irradiation += [irradiation_y[closest(irradiation_x, ora_x)]/20]
            serie_wind_dir += [wind_dir_y[closest(wind_dir_x, ora_x)]]
            serie_wind_speed += [wind_speed_y[closest(wind_speed_x, ora_x)]]

        ax_wspeed.cla()
        ax_wspeed.plot(serie_wind_speed)
        #ax_wspeed.plot(wind_speed_y)
        ax_wspeed.set_xlim(0, len(serie_wind_speed))
        ax_wspeed.set_ylim(0,40)
        ax_wspeed.set_yticks(range(0, 10*5, 10))
        ax_wspeed.set_title("Wind Speed", fontsize=14)
        ax_wspeed.set_xticks(x_tick)
        ax_wspeed.set_xticklabels(np.array(range(0, 3*9, 3)).astype("str").tolist())

        ax_wspeed.grid(True)
        ax_wdir.cla()
        ax_wdir.plot(serie_wind_dir)
        #ax_wdir.plot(wind_dir_y)
        ax_wdir.set_xlim(0, len(serie_wind_speed))
        ax_wdir.set_ylim(0, 360)
        ax_wdir.set_yticks(range(0, 90*5, 90))
        ax_wdir.set_title("Wind Direction (0-180 = N-S)", fontsize=14)
        ax_wdir.grid(True)
        ax_wdir.set_xticks(x_tick)
        ax_wdir.set_xticklabels(np.array(range(0, 3*9, 3)).astype("str").tolist())

        ax_humidity.cla()
        ax_humidity.plot(serie_humidity, color='b', label="Humidity")
        ax_humidity.plot(serie_temperature, color='r', label="Temperature")
        ax_humidity.plot(serie_irradiation, color='g', label="Irradiation")
        #ax_humidity.plot(humidity_y)
        ax_humidity.set_xlim(0, len(serie_wind_speed))
        ax_humidity.set_ylim(0, 50)
        ax_humidity.set_yticks(range(0, 10 * 7, 10))
        ax_humidity.set_title("Humidity (Blue), Temperature (Red) and Solar Irradiation* (Green)   *:[1/20]", fontsize=14)
        #ax_humidity.legend(fontsize=10)
        ax_humidity.grid(True)
        ax_humidity.set_xticks(x_tick)
        ax_humidity.set_xticklabels(np.array(range(0, 3*9, 3)).astype("str").tolist())

        plt.tight_layout()
        # print fname[:fname.rfind("/")+1]+"PNG/"+fname.split("/")[-1][:-4]+".png"
        if not os.path.isdir(BASE_DIR + "SPECTROGRAM/" + b["dir"] + "/" + RX_DIR + POL_DIR):
            os.makedirs(BASE_DIR + "SPECTROGRAM/" + b["dir"] + "/" + RX_DIR + POL_DIR)

        plt.savefig(BASE_DIR + "SPECTROGRAM/" + b["dir"] + "/" + RX_DIR + POL_DIR + b["dir"][13:] + "_" + fname.split("/")[-1][:-11] + ".png")
    print "done!"
