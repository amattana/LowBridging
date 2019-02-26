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

    parser.add_option("--dir",
                      dest="dir",
                      default="",
                      help="Directory containing tdd files")

    parser.add_option("--start-freq",
                      dest="startfreq",
                      default=0, type="int",
                      help="Start Frequency for Waterfall")

    parser.add_option("--stop-freq",
                      dest="stopfreq",
                      default=400, type="int",
                      help="Stop Frequency for Waterfall")

    parser.add_option("--resolution",
                      dest="resolution",
                      default=100, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")

    parser.add_option("--channel",
                      dest="channel",
                      default=160,
                      help="Frequency channel in MHz to be used to plot the power")

    (options, args) = parser.parse_args()

    plt.ioff()

    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 17)
    rbw = int(closest(resolutions, options.resolution))
    avg = 2 ** rbw
    nsamples = 2 ** 17 / avg
    RBW = (avg * (400000.0 / 65536.0))

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
        fname = ""

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

    # gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])
    gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1])
    fig = plt.figure(figsize=(14, 9), facecolor='w')

    ax_water = fig.add_subplot(gs[0])
    ax_power = fig.add_subplot(gs[1])
    #ax_power_sc = fig.add_subplot(gs[2])
    #ax_wdir = fig.add_subplot(gs[2])
    #ax_humidity = fig.add_subplot(gs[3])

    bw = (nsamples / 2) + 1
    asse_x = np.linspace(0, 400, bw)

    list_spgramma = []
    xmin = closest(asse_x, int(options.startfreq))
    xmax = closest(asse_x, int(options.stopfreq))
    dic_spgramma = {}
    dayspgramma = np.empty((10, xmax - xmin + 1,))
    dayspgramma[:] = np.nan
    dic_spgramma["dwater"] = dayspgramma
    dic_spgramma["dir"] = SPG_DIR + str("%03d" % int(options.startfreq)) + "-" + str("%03d" % int(options.stopfreq))
    dic_spgramma["xmin"] = closest(asse_x, int(options.startfreq))
    dic_spgramma["xmax"] = closest(asse_x, int(options.stopfreq))
    dic_spgramma["band"] = str("%03d" % int(options.startfreq)) + "-" + str("%03d" % int(options.stopfreq))

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



    ax_power.cla()
    x = np.linspace(0, 400, len(spettro))
    ax_power.plot(x, spettro, color="b")
    ax_power.grid(True)

    # plt.title(fname.split("/")[-1][:-4].replace("_", "  "), fontsize=18)

    plt.tight_layout()

    plt.savefig(fname[:fname.rfind("/") + 1] + b["dir"] + "/" + fname.split("/")[-1][:-4] + ".png")
    os.system("rm " + fname[:fname.rfind("/") + 1] + b["dir"] + "/" + fname.split("/")[-1][:-4] + ".png")

    orari = []
    power_fb = []
    power_sc = []
    for cnt in tqdm(range(len(datafiles))):
        try:
            fname = datafiles[cnt]
            with open(fname, "r") as f:
                a = f.read()
            l = struct.unpack(">d", a[0:8])[0]
            data = struct.unpack(">" + str(int(l)) + "b", a[8:])
            spettro = calcolaspettro(data, nsamples)
            orari += [datetime.datetime.strptime(datafiles[cnt][-21:-4], "%Y-%m-%d_%H%M%S")]
            orario = datetime.datetime.strptime(fname.split("/")[-1][-21:-4], "%Y-%m-%d_%H%M%S")

            adu_rms = np.sqrt(np.mean(np.power(data, 2), 0))
            volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
            power_adc = 10 * np.log10(
                np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
            power_rf = power_adc + 12  # single ended to diff net loose 12 dBm
            power_fb.append(power_rf)

            centro = closest(x, float(options.channel))
            integra = linear2dBm(np.sum(dBm2Linear(spettro[centro - 10:centro + 10])))
            power_sc.append(integra)

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
        except:
            pass

    # print "\nReading Humidity file...",
    # humidity_x, humidity_y = read_weather(FILE_HUMIDITY, ora_inizio)
    # print "done!\nReading Temperature file...",
    # temperature_x, temperature_y = read_weather(FILE_TEMPERATURE, ora_inizio)
    # print "done!\nReading Solar Irradiation file...",
    # irradiation_x, irradiation_y = read_weather(FILE_IRRADIATION, ora_inizio)
    # print "done!\nReading Wind Direction file...",
    # wind_dir_x, wind_dir_y = read_weather(FILE_WIND_DIR, ora_inizio)
    # print "done!\nReading Wind Speed file...",
    # wind_speed_x, wind_speed_y = read_weather(FILE_WIND_SPEED, ora_inizio)
    # print "done!\n\nProcessing weather files...\n"
    # humidity_x = np.array(humidity_x)
    # temperature_x = np.array(temperature_x)
    # irradiation_x = np.array(irradiation_x)
    # wind_dir_x = np.array(wind_dir_x)
    # wind_speed_x = np.array(wind_speed_x)

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
        ax_water.set_title(" Spectrogram with RBW of %3.1f"%(RBW)+" KHz  -  " + RX_DIR[:-1].replace("_", "  ") + " " +
                           POL_DIR[:-1] + " " + fname.split("/")[-1][-22:-11].replace("_", "  "), fontsize=14)
        ax_water.set_ylabel("MHz")
        ax_water.set_xlabel('Time (UTC)')
        ax_water.set_xticks(x_tick)
        ax_water.set_xticklabels(np.array(range(0, 3*9, 3)).astype("str").tolist())
        ystep = 10
        if int(b["band"].split("-")[1]) <= 100:
            ystep = 10
        elif int(b["band"].split("-")[1]) <= 200:
            ystep = 20
        elif int(b["band"].split("-")[1]) > 200:
            ystep = 50
        BW = int(b["band"].split("-")[1]) - int(b["band"].split("-")[0])
        ytic = np.array(range(( BW / ystep) + 1 )) * ystep * (len(np.rot90(b["dwater"])) / float(BW))
        ax_water.set_yticks(len(np.rot90(b["dwater"])) - ytic)
        ylabmax = np.array(range(( BW / ystep) + 1 )) * ystep
        ax_water.set_yticklabels(ylabmax.astype("str").tolist())

        ax_power.cla()
        ax_power.plot(power_fb, color="b")
        #ax_power.plot(power_sc, color="g")
        ax_power.set_xlim(0, len(power_fb))
        ax_power.set_ylim(-15,15)
        ax_power.set_yticks(range(-15, 20, 5))
        ax_power.set_yticklabels(np.array(range(-15, 20, 5)).astype("str").tolist(), fontsize=10)
        ax_power.set_ylabel("dBm")
        #ax_power.set_title("RF Power: Full Band (Blue) and Channel "+str(int(options.channel))+" MHz (Green)", fontsize=14)
        ax_power.set_title("RF Power: Full Band", fontsize=14)
        ax_power.set_xticks(x_tick)
        ax_power.set_xticklabels(np.array(range(0, 3*9, 3)).astype("str").tolist())
        ax_power.grid(True)

        plt.tight_layout()
        # print fname[:fname.rfind("/")+1]+"PNG/"+fname.split("/")[-1][:-4]+".png"
        if not os.path.isdir(BASE_DIR + "SPECTROGRAM/" + b["dir"] + "/" + RX_DIR + POL_DIR):
            os.makedirs(BASE_DIR + "SPECTROGRAM/" + b["dir"] + "/" + RX_DIR + POL_DIR)

        plt.savefig(BASE_DIR + "SPECTROGRAM/" + b["dir"] + "/" + RX_DIR + POL_DIR + b["dir"][13:] + "_" + fname.split("/")[-1][:-11] + ".png")
    print "done!"
