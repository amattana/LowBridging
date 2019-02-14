#!/usr/bin/env python

'''

   TPM Spectra Viever 

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


if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("--dir",
                      dest="dir",
                      default="",
                      help="Directory containing tdd files")

    parser.add_option("--out",
                      dest="fout",
                      default="",
                      help="Output Filename of the txt file")

    parser.add_option("--start-freq",
                      dest="startfreq",
                      default=0, type="int",
                      help="Start Frequency for Waterfall")

    parser.add_option("--stop-freq",
                      dest="stopfreq",
                      default=400, type="int",
                      help="Stop Frequency for Waterfall")

    parser.add_option("--wclim",
                      dest="wclim",
                      default="auto",
                      help="Waterfall Color Limits (String like: \"-70,-30\", default \"auto\" that means autoscale)")

    parser.add_option("--resolution",
                      dest="resolution",
                      default=100, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")



    (options, args) = parser.parse_args()

    plt.ioff()

    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 17)
    rbw = int(closest(resolutions, options.resolution))
    avg = 2 ** rbw

    nsamples = 2 ** 17 / avg

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
        fname = easygui.fileopenbox(title="Choose a tdd file", default="/data/data_2/2018-11-LOW-BRIDGING/",
                                    filetypes="tdd")
    if not os.path.isfile(fname):
        print "Invalid file! \n"
        exit(0)

    datapath = fname[:fname.rfind("/")]
    print "\nListing directory:", datapath
    datafiles = sorted(glob.glob(datapath + "/*.tdd"))
    print "Found " + str(len(datafiles)) + " \"tdd\" files.\n"

    RBW = (avg * (400000.0 / 65536.0))


    bw = nsamples / 2
    asse_x = np.linspace(0, 400, bw)
    xmin = closest(asse_x, options.startfreq)
    xmax = closest(asse_x, options.stopfreq)

    spgramma = np.empty((10, xmax - xmin + 1,))
    spgramma[:] = np.nan

    SPG_DIR += str("%03d" % int(options.startfreq)) + "-" + str("%03d" % int(options.stopfreq))

    fname = datafiles[0]
    plt.ion()
    if not os.path.isdir(datapath + "/" + SPG_DIR):
        os.makedirs(datapath + "/" + SPG_DIR)
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
    asse_x = np.linspace(0,400,len(spettro))

    if (options.startfreq == 0) and (options.stopfreq == 400):
        if "EDA2" in fname:
            wclim = (-70, -40)
            print "Setting waterfall colors for EDA2"
        else:
            wclim = (-80, -30)
            print "Setting waterfall colors for SKALA-4"
    else:
        if options.wclim == "auto":
            wclim = (min(spettro[xmin:xmax + 1]), max(spettro[xmin:xmax + 1]))
        else:
            wclim = (int(options.wclim.split(",")[0]), int(options.wclim.split(",")[1]))

    #ax1.cla

    if options.fout == "":
        foutname = fname[:-4] + "_RBW-" + str("%03d" % int(RBW)) + "KHz.csv"
    else:
        outpath = "/".join(fname.split("/")[:-4])+"/CSV"
        if not os.path.isdir(outpath):
            os.makedirs(outpath)
        foutname = outpath + "/" + options.fout

    print "Writing output text file: ",foutname
    fout = open(foutname, "w")
    fout.write(fname.split("/")[-1][-21:-11] + "\t" + "FREQ")
    for i in range(len(asse_x)):
        fout.write(str("\t%9.6f" % asse_x[i]))
    fout.write("\n")
    for cnt in tqdm(range(len(datafiles))):
        fname = datafiles[cnt]
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

        #print power_rf, 0 - power_rf, spettro[100], spettro[100] + (0 - power_rf)
        #spettro += (0 - power_rf) # Equalizzazione a zero

        if power_rf < 8:
            nmax_hold = np.maximum(spettro.astype(np.float), max_hold.astype(np.float))
            max_hold = nmax_hold
            if power_rf > -20:
                nmin_hold = np.minimum(spettro.astype(np.float), min_hold.astype(np.float))
                min_hold = nmin_hold

            spgramma = np.concatenate((spgramma, [spettro[xmin:xmax + 1].astype(np.float)]), axis=0)

        fout.write(fname.split("/")[-1][-21:-4]+"\t"+str("%3.1f" % power_rf))
        for i in range(len(spettro)):
            fout.write(str("\t%3.1f" % spettro[i]))
        fout.write("\n")
        fout.flush()
    fout.close()

    first_empty, spgramma = spgramma[:10], spgramma[10:]

    # gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])
    gs = gridspec.GridSpec(2, 1, height_ratios=[6, 3])
    fig = plt.figure(figsize=(12,7), facecolor='w', dpi=100)

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    ax1.cla()
    ax1.imshow(spgramma, interpolation='none', aspect='auto', extent=[asse_x[xmin], asse_x[xmax], 1, 0],
               cmap='jet', clim=wclim)
    ax1.set_title(" Spectrogram of " + fname.split("/")[-1][:-11].replace("_", "  "), fontsize=14)
    ax1.set_ylabel("Time")
    ax1.set_xlabel('MHz')

    ax2.cla()
    x = np.linspace(0, 400, len(spettro))
    ax2.plot(x, max_hold, color="r")
    ax2.plot(x, min_hold, color="g")
    ax2.set_xlim(asse_x[xmin], asse_x[xmax])
    # ax2.set_ylim(-90, -40)
    ax2.set_ylim(-100, 0)
    ax2.set_xlabel('MHz')
    ax2.set_ylabel("dBm")
    ax2.set_title("Power Spectrum", fontsize=10)
    # ax2.annotate("RF Power: " + "%3.1f" % (power_rf) + " dBm", (10, -15), fontsize=16)
    x_annotation = asse_x[xmin]+((asse_x[xmax]-asse_x[xmin])/4*3)
    ax2.annotate("RBW: " + str("%3.1f" % RBW) + "KHz", (x_annotation, -15), fontsize=12)
    ax2.grid(True)

    plt.title("Max Hold and Min Hold of " + fname.split("/")[-1][:-11].replace("_", "  "), fontsize=14)

    plt.tight_layout()
    # print fname[:fname.rfind("/")+1]+"PNG/"+fname.split("/")[-1][:-4]+".png"
    if not os.path.isdir(BASE_DIR + "SPECTROGRAM/" + SPG_DIR + "/" + RX_DIR + POL_DIR):
        os.makedirs(BASE_DIR + "SPECTROGRAM/" + SPG_DIR + "/" + RX_DIR + POL_DIR)

    plt.savefig(BASE_DIR + "SPECTROGRAM/" + SPG_DIR + "/" + RX_DIR + POL_DIR + SPG_DIR[13:] + "_" + fname.split("/")[-1][:-11] + ".png")
