#!/usr/bin/env python

'''

   Phase-0 ADU RMS Plot of Bridging data saved with tpm_dump.py

   Input: /data/data_2/2018-11-LOW-BRIDGING/ + DATE directory
   Output: /data/data_2/2018-11-LOW-BRIDGING/ADURMS txt files and plot picture

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


if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("--dir",
                      dest="dir",
                      default="",
                      help="Directory containing tdd files")

    parser.add_option("--skipreadfile", action="store_true",
                      dest="skipreadfile",
                      default=False,
                      help="Use the files already saved")

    (options, args) = parser.parse_args()

    if options.dir == "":
        base_dir = easygui.diropenbox(title="Choose a directory file", default=BASE_DIR)
        if base_dir == None:
            print "\nMissing Directory. Exiting...\n"
            exit(0)
    else:
        base_dir = options.dir
        if not os.path.isdir(base_dir):
            print "\nThe given directory does not exist. Exiting...\n"
            exit(0)

    if not os.path.isdir(base_dir + "/DATA"):
        print "\nThe selected directory does not contain the DATA folder. Exiting...\n"
        exit(0)

    ADURMSDIR = base_dir + "/ADURMS"
    if not os.path.isdir(ADURMSDIR):
        os.makedirs(ADURMSDIR)
    ADURMSDIR += "/"
    if not options.skipreadfile:
        for rx in os.listdir(base_dir+"/DATA"):
            for pol in ["Pol-X", "Pol-Y"]:
                datapath = base_dir + "/DATA/" + rx + "/" + pol
                print "\nListing directory of", rx, pol,
                datafiles = sorted(glob.glob(datapath + "/*.tdd"))
                print " - Found " + str(len(datafiles)) + " \"tdd\" files.\n"

                adurms_file = open(ADURMSDIR + rx + "_" + pol + ".txt","w")
                for cnt in tqdm(range(len(datafiles))):
                    fname = datafiles[cnt]
                    # print fname.split("/")[-1][-21:-4]
                    orario = datetime.datetime.strptime(fname.split("/")[-1][-21:-4], "%Y-%m-%d_%H%M%S")
                    with open(fname, "r") as f:
                        a = f.read()
                    l = struct.unpack(">d", a[0:8])[0]
                    data = struct.unpack(">" + str(int(l)) + "b", a[8:])

                    adu_rms = np.sqrt(np.mean(np.power(data, 2), 0))
                    volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
                    power_adc = 10 * np.log10(
                        np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
                    power_rf = power_adc + 12  # single ended to diff net loose 12 dBm

                    epoch = time.mktime(orario.timetuple())
                    data = orario.strftime("%Y/%m/%d")
                    ora = orario.strftime("%H:%M:%S")
                    adurms_file.write(str(epoch) + "\t" + str(data) + "\t" + str(ora) + "\t" + str("%3.1f" % (adu_rms)) + "\n")
                adurms_file.close()

    with open(ADURMSDIR+"/"+os.listdir(ADURMSDIR)[0]) as fl:
        data = fl.readline()
    dati = data.replace("\n", "").split("\t")
    orario = datetime.datetime.strptime(dati[1] + " " + dati[2], "%Y/%m/%d %H:%M:%S")
    #datetime.datetime.utcfromtimestamp(dati[0])+datetime.timedelta(0,3600)
    day_start = time.mktime(orario.date().timetuple())
    day_stop  = time.mktime((orario.date() + datetime.timedelta(1)).timetuple())

    plt.ioff()

    gs = gridspec.GridSpec(1, 1)
    fig = plt.figure(figsize=(12, 7), facecolor='w')
    ax1 = fig.add_subplot(gs[0])

    rms = []
    x = []
    ax1.cla()
    for f in os.listdir(ADURMSDIR):
        if f[-4:] == ".txt":
            rms = []
            x = []
            l = f.split("/")[-1][:-4].replace("_"," ")
            with open(ADURMSDIR + f) as fl:
                data = fl.readlines()
            for d in data:
                dati = d.replace("\n", "").split("\t")
                t = datetime.datetime.strptime(dati[1] + " " + dati[2], "%Y/%m/%d %H:%M:%S")
                day = datetime.datetime(t.year, t.month, t.day)
                x += [(t - day).seconds]
                rms += [float(dati[3])]
            ax1.plot(x, rms, label=l)

    ax1.set_xlim(0, 24*60*60)
    ax1.set_ylim(0, 50)
    ax1.set_yticks(xrange(0, 55, 5))
    ax1.set_xticks(xrange(0, (24*60*60)+60, 60*60))
    ax1.set_xticklabels(np.array(xrange(25)).astype("str"))
    ax1.set_xlabel('UTC Day Hours')
    ax1.set_ylabel("ADU RMS")
    ax1.set_title("ADU RMS of Day " + str(orario.date()), fontsize=14)
    ax1.grid(True)
    ax1.legend(fontsize=10)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    plt.savefig(ADURMSDIR + str(orario.date()) + "_ADURMS.png")

