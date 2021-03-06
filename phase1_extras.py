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

    if not base_dir[-1] == "/":
        base_dir += "/"
    base_dir += options.date
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
    img_dir += "/EXTRA"
    if not os.path.isdir(img_dir):
        os.mkdir(img_dir)
    img_dir += "/" + tile
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
    x_tick = []
    step = 0
    for z in range(len(obs)):
        if int(obs[z][11:13]) == step:
            #print str(orari[z])
            x_tick += [z]
            step = step + 3
    x_tick += [len(obs)]

    keys, cells = read_from_local(options.station)
    ant_pos = [(float(x["East"]), float(x["North"])) for x in cells if x["Tile"] == options.tile]

    plt.ioff()
    gs = gridspec.GridSpec(5, 3)
    fig = plt.figure(figsize=(16, 9), facecolor='w')

    # ax = []
    for i in range(16):
        ant_list[i] = ant_list[i][-7:]
    ax_title = fig.add_subplot(gs[0, 0])
    ax_geo_map = fig.add_subplot(gs[1:3, 0])

    potenza_rf = []
    ax_total_power = fig.add_subplot(gs[3:5, 0])

    potenza_airplane = []
    ax_airplane = []
    ax_airplane += [fig.add_subplot(gs[0, 1])]
    ax_airplane += [fig.add_subplot(gs[0, 2])]

    potenza_orbcomm = []
    ax_orbcomm = []
    ax_orbcomm += [fig.add_subplot(gs[1, 1])]
    ax_orbcomm += [fig.add_subplot(gs[1, 2])]

    ax_rms = []
    ax_rms += [fig.add_subplot(gs[2, 1])]
    ax_rms += [fig.add_subplot(gs[2, 2])]
    ind = np.arange(16)

    ax_spectra = []
    ax_spectra += [fig.add_subplot(gs[3:5, 1])]
    ax_spectra += [fig.add_subplot(gs[3:5, 2])]

    obs = [obs[0]] + obs
    for x in tqdm(range(len(obs))):
        cnt = 0
        spettri = []
        legends = []
        prf = []
        porbcomm = []
        pairplane = []
        try:
            for i, (pol, col) in enumerate([("POL-X", "b"), ("POL-Y", "g")]):
                ax_spectra[i].cla()
                rms = []
                for z, ant in enumerate(ant_list):
                    fname = tile_dir + "/" + ant + "/" + pol + "/" + tile + "_" + ant + "_" + pol + "_" + obs[x] + ".raw"
                    with open(fname, "r") as f:
                        a = f.read()
                    data = struct.unpack(">" + str(len(a)) + "b", a)
                    spettro = calcolaspettro(data, nsamples)
                    spettri += [spettro]
                    legends += [ant]

                    adu_rms = np.sqrt(np.mean(np.power(data, 2), 0))
                    rms += [adu_rms]
                    volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
                    power_adc = 10 * np.log10(
                        np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
                    power_rf = power_adc + 12  # single ended to diff net loose 12 dBm
                    prf += [power_rf]

                    ax_spectra[i].plot(asse_x[3:-3], np.array(spettro).astype("float")[3:-3])
                    ax_spectra[i].grid(True)

                    centro = closest(asse_x, 138)
                    integra = linear2dBm(np.sum(dBm2Linear(spettro[centro - 10:centro + 10])))
                    porbcomm.append(integra)

                    centro = closest(asse_x, 125)
                    integra = linear2dBm(np.sum(dBm2Linear(spettro[centro - 10:centro + 10])))
                    pairplane.append(integra)

                    cnt = cnt + 1
                ax_spectra[i].set_xlim(0, 400)
                ax_spectra[i].set_xticks([50, 100, 150, 200, 250, 300, 350, 400])
                ax_spectra[i].set_xticklabels([50, 100, 150, 200, 250, 300, 350, 400], fontsize=8)#, rotation=45)
                ax_spectra[i].set_xlabel("MHz", fontsize=10)

                ax_spectra[i].set_ylim(-80, 0)
                ax_spectra[i].set_yticks([0, -20, -40, -60, -80])
                ax_spectra[i].set_yticklabels([0, -20, -40, -60, -80], fontsize=8)
                ax_spectra[i].set_ylabel("dB", fontsize=10)
                ax_spectra[i].set_title(pol + " Spectra", fontsize=12)

                ax_rms[i].cla()
                ax_rms[i].tick_params(axis='both', which='both', labelsize=6)
                ax_rms[i].set_xticks(xrange(1,17))
                ax_rms[i].set_xticklabels(np.array(range(1,17)).astype("str").tolist(), fontsize=4)
                ax_rms[i].set_yticks([15, 20])
                ax_rms[i].set_yticklabels(["15", "20"], fontsize=7)
                ax_rms[i].set_ylim([0, 40])
                ax_rms[i].set_xlim([0, 17])
                ax_rms[i].set_ylabel("RMS", fontsize=10)
                ax_rms[i].grid()
                ax_rms[i].bar(ind+0.65, rms, 0.8, color=col)
                ax_rms[i].set_title("ADC RMS Pol X", fontsize=10)

        except:
            print "Something went wrong!"
            pass

        if cnt == 32:
            ax_title.cla()
            ax_title.set_axis_off()
            ax_title.plot([0.001, 0.002], color='w')
            ax_title.set_xlim(-20, 20)
            ax_title.set_ylim(-20, 20)
            ax_title.annotate(options.station, (-15, 10), fontsize=32, color='blue')
            ax_title.annotate(tile, (-5, -8), fontsize=28, color='green')
            titolo = "  ".join(obs[x][:-7-4].split("_")) + ":" + obs[x][-7-4:-7-2] + ":" + obs[x][-7-2:-7] + "  UTC"
            ax_title.annotate(titolo, (-16, -20), fontsize=16, color='black')

            ax_geo_map.cla()
            ax_geo_map.set_axis_off()
            ax_geo_map.plot([0.001, 0.002], color='w')
            ax_geo_map.set_xlim(-30, 40)
            ax_geo_map.set_ylim(-25.5, 25.5)
            circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
            ax_geo_map.add_artist(circle1)
            for c in ant_pos:
                ax_geo_map.plot(c[0], c[1], marker='+', markersize=6,
                    linestyle='None', color='k')
            ax_geo_map.annotate("E", (23, -1), fontsize=10, color='black')
            ax_geo_map.annotate("W", (-25.1, -1), fontsize=10, color='black')
            ax_geo_map.annotate("N", (-1, 21), fontsize=10, color='black')
            ax_geo_map.annotate("S", (-1, -24.6), fontsize=10, color='black')

            potenza_rf += prf
            ax_total_power.cla()
            for j in range(32):
                serie = potenza_rf[j::32]
                if j < 16:
                    ax_total_power.plot(range(len(serie)), serie, color='b')
                else:
                    ax_total_power.plot(range(len(serie)), serie, color='g')
            ax_total_power.set_xlim(0, len(obs))
            ax_total_power.set_xlabel("Hours", fontsize=10)
            ax_total_power.set_ylim(-15, 15)
            ax_total_power.set_ylabel("dBm", fontsize=10)
            ax_total_power.set_xticks(x_tick)
            ax_total_power.set_xticklabels(np.array(range(0, 3 * 9, 3)).astype("str").tolist())
            ax_total_power.grid()

            potenza_orbcomm += [max(porbcomm[:16])]
            potenza_orbcomm += [max(porbcomm[16:])]
            for i, (pol, c) in enumerate([("POL-X", 'b'), ("POL-Y", 'g')]):
                ax_orbcomm[i].cla()
                ax_orbcomm[i].plot(range(len(potenza_orbcomm)/2), potenza_orbcomm[i::2], color=c)
                ax_orbcomm[i].set_xlim(0, len(obs))
                ax_orbcomm[i].set_xlabel("Hours", fontsize=10)
                ax_orbcomm[i].set_ylim(-30, 0)
                ax_orbcomm[i].set_ylabel("dB", fontsize=10)
                ax_orbcomm[i].set_xticks(x_tick)
                ax_orbcomm[i].set_xticklabels(np.array(range(0, 3 * 9, 3)).astype("str").tolist())
                ax_orbcomm[i].set_yticks(np.arange(-30, 5, 5))
                ax_orbcomm[i].set_yticklabels(np.arange(-30, 5, 5).astype("str").tolist(), fontsize=10)
                ax_orbcomm[i].set_title("(133-143 MHz) ORBCOMM received power "+pol, fontsize=10)
                ax_orbcomm[i].grid()

            potenza_airplane += [max(pairplane[:16])]
            potenza_airplane += [max(pairplane[16:])]
            for i, (pol, c) in enumerate([("POL-X",'b'), ("POL-Y",'g')]):
                ax_airplane[i].cla()
                ax_airplane[i].plot(range(len(potenza_airplane)/2), potenza_airplane[i::2], color=c)
                ax_airplane[i].set_xlim(0, len(obs))
                ax_airplane[i].set_xlabel("Hours", fontsize=10)
                ax_airplane[i].set_ylim(-30, 0)
                ax_airplane[i].set_ylabel("dB", fontsize=10)
                ax_airplane[i].set_xticks(x_tick)
                ax_airplane[i].set_xticklabels(np.array(range(0, 3 * 9, 3)).astype("str").tolist())
                ax_airplane[i].set_yticks(np.arange(-30, 5, 5))
                ax_airplane[i].set_yticklabels(np.arange(-30, 5, 5).astype("str").tolist(), fontsize=10)
                ax_airplane[i].set_title("(120-130 MHz) Airplanes received power "+pol, fontsize=10)
                ax_airplane[i].grid()

            fig.tight_layout()#rect=[0, 0.03, 1, 0.95])
            fig.canvas.draw()
            # time.sleep(1)
            #print img_dir + "/" + tile + "_" + obs[x] + ".png"
            fig.savefig(img_dir + "/" + tile + "_" + obs[x] + ".png")

    os.system("ffmpeg -y -f image2 -i " + img_dir + "/%*.png  -vcodec libx264 " + video_dir + "/" +
              options.date + "_" + tile + ".avi")
