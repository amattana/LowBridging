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
import os, easygui, glob
from optparse import OptionParser
import numpy as np

import matplotlib.gridspec as gridspec
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

    parser.add_option("--multiplot", action="store_true",
                      dest="multiplot",
                      default=False,
                      help="Plot all the RX files in a grid multiplots")

    (options, args) = parser.parse_args()

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

    if not os.path.isdir(base_dir + "/CSV"):
        print "\nThe selected directory does not contain the CSV folder. Exiting...\n"
        exit(0)

    PLOTSDIR = base_dir + "/PLOTS"
    if not os.path.isdir(PLOTSDIR):
        os.makedirs(PLOTSDIR)
    PLOTSDIR += "/"

    VIDEODIR = base_dir + "/VIDEO"
    if not os.path.isdir(VIDEODIR):
        os.makedirs(VIDEODIR)
    VIDEODIR += "/"

    if not options.multiplot:
        plt.ioff()
        gs = gridspec.GridSpec(1, 1)
        fig = plt.figure(figsize=(12, 7), facecolor='w')
        ax1 = fig.add_subplot(gs[0])

        datapath = base_dir + "/CSV/"
        print "\nListing directory of", datapath
        datafiles = sorted(glob.glob(datapath + "*.csv"))
        print " - Found " + str(len(datafiles)) + " \"csv\" files.\n"
        for fname in datafiles:
            CSVPLOTSDIR = fname.split("/")[-1][:-4]
            if not os.path.isdir(PLOTSDIR + CSVPLOTSDIR):
                os.makedirs(PLOTSDIR + CSVPLOTSDIR)
            CSVPLOTSDIR += "/"

            with open(fname, "r") as f:
                a = f.readlines()
            if len(a) < 2:
                print "There are no measurements in file: ",fname, "\n"
                pass
            x = np.linspace(0,400,len(a[1].split()[2:]))
            rbw = 400000.0/len(x)
            for spettro in tqdm(a[1:]):
                data = spettro.split()[2:]
                ax1.cla()
                ax1.plot(x, np.array(data).astype("float"))
                ax1.set_xlim(0, 400)
                ax1.set_ylim(-100, 0)
                ax1.set_xlabel('MHz')
                ax1.set_ylabel("dB")
                ax1.set_title("  ".join(spettro.split()[0].split("_")) + "  UTC", fontsize=20)
                ax1.grid(True)
                ax1.annotate("RBW: " + "%3.1f" % (rbw) + " KHz", (280, -8), fontsize=20, color='g')
                ax1.annotate("RF Power:  " + spettro.split()[1] + " dBm", (280, -15), fontsize=20, color='b')
                plt.tight_layout(rect=[0, 0.03, 1, 0.95])
                plt.savefig(PLOTSDIR + CSVPLOTSDIR + fname.split("/")[-1][:-4] + "_" + spettro.split()[0] + ".png")
        os.system("ffmpeg -y -f image2 -i " + PLOTSDIR + CSVPLOTSDIR  + "%*.png -vcodec libx264 " + VIDEODIR + fname.split("/")[-1][:-4] + ".avi")

    else:

        datapath = base_dir + "/CSV/"
        print "\nListing directory of", datapath
        datafiles = sorted(glob.glob(datapath + "*.csv"))
        print " - Found " + str(len(datafiles)) + " \"csv\" files.\n"

        plt.ioff()
        gs = gridspec.GridSpec(int(np.ceil(np.sqrt(len(datafiles)))), int(np.ceil(np.sqrt(len(datafiles)))))
        fig = plt.figure(figsize=(12, 7), facecolor='w')
        ax = np.array([])
        for i in range(len(datafiles)):
            ax = np.concatenate((ax, [fig.add_subplot(gs[i])]), axis=0)
