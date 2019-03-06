#!/usr/bin/env python

'''

   Phase-0 Correlator Plot of Bridging data saved with tpm_dump.py

'''

__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

from matplotlib import pyplot as plt
import struct, os, easygui, glob
from optparse import OptionParser
import numpy as np

import matplotlib.gridspec as gridspec
import datetime, time
from tqdm import tqdm

BASE_DIR = "/data/data_2/2018-11-LOW-BRIDGING/"
epoch = datetime.datetime(1970, 1, 1)


def toTimestamp(t):
    dt = t - epoch
    return (dt.microseconds + (dt.seconds + dt.days * 86400) * 10**6) / 10**6


def corr(a, b):
    re = (a.real * b.real)+(a.imag * b.imag)
    im = (a.imag * b.real)-(a.real * b.imag)
    return np.complex(re, im)

def corrint(a, b, avg, freq_bin):
    nsamples = 2 ** 17 / avg
    window = np.hanning(nsamples)
    xAB = []
    for i in range(avg):
        bina = np.fft.rfft(a[(i * nsamples):(i * nsamples) + nsamples] * window)[freq_bin]
        binb = np.fft.rfft(b[(i * nsamples):(i * nsamples) + nsamples] * window)[freq_bin]
        xAB += [corr(bina, binb)]
    return np.sum(xAB)


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("--dirA",
                      dest="dirA",
                      default="",
                      help="Directory containing tdd files of Antenna A")

    parser.add_option("--dirB",
                      dest="dirB",
                      default="",
                      help="Directory containing tdd files of Antenna B")

    parser.add_option("--flabel",
                      dest="flabel",
                      default="",
                      help="Label to be attached to the output file name")

    parser.add_option("--freq",
                      dest="freq",
                      default=160, type='float',
                      help="Frequency (MHz) to be correlated (default: 160 MHz)")

    parser.add_option("--resolution",
                      dest="resolution",
                      default=6, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")

    (options, args) = parser.parse_args()

    if options.dirA == "":
        dirA = easygui.diropenbox(title="Choose a directory file for Antenna A", default=BASE_DIR)
        if dirA == None:
            print "\nMissing Directory. Exiting...\n"
            exit(0)
    else:
        dirA = options.dirA
        if not os.path.isdir(dirA):
            print "\nThe given directory does not exist. Exiting...\n"
            exit(0)

    if options.dirB == "":
        dirB = easygui.diropenbox(title="Choose a directory file for Antenna B", default=BASE_DIR)
        if dirB == None:
            print "\nMissing Directory. Exiting...\n"
            exit(0)
    else:
        dirB = options.dirB
        if not os.path.isdir(dirB):
            print "\nThe given directory does not exist. Exiting...\n"
            exit(0)

    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 17)
    rbw = int(closest(resolutions, options.resolution))
    avg = 2 ** rbw
    nsamples = 2 ** 17 / avg
    RBW = (avg * (400000.0 / 65536.0))
    bw = (nsamples / 2) + 1
    asse_x = np.linspace(0, 400, bw)
    freq_bin = closest(asse_x, options.freq)
    print "\nCorrelation Frequency: ", options.freq, "MHZ, Channel #", freq_bin, "at resolution ", RBW, "KHz\n"

    datafilesA = sorted(glob.glob(dirA + "/*.tdd"))
    print " - Found " + str(len(datafilesA)) + " \"tdd\" files in dir:",dirA
    datafilesB = sorted(glob.glob(dirB + "/*.tdd"))
    print " - Found " + str(len(datafilesB)) + " \"tdd\" files in dir:",dirB

    orari = []       # Timestamps
    #power_rfA = []   # RF Power
    #power_rfB = []   # RF Power
    bin_A = []       # Complex values of bin channel to be correlated
    bin_B = []       # Complex values of bin channel to be correlated
    crossAB = []     # Cross Correlation A*B^
    autoA = []       # Auto Correlation A
    autoB = []       # Auto Correlation B

    for cnt in tqdm(range(len(datafilesA))):
        fnameA = datafilesA[cnt]
        fnameB = datafilesB[cnt]
        if fnameA[-21:-4] in fnameB:
            # print fname.split("/")[-1][-21:-4]
            orari += [datetime.datetime.strptime(fnameA.split("/")[-1][-21:-4], "%Y-%m-%d_%H%M%S")]

            with open(fnameA, "r") as f:
                a = f.read()
            l = struct.unpack(">d", a[0:8])[0]
            dataA = struct.unpack(">" + str(int(l)) + "b", a[8:])

            with open(fnameB, "r") as f:
                a = f.read()
            l = struct.unpack(">d", a[0:8])[0]
            dataB = struct.unpack(">" + str(int(l)) + "b", a[8:])

            crossAB += [corrint(dataA, dataB, avg, freq_bin)]
            autoA += [np.real(corrint(dataA, dataA, avg, freq_bin))]
            autoB += [np.real(corrint(dataB, dataB, avg, freq_bin))]

    plt.ioff()

    gs = gridspec.GridSpec(2, 1)
    fig = plt.figure(figsize=(12, 7), facecolor='w')
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    x_tick = []
    step = 0
    for z in range(len(orari)):
        if orari[z].hour == step:
            #print str(orari[z])
            x_tick += [z]
            step = step + 3
    x_tick += [len(crossAB)]

    ax1.plot(10*np.log10(np.abs(crossAB)))
    ax1.plot(10*np.log10(autoA))
    ax1.plot(10*np.log10(autoB))
    ax1.grid(True)
    ax1.set_xlim(0, len(crossAB))
    #ax1.set_ylim(0, 150)
    ax1.set_xticks(x_tick)
    ax1.set_xticklabels(np.array(range(0, 3*9, 3)).astype("str").tolist())
    ax1.set_ylabel("Magnitude")
    ax1.set_xlabel("Time UTC")
    ax1.set_title("AutoCorrelation between: (add description here)", fontsize=14)

    phs = np.angle(crossAB, deg=True)
    ax2.plot(phs, linestyle="None", marker=".")
    #ax2.plot(phs, color='r')
    ax2.grid(True)
    ax2.set_xlim(0, len(crossAB))
    ax2.set_xticks(x_tick)
    ax2.set_yticks(range(-180, 180 + 45, 45))
    ax2.set_xticklabels(np.array(range(0, 3*9, 3)).astype("str").tolist())
    ax2.set_ylabel("Phase (deg)")
    ax2.set_xlabel("Time UTC")
    ax2.set_title("Phase computed Cross Correlating signals - "+datetime.datetime.strftime(orari[0], "%Y-%m-%d ")+" ", fontsize=14)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    #plt.show()
    if not os.path.isdir(BASE_DIR + "CORR"):
        os.makedirs(BASE_DIR + "CORR")
    if not os.path.isdir(BASE_DIR + "CORR/IMG"):
        os.makedirs(BASE_DIR + "CORR/IMG")
    if not os.path.isdir(BASE_DIR + "CORR/DATA"):
        os.makedirs(BASE_DIR + "CORR/DATA")

    outdir = BASE_DIR + "CORR/"
    foutname = datetime.datetime.strftime(orari[0], "%Y-%m-%d") + options.flabel + "_Freq-%6.3fMHz"%(options.freq)

    plt.savefig(outdir + "IMG/" + foutname + ".png")
    print "\nSaved File: " + outdir + "IMG/" + foutname + ".png"

    with open(outdir + "DATA/" + foutname + ".txt", "w") as f:
        for i in range(len(crossAB)):
            timestamp = toTimestamp(orari[i])
            f.write(str(timestamp) + "\t" + "%6.3f"%(phs[i]) + "\n")
    print "Saved File: " + outdir + "DATA/" + foutname + ".txt\n"


