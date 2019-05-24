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

    parser.add_option("--multiplot", action="store_true",
                      dest="multiplot",
                      default=False,
                      help="Plot all the RX files in a grid multiplots")

    parser.add_option("--resolution",
                      dest="resolution",
                      default=1000, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")

    parser.add_option("--antennas",
                      dest="antennas",
                      default="",
                      help="Comma separated antenna list")

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
    if not os.path.isdir(video_dir):
        os.mkdir(video_dir)
    video_dir += "/" + options.date
    if not os.path.isdir(video_dir):
        os.mkdir(video_dir)
    video_dir += "/" + options.station
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

    if options.antennas == "":
        print "\nMissing input: Antenna list"
        exit(0)

    antenne = []
    for a in options.antennas.split(","):
        antenne += ["ANT-%03d"%(int(a))]

    img_dir = base_dir[:-4] + "CHECK"
    if not os.path.isdir(img_dir):
        os.mkdir(img_dir)
    if not os.path.isdir(img_dir + "/" + options.antennas.replace(",", "_")):
        os.mkdir(img_dir + "/" + options.antennas.replace(",", "_"))

    tiles_dir = sorted(glob.glob(base_dir + "/TILE*"))
    ant_dir = []
    for t in tiles_dir:
        for x in sorted(glob.glob(t+"/ANT*")):
            if x[-7:] in antenne:
                ant_dir += [x]

    print "\nFound", len(ant_dir), "Antenna Directories"
    if len(ant_dir) == 0:
        print "ERROR: Missing antenna data"
        exit(0)

    obs = sorted(glob.glob(ant_dir[0] + "/POL-X/*raw"))
    for i in range(len(obs)):
        obs[i] = obs[i][-28:-4]
    print "Found", len(obs), "observation files\n"

    keys, cells = read_from_local(options.station)
    ant_pos = [(float(x["East"]), float(x["North"])) for x in cells if x["Deployed"] == "ON"]
    ant_pos_check = [(float(x["East"]), float(x["North"])) for x in cells if x["Deployed"] == "ON" and "ANT-%03d"%(int(x["Antenna"])) in antenne]
    print ant_pos_check
    exit(0)

    plt.ioff()
    gs = gridspec.GridSpec(5, 4)
    gs2 = gridspec.GridSpec(5, 8)
    fig = plt.figure(figsize=(16, 9), facecolor='w')
    fig2 = plt.figure(figsize=(16, 9), facecolor='w')

    ax = []
    for i in range(16):
        ax += [fig.add_subplot(gs[i+4])]
        ant_list[i] = ant_list[i][-7:]
    title_left = fig.add_subplot(gs[0])
    title_center = fig.add_subplot(gs[1:2])
    gs3 = gridspec.GridSpecFromSubplotSpec(1, 2, wspace=0.05, hspace=0.5, subplot_spec=gs[0, 3])
    title_right = fig.add_subplot(gs3[1])

    title_left2 = fig2.add_subplot(gs2[0, 0:1])
    title_center2 = fig2.add_subplot(gs2[0, 2:6])
    title_right2 = fig2.add_subplot(gs2[0, 7])

    ax2 = fig2.add_subplot(gs2[1:5, :])


    # Patching matplotlib tight figures
    pol = "POL-X"
    ant = ant_list[0]
    x = 0

    fname = tile_dir + "/" + ant_list[0] + "/POL-X/" + tile + "_" + ant_list[0] + "_POL-X_" + obs[0] + ".raw"
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
    ax[i].plot(asse_x, np.array(spettro).astype("float"))
    ax[i].set_xlim(0, 400)
    ax[i].set_xticks([50, 100, 150, 200, 250, 300, 350, 400])
    ax[i].set_xticklabels([50, 100, 150, 200, 250, 300, 350, 400], fontsize=8)#, rotation=45)
    ax[i].set_xlabel("MHz", fontsize=10)

    ax[i].set_ylim(-80, 0)
    ax[i].set_yticks([0, -20, -40, -60, -80])
    ax[i].set_yticklabels([0, -20, -40, -60, -80], fontsize=8)
    ax[i].set_ylabel("dB", fontsize=10)

    ax[i].set_title(ant, fontsize=12)
    ax[i].grid(True)
    ax[i].annotate("RF Power:  " + "%3.1f"%(power_rf) + " dBm", (160, -19), fontsize=9, color='b')

    titolo = "  ".join(obs[x][:-7].split("_")) + " UTC   (RBW: " + "%3.1f" % RBW + " KHz)"
    #fig.suptitle(titolo, fontsize=14)
    fig.tight_layout()
    #plt.tight_layout()
    fig.canvas.draw()
    time.sleep(1)
    plt.savefig(img_dir + "/" + tile + "/" + pol + "/MULTI/" + tile + "_" + pol + "_" + obs[x] + ".png")


    for pol in ["POL-X", "POL-Y"]:
        print "\nGenerating pictures for", pol

        for x in tqdm(range(len(obs)), desc=pol):
            cnt = 0
            spettri = []
            legends = []
            for i, ant in enumerate(ant_list):
                try:
                    fname = tile_dir + "/" + ant + "/" + pol + "/" + tile + "_" + ant + "_" + pol + "_" + obs[x] + ".raw"
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

                    ax[i].cla()
                    ax[i].plot(asse_x[3:-3], np.array(spettro).astype("float")[3:-3])
                    ax[i].set_xlim(0, 400)
                    ax[i].set_xticks([50, 100, 150, 200, 250, 300, 350, 400])
                    ax[i].set_xticklabels([50, 100, 150, 200, 250, 300, 350, 400], fontsize=8)#, rotation=45)
                    if i >= 12:
                        ax[i].set_xlabel("MHz", fontsize=10)

                    ax[i].set_ylim(-80, 0)
                    ax[i].set_yticks([0, -20, -40, -60, -80])
                    ax[i].set_yticklabels([0, -20, -40, -60, -80], fontsize=8)
                    if i % 4 == 0:
                        ax[i].set_ylabel("dB", fontsize=10)

                    ax[i].set_title(ant, fontsize=12)
                    ax[i].grid(True)
                    ax[i].annotate("RF Power:  " + "%3.1f"%(power_rf) + " dBm", (160, -19), fontsize=9, color='b')

                    # fig.suptitle(titolo, fontsize=14)
                    # plt.tight_layout(rect=[0, 0.03, 1, 0.95])
                    cnt = cnt + 1

                except:
                    print "Something went wrong!"
                    pass

            if cnt == 16:
                title_left.cla()
                title_left.set_axis_off()
                title_left.plot([0.001, 0.002], color='w')
                title_left.set_xlim(-20, 20)
                title_left.set_ylim(-20, 20)
                title_left.annotate(options.station, (-15, 8), fontsize=32, color='blue')
                title_left.annotate(tile, (-5, -10), fontsize=28, color='green')

                title_center.cla()
                title_center.set_axis_off()
                title_center.plot([0.001, 0.002], color='w')
                title_center.set_xlim(-20, 20)
                title_center.set_ylim(-20, 20)
                titolo = "  ".join(obs[x][:-7-4].split("_")) + ":" + obs[x][-7-4:-7-2] + ":" + obs[x][-7-2:-7] + "  UTC"
                subtitolo = "(RBW: " + "%3.1f" % RBW + " KHz)"
                title_center.annotate(titolo, (-2, 5), fontsize=20, color='black')
                title_center.annotate(pol, (18, -8), fontsize=16, color='red')

                title_right.cla()
                title_right.set_axis_off()
                title_right.plot([0.001, 0.002], color='w')
                title_right.set_xlim(-25.5, 25.5)
                title_right.set_ylim(-25.5, 25.5)
                circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
                title_right.add_artist(circle1)
                for c in ant_pos:
                    title_right.plot(c[0], c[1], marker='+', markersize=4,
                        linestyle='None', color='k')
                title_right.annotate("E", (21, -1), fontsize=10, color='black')
                title_right.annotate("W", (-25.1, -1), fontsize=10, color='black')
                title_right.annotate("N", (-1, 21), fontsize=10, color='black')
                title_right.annotate("S", (-1, -24.6), fontsize=10, color='black')

                fig.tight_layout()#rect=[0, 0.03, 1, 0.95])
                fig.canvas.draw()
                # time.sleep(1)
                fig.savefig(img_dir + "/" + tile + "/" + pol + "/MULTI/" + tile + "_" + pol + "_" + obs[x] + ".png")

                title_left2.cla()
                title_left2.set_axis_off()
                title_left2.plot([0.001, 0.002], color='w')
                title_left2.set_xlim(-20, 20)
                title_left2.set_ylim(-20, 20)
                title_left2.annotate(options.station, (-15, 8), fontsize=32, color='blue')
                title_left2.annotate(tile, (10, -8), fontsize=28, color='green')

                title_center2.cla()
                title_center2.set_axis_off()
                title_center2.plot([0.001, 0.002], color='w')
                title_center2.set_xlim(-20, 20)
                title_center2.set_ylim(-20, 20)
                title_center2.annotate(titolo, (-11, 3), fontsize=22, color='black')
                title_center2.annotate(pol, (-2, -13), fontsize=16, color='red')

                title_right2.cla()
                title_right2.set_axis_off()
                title_right2.plot([0.001, 0.002], color='wheat')
                title_right2.set_xlim(-25.5, 25.5)
                title_right2.set_ylim(-25.5, 25.5)
                circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
                title_right2.add_artist(circle1)
                for c in ant_pos:
                    title_right2.plot(c[0], c[1], marker='+', markersize=4,
                        linestyle='None', color='k')
                title_right2.annotate("E", (21, -1), fontsize=10, color='black')
                title_right2.annotate("W", (-25.1, -1), fontsize=10, color='black')
                title_right2.annotate("N", (-1, 21), fontsize=10, color='black')
                title_right2.annotate("S", (-1, -24.6), fontsize=10, color='black')

                ax2.cla()
                for l, sp in enumerate(spettri):
                    ax2.plot(asse_x[3:-3], sp[3:-3], label=legends[l])
                    ax2.set_ylim(-80, 0)
                    ax2.set_ylabel("dB", fontsize=16)
                    ax2.set_xlim(0, 400)
                    ax2.set_xlabel("MHz", fontsize=16)
                    ax2.grid(True)
                    ax2.legend(loc=8, ncol=8, borderaxespad=0.5, fontsize=12)#, borderaxespad=0., fontsize='small')
                fig2.tight_layout()#rect=[0, 0.03, 1, 0.9])
                fig2.canvas.draw()
                fig2.savefig(img_dir + "/" + tile + "/" + pol + "/SINGLE/" + tile + "_" + pol + "_" + obs[x] + "_all.png")

    for pol in ["POL-X", "POL-Y"]:
        for mode in ["MULTI", "SINGLE"]:
            os.system("ffmpeg -y -f image2 -i " + img_dir + "/" + tile + "/" + pol + "/" + mode + "/" + tile + "_" +
                      pol + "_" + options.date + "_%*.png  -vcodec libx264 " + video_dir + "/" + tile + "_" +
                      pol + "_" + options.date + "_" + mode + ".avi")

