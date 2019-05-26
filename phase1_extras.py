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
import os, easygui, glob, struct, time
from optparse import OptionParser
import numpy as np

import matplotlib.gridspec as gridspec
from tqdm import tqdm
from tpm_save import read_from_local

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
    asse_x = np.linspace(0, 400, (nsamples/2)+1)
    RBW = (avg * (400000.0 / 65536.0))


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

    # Example of video dir structure
    # /base_dir/VIDEO/2019-05-15/SKALA-4
    video_dir = base_dir + "/VIDEO"
    img_dir = base_dir + "/EXTRA"
    if not os.path.isdir(video_dir):
        os.mkdir(video_dir)
    video_dir += "/EXTRA"
    if not os.path.isdir(video_dir):
        os.mkdir(video_dir)

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
        os.mkdir(img_dir + "/" + tile + "/POL-X/MULTI")
        os.mkdir(img_dir + "/" + tile + "/POL-X/SINGLE")
    if not os.path.isdir(img_dir + "/" + tile + "/POL-Y"):
        os.mkdir(img_dir + "/" + tile + "/POL-Y")
        os.mkdir(img_dir + "/" + tile + "/POL-Y/MULTI")
        os.mkdir(img_dir + "/" + tile + "/POL-Y/SINGLE")

    if not os.path.isdir(img_dir):
        os.mkdir(img_dir)
    img_dir = img_dir + "/" + options.date
    if not os.path.isdir(img_dir):
        os.mkdir(img_dir)
    img_dir = img_dir + "/" + tile
    if not os.path.isdir(img_dir):
        os.mkdir(img_dir)

    ant_list = sorted(glob.glob(tile_dir + "/ANT*"))
    print "\nFound", len(ant_list), "Antenna Directories"
    if len(ant_list) == 0:
        print "ERROR: Missing antenna data"
        exit(0)
    #print ant_list[0] + "/POL-X/*raw"
    obs = sorted(glob.glob(ant_list[0] + "/POL-X/*raw"))
    for i in range(len(obs)):
        obs[i] = obs[i][-28:-4]
    print "Found", len(obs), "observation files\n"

    keys, cells = read_from_local(options.station)
    ant_pos = [(float(x["East"]), float(x["North"])) for x in cells if x["Tile"] == options.tile]

    plt.ioff()
    gs = gridspec.GridSpec(5, 3)
    fig = plt.figure(figsize=(16, 9), facecolor='w')

    # ax = []
    # for i in range(16):
    #     ant_list[i] = ant_list[i][-7:]
    ax_title = fig.add_subplot(gs[0, 0])
    ax_geo_map = fig.add_subplot(gs[1:2, 0])
    ax_total_power = fig.add_subplot(gs[3:4, 0])

    ax_airplane = []
    ax_airplane += [fig.add_subplot(gs[0, 1])]
    ax_airplane += [fig.add_subplot(gs[0, 2])]

    ax_orbcomm = []
    ax_orbcomm += [fig.add_subplot(gs[1, 1])]
    ax_orbcomm += [fig.add_subplot(gs[1, 2])]

    ax_rms = []
    ax_rms += [fig.add_subplot(gs[2, 1])]
    ax_rms += [fig.add_subplot(gs[2, 2])]

    ax_spectra = []
    ax_spectra += [fig.add_subplot(gs[3:4, 1])]
    ax_spectra += [fig.add_subplot(gs[3:4, 2])]

    for x in tqdm(range(len(obs))):
        cnt = 0
        spettri = []
        legends = []
        try:
            for i, (pol, col) in enumerate([("POL-X", "b"), ("POL-Y", "g")]):
                ax_spectra[i].cla()
                for z, ant in enumerate(ant_list):
                    fname = tile_dir + "/" + ant + "/" + pol + "/" + tile + "_" + ant + "_" + pol + "_" + obs[x] + ".raw"
                    print fname
                    with open(fname, "r") as f:
                        a = f.read()
                    data = struct.unpack(">" + str(len(a)) + "b", a)
                    spettro = calcolaspettro(data, nsamples)
                    spettri += [spettro]
                    legends += [ant]

                    adu_rms = np.sqrt(np.mean(np.power(data, 2), 0))
                    volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
                    power_adc = 10 * np.log10(
                        np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
                    power_rf = power_adc + 12  # single ended to diff net loose 12 dBm

                    ax_spectra[i].plot(asse_x[3:-3], np.array(spettro).astype("float")[3:-3])
                    ax_spectra[i].set_xlim(0, 400)
                    ax_spectra[i].set_xticks([50, 100, 150, 200, 250, 300, 350, 400])
                    ax_spectra[i].set_xticklabels([50, 100, 150, 200, 250, 300, 350, 400], fontsize=8)#, rotation=45)
                    ax_spectra[i].set_xlabel("MHz", fontsize=10)

                    ax_spectra[i].set_ylim(-80, 0)
                    ax_spectra[i].set_yticks([0, -20, -40, -60, -80])
                    ax_spectra[i].set_yticklabels([0, -20, -40, -60, -80], fontsize=8)
                    ax_spectra[i].set_ylabel("dB", fontsize=10)

                    ax_spectra[i].set_title(ant, fontsize=12)
                    ax_spectra[i].grid(True)
                    #ax_spectra[i].annotate("RF Power:  " + "%3.1f"%(power_rf) + " dBm", (160, -19), fontsize=9, color='b')

                    # fig.suptitle(titolo, fontsize=14)
                    # plt.tight_layout(rect=[0, 0.03, 1, 0.95])
                    cnt = cnt + 1

        except:
            print "Something went wrong!"
            pass

        if cnt == 32:
            ax_title.cla()
            ax_title.set_axis_off()
            ax_title.plot([0.001, 0.002], color='w')
            ax_title.set_xlim(-20, 20)
            ax_title.set_ylim(-20, 20)
            ax_title.annotate(options.station, (-15, 8), fontsize=32, color='blue')
            ax_title.annotate(tile, (-5, -10), fontsize=28, color='green')
            titolo = "  ".join(obs[x][:-7-4].split("_")) + ":" + obs[x][-7-4:-7-2] + ":" + obs[x][-7-2:-7] + "  UTC"
            ax_title.annotate(titolo, (-2, -18), fontsize=10, color='black')

            ax_geo_map.cla()
            ax_geo_map.set_axis_off()
            ax_geo_map.plot([0.001, 0.002], color='w')
            ax_geo_map.set_xlim(-25.5, 25.5)
            ax_geo_map.set_ylim(-25.5, 25.5)
            circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
            ax_geo_map.add_artist(circle1)
            for c in ant_pos:
                ax_geo_map.plot(c[0], c[1], marker='+', markersize=4,
                    linestyle='None', color='k')
            ax_geo_map.annotate("E", (21, -1), fontsize=10, color='black')
            ax_geo_map.annotate("W", (-25.1, -1), fontsize=10, color='black')
            ax_geo_map.annotate("N", (-1, 21), fontsize=10, color='black')
            ax_geo_map.annotate("S", (-1, -24.6), fontsize=10, color='black')

            fig.tight_layout()#rect=[0, 0.03, 1, 0.95])
            fig.canvas.draw()
            # time.sleep(1)
            fig.savefig(img_dir + "/" + tile + "_" + obs[x] + ".png")

