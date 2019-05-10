#!/usr/bin/env python

'''

   Phase-0 Generation of Pictures and Movie
   of Bridging data saved with tpm_dump.py

   Input: /data/data_2/2018-11-LOW-BRIDGING/ + DATE directory
   Output: /data/data_2/2018-11-LOW-BRIDGING/DATE/VIDEO will contain the movies
   Output: /data/data_2/2018-11-LOW-BRIDGING/DATE/IMG will contain the picture frames of the movie

'''

__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

from matplotlib import pyplot as plt
import os, easygui, glob, struct
from optparse import OptionParser
import numpy as np

import matplotlib.gridspec as gridspec
from tqdm import tqdm

BASE_DIR = "/data/data_2/2019-LOW-BRIDGING-PHASE1/"


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

    parser.add_option("--dir",
                      dest="dir",
                      default="",
                      help="Directory containing raw files")

    parser.add_option("--date",
                      dest="date",
                      default="",
                      help="Date to be processed")

    parser.add_option("--station",
                      dest="station",
                      default="SKALA-4",
                      help="The station type (def: SKALA-4, alternatives: EDA-2)")

    parser.add_option("--tile",
                      dest="tile",
                      default=0,
                      help="The number of the tile")

    parser.add_option("--skipreadfile", action="store_true",
                      dest="skipreadfile",
                      default=False,
                      help="Use the files already saved")

    parser.add_option("--multiplot", action="store_true",
                      dest="multiplot",
                      default=False,
                      help="Plot all the RX files in a grid multiplots")

    parser.add_option("--resolution",
                      dest="resolution",
                      default=1000, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")

    (options, args) = parser.parse_args()

    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 17)
    rbw = int(closest(resolutions, options.resolution))
    avg = 2 ** rbw
    nsamples = 2 ** 17 / avg

    if options.dir == "":
        base_dir = easygui.diropenbox(title="Choose a directory file", default=BASE_DIR)
        if base_dir is None:
            print "\nMissing Directory. Exiting...\n"
            exit(0)
    else:
        base_dir = options.dir
        if not os.path.isdir(base_dir):
            print "\nThe given directory does not exist. Exiting...\n"
            exit(0)

    base_dir += "/" + options.date
    if not os.path.isdir(base_dir):
        print "ERROR: WRONG DATE", base_dir, "\nThe given directory does not exist. Exiting...\n"
        exit(0)

    base_dir += "/" + options.station + "/DATA"
    if not os.path.isdir(base_dir):
        print "ERROR: MISSING DATA FOLDER", base_dir, "\nThe given directory does not exist. Exiting...\n"
        exit(0)

    tile = "TILE-" + "%02d"%(int(options.tile))
    tile_dir = base_dir + "/" + tile
    if not os.path.isdir(tile_dir):
        print "ERROR: TILE NUMBER ", tile_dir, "\nThe given directory does not exist. Exiting...\n"
        exit(0)

    img_dir = base_dir[:-4] + "IMG"
    if not os.path.isdir(img_dir):
        os.mkdir(img_dir)
    if not os.path.isdir(img_dir + "/" + tile):
        os.mkdir(img_dir + "/" + tile)
    if not os.path.isdir(img_dir + "/" + tile + "/POL-X"):
        os.mkdir(img_dir + "/" + tile + "/POL-X")
    if not os.path.isdir(img_dir + "/" + tile + "/POL-Y"):
        os.mkdir(img_dir + "/" + tile + "/POL-Y")

    ant_list = sorted(glob.glob(tile_dir + "/ANT*"))
    print "\nFound", len(ant_list), "Antenna Directories"
    if len(ant_list) == 0:
        print "ERROR: Missing antenna data"
        exit(0)
    #print ant_list[0] + "/POL-X/*raw"
    obs = sorted(glob.glob(ant_list[0] + "/POL-X/*raw"))
    for i in range(len(obs)):
        obs[i] = obs[i][22:-4]
    print "Found", len(obs), "observation files\n"

    plt.ioff()
    gs = gridspec.GridSpec(4, 4)
    fig = plt.figure(figsize=(12, 7), facecolor='w')
    ax = []
    for i in range(16):
        ax += [fig.add_subplot(gs[i])]
        ant_list[i] = ant_list[i][-7:]

    for pol in ["POL-X", "POL-Y"]:
        print "\nGenerating pictures for", pol

        for x in tqdm(range(len(obs)), desc=pol):
            cnt = 0
            for i, ant in enumerate(ant_list):
                try:
                    fname = tile_dir + "/" + ant + "/" + pol + "/" + tile + "_" + ant + "_" + pol + "_" + obs[x] + ".raw"

                    with open(fname, "r") as f:
                        a = f.read()
                    data = struct.unpack(">" + str(len(a)) + "b", a)
                    spettro = calcolaspettro(data, nsamples)

                    adu_rms = np.sqrt(np.mean(np.power(data, 2), 0))
                    volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
                    power_adc = 10 * np.log10(
                        np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
                    power_rf = power_adc + 12  # single ended to diff net loose 12 dBm

                    ax[i].cla()
                    ax[i].plot(x, np.array(spettro).astype("float"))
                    ax[i].set_xlim(0, 400)
                    ax[i].set_ylim(-80, 0)
                    ax[i].set_xlabel('MHz')
                    ax[i].set_ylabel("dB")
                    ax[i].set_title(ant, fontsize=20)
                    ax[i].grid(True)
                    ax[i].annotate("RF Power:  " + "%3.1f"%(power_rf) + " dBm", (280, -15), fontsize=10, color='b')
                    cnt = cnt + 1
                except:
                    pass
            #if cnt == 16:
            print obs[x]
            print img_dir + "/" + tile + "/" + pol + "/" + tile + "_" + pol + "_" + obs[x] + ".png"
            titolo = "  ".join(obs[x].split("_")) + " UTC   (RBW: " + "%3.1f" % rbw + " KHz)"
            fig.suptitle(titolo, fontsize=16)
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.savefig(img_dir + "/" + tile + "/" + pol + "/" + tile + "_" + pol + "_" + obs[x] + ".png")



