#!/usr/bin/env python

'''

  Low Bridging Phase 0 Logger.

  Regenerate pictures for movie

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import easygui, os

from optparse import OptionParser

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Other stuff
import numpy as np
import struct
import datetime
import glob
from tqdm import tqdm

# Some globals
OUT_PATH = "/data/data_2/2018-11-LOW-BRIDGING/"
DATA_PATH = "DATA/"
POWER_DIR = "POWER/"
TRIGGER_DIR = "TRIGGER/"

PHASE_0_MAP = [[0, "EDA-2"], [1, "SKALA-4.0"], [4, "SKALA-2"], [5, "SKALA-4.1"]]


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


if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("-d", "--dir",
                      dest="dir",
                      default="",
                      help="Directory to be processed")

    parser.add_option("--resolution",
                      dest="resolution",
                      default=780, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")

    (options, args) = parser.parse_args()

    plt.ioff()

    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 17)
    rbw = int(closest(resolutions, options.resolution))
    avg = 2 ** rbw
    RBW = (avg * (400000.0 / 65536.0))

    nsamples = 2 ** 17 / avg

    print "\n######################################################"
    print "\n\n - Regenerate TPM Data Logger Pictures\n"

    if not options.dir == "":
        datapath = options.dir
    else:
        datapath = easygui.diropenbox(title="Choose a Directory", default=OUT_PATH)

    if not datapath[-1] == "/":
        datapath += "/"

    if not os.path.exists(datapath+DATA_PATH):
        print "Inalid directory, missing DATA folder! \n"
        exit(0)

    Rxs = sorted(os.listdir(datapath+DATA_PATH))
    datafiles = sorted(glob.glob(datapath+DATA_PATH+Rxs[0]+"/Pol-X/*.tdd"))
    if not len(datafiles)>0:
        print "\nNo measurements found in "+datapath+DATA_PATH+"/Pol-X\n"
        exit(0)
    else:

        # Creating Directory to store pictures
        print "Generating directory tree..."
        if not os.path.exists(datapath + "IMG"):
            os.makedirs(datapath + "IMG")
        if not os.path.exists(datapath + "IMG/PLOT-A"):
            os.makedirs(datapath + "IMG/PLOT-A")

        gs = gridspec.GridSpec(int(np.ceil(np.sqrt(len(Rxs)))), int(np.ceil(np.sqrt(len(Rxs)))))#, hspace=0.1, wspace=0.2)
        fig = plt.figure(figsize=(12, 7), facecolor='w')
        #fig, axes = plt.subplots(nrows=int(np.ceil(np.sqrt(len(Rxs)))), ncols=int(np.ceil(np.sqrt(len(Rxs)))), figsize=(12, 7), facecolor='w')
        axes = []
        for i in range(len(Rxs)):
            axes += [fig.add_subplot(gs[i])]
        #axes = axes.reshape(1,len(Rxs))[0]

        for x in axes:
            x.set_xlim(0, 400)
            x.set_ylim(-80, 0)
            x.set_xlabel('MHz ')
            x.set_ylabel("dBm ")
            x.grid(True)
            x.plot(np.linspace(0, 400, (nsamples/2)+1), np.linspace(0, 400, (nsamples/2)+1))
        titolo = "FAKE FIGURE TO FIX MATPLOTLIB - UTC   (RBW: " + "%3.1f" % rbw + " KHz)"
        fig.suptitle(titolo, fontsize=16)
        #plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(datapath + "IMG/PLOT-A/LB_PHASE-0_A.png")
        os.system("rm "+datapath + "IMG/PLOT-A/LB_PHASE-0_A.png")

    asse_x = np.linspace(0, 400, (nsamples/2)+1)
    TPM = datafiles[0].split("/")[-1][:7]
    for z in tqdm(range(len(datafiles))):
        skip = False

        timestamp = datafiles[z][-21:-4]
        try:
            tstamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d_%H%M%S")
        except:
            #print "Got: ", timestamp, ", trying with:", datafiles[z][-24:-4]+"000"
            try:
                timestamp = datafiles[z][-24:-4]
                tstamp = datetime.datetime.strptime(timestamp+"000", "%Y-%m-%d_%H%M%S%f")
            except:
                print "Bad time format:", timestamp
                skip = True

        if not skip:
            for n, rx in enumerate(Rxs):
                axes[n].cla()
                for pol, col, rf in [("Pol-X", 'b', -9), ("Pol-Y", 'g', -16)]:
                    fname = datapath + DATA_PATH + rx + "/" + pol + "/" + TPM
                    fname += rx + "_" + pol + "_" + timestamp + ".tdd"

                    try:
                        with open(fname, "r") as f:
                            a = f.read()
                        l = struct.unpack(">d", a[0:8])[0]
                        data = struct.unpack(">" + str(int(l)) + "b", a[8:])
                        spettro = calcolaspettro(data, nsamples)
                        #print len(spettro), len(asse_x)

                        adu_rms = np.sqrt(np.mean(np.power(data, 2), 0))
                        volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
                        power_adc = 10 * np.log10(
                            np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
                        power_rf = power_adc + 12  # single ended to diff net loose 12 dBm

                        axes[n].plot(asse_x[1:], spettro[1:], color=col)
                        axes[n].annotate("RF Power:  " + "%3.1f" % (power_rf) + " dBm",
                                            (228, rf), fontsize=14, color=col)
                    except:
                       skip = True

                if not skip:
                    axes[n].set_xlim(0, 400)
                    axes[n].set_ylim(-80, 0)
                    axes[n].set_xlabel('MHz ')
                    axes[n].set_ylabel("dBm ")
                    axes[n].set_title(" " + PHASE_0_MAP[n][1] + " ", fontsize=15)
                    axes[n].grid(True)

        if not skip:
            titolo = timestamp.replace("_", " ")[:13]+":"+timestamp.split("_")[1][2:4]+":"+timestamp.split("_")[1][4:6] + " UTC   (RBW: " + "%3.1f" % rbw + " KHz)"
            fig.suptitle(titolo, fontsize=16)
            #plt.tight_layout()
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.savefig(datapath + "IMG/PLOT-A/LB_PHASE-0_A_" + timestamp + ".png")

