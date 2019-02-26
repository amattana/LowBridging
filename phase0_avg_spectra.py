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
    mediato[:] /= (2 ** 17 / nsamples)
    return mediato


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))



if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("--dir",
                      dest="dir",
                      default="",
                      help="Directory containing tdd files")

    parser.add_option("--savetxt", action="store_true",
                      dest="savetxt",
                      default=False,
                      help="Save the Spectrum ")

    parser.add_option("--resolution",
                      dest="resolution",
                      default=400, type="int",
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
        if fname is not None:
            datapath = fname[:fname.rfind("/")]
            print "\nListing directory:", datapath
            datafiles = sorted(glob.glob(datapath + "/*.tdd"))
            print "Found " + str(len(datafiles)) + " \"tdd\" files.\n"
        else:
            print "\nExiting!\n"
            exit(0)

    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 17)
    rbw = int(closest(resolutions, options.resolution))
    avg = 2 ** rbw
    nsamples = 2 ** 17 / avg
    RBW = (avg * (400000.0 / 65536.0))

    if len(datafiles)>0:
        spettri = np.zeros((nsamples/2)+1)
        for ff in datafiles:
            with open(ff, "r") as f:
                a = f.read()
            l = struct.unpack(">d", a[0:8])[0]
            data = struct.unpack(">" + str(int(l)) + "b", a[8:])
            singolo = calcolaspettro(data, nsamples)
            spettri += singolo
        spettri /= len(datafiles)

        with np.errstate(divide='ignore', invalid='ignore'):
            spettro = 20 * np.log10(spettri / 127)

        gs = gridspec.GridSpec(1, 1)
        fig = plt.figure(figsize=(10, 7), facecolor='w')
        ax2 = fig.add_subplot(gs[0])

        asse_x = np.linspace(0, 400, len(spettro))
        ax2.plot(asse_x[3:], spettro[3:])
        ax2.set_xlim(0, 400)
        ax2.set_ylim(-100, 0)
        ax2.set_xlabel('MHz')
        ax2.set_ylabel("dBm")
        ax2.set_title("Power Spectrum", fontsize=14)
        ax2.annotate("Averaged Spectra: " + str(len(datafiles)), (280, -15), fontsize=16)
        ax2.annotate("RBW: " + str("%3.1f" % RBW) + "KHz", (280, -20), fontsize=16)
        ax2.grid(True)

        plt.tight_layout()

        plt.show()

        if options.savetxt:
            with open(fname[:-4]+"_RBW-"+str("%03d" % int(RBW))+"KHz.txt", "w") as f:
                for i in range(len(singolo)):
                    f.write(str("%9.6f\t%5.2f\n"%(asse_x[i], spettro[i])))
            print "\nWritten file: " + fname[:-4]+"_RBW-"+str("%03d" % int(RBW))+"KHz.txt\n"
    else:
        print "Not enough tdd file to compute an averaged spectrum!\n"

