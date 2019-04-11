#!/usr/bin/env python

'''

  Low Bridging Phase 0 Logger.

  It produces for each antenna and for both pols:
    -  Time domain binary data (first double word (64b) is the lenght of the following double word (64b) elements)
    -  Spectra binary data (first double word (64b) is the lenght of the following double word (64b) elements)
    -  Picture of the spectra

  Logging period can be specified in minutes with parameter -t (--time)

  When hit Ctrl+C (Keyboard Interrupt Signal) it produces
    -  A Movie (MPEG4 avi) for each antenna saved in the videos folder with subfolders for each pol

'''

__author__ = "Andrea Mattana"
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
from tpm_utils import *
from bsp.tpm import *

DEVNULL = open(os.devnull, 'w')

from gui_utils import *
from rf_jig import *
from rfjig_bsp import *
from ip_scan import *

from optparse import OptionParser


# Other stuff
import numpy as np
import struct
import datetime
import time

# Some globals
OUT_PATH = "/data/data_2/2019-LOW-BRIDGING-PHASE1/"
WWW_PATH = "/data/data_2/2019-LOW-BRIDGING-PHASE1/WWW/"
DATA_PATH = "DATA/"
POWER_DIR = "POWER/"
POWER_DAY = "~/work/LowBridging/power_plot.py --silent -a --dir=" + OUT_PATH

PHASE_0_MAP = [[0, "EDA-2"], [1, "SKALA-4.0"], [4, "SKALA-2"], [5, "SKALA-4.1"]]


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-b", "--board",
                      dest="board",
                      default="10.0.10.2",
                      help="Board ip (def: 10.0.10.2)")

    parser.add_option("--tile",
                      dest="tile",
                      default="10",
                      help="Numer of the Tile (def: 10)")

    parser.add_option("-d", "--debug", action='store_true',
                      dest="debug",
                      default=False,
                      help="If set the program runs in debug mode")

    (options, args) = parser.parse_args()

    if options.debug:
        print "["+str(options.board)+"] DEBUG MODE: Using saved data !!!\n"

    nsamples = 1024
    rbw = (800000.0 / 2 ** 17) * (2 ** 17 / nsamples)

    # Search for TPMs
    TPM = str(options.board)
    TILE = str(options.tile)
    TILE_PATH = "TILE-%02d/"%(int(TILE))
    data = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y/%m/%d")
    ora = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%H:%M:%S")

    # Creating Main data Directory
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)
        print "Generating main directory for data... (" + OUT_PATH + ")"

    # Creating Directory for today's data
    OUT_PATH = OUT_PATH + datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y-%m-%d/")
    try:
        if not os.path.exists(OUT_PATH):
            os.makedirs(OUT_PATH)
            print "Generating directory for today data... (" + OUT_PATH + ")"
    except:
        print "Directory " + OUT_PATH + " already exist..."

    ## Creating Directory to store the videos
    if not os.path.exists(OUT_PATH + "IMG"):
        os.makedirs(OUT_PATH + "IMG")
        os.makedirs(OUT_PATH + "IMG/PLOT-A")
        os.makedirs(OUT_PATH + "IMG/PLOT-B")
    if not os.path.exists(OUT_PATH + POWER_DIR):
        os.makedirs(OUT_PATH + POWER_DIR)
    pdir = OUT_PATH + POWER_DIR

    counter = 0
    try:
        # num = long(options.num)
        ora = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y/%m/%d  %H:%M:%S")
        today = datetime.datetime.utcfromtimestamp(time.time()).date()
        measnum = 0
        tot_triggered = 0

        last_meas = last_power = trigger_time = time.time()
        mask_trigger = False

        counter = counter + 1
        epoch = time.time()
        actual_time = datetime.datetime.utcfromtimestamp(epoch)
        ora = datetime.datetime.strftime(actual_time, "%Y-%m-%d_%H%M%S")
        orario = datetime.datetime.strftime(actual_time, "%Y/%m/%d  %H:%M:%S")

        # Creating Directory for today's data
        if not actual_time.date() == today:
            # os.system(POWER_DAY+today.strftime("%Y-%m-%d")+"/POWER/")
            OUT_PATH = OUT_PATH[:-11] + datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()),
                                                                   "%Y-%m-%d/")
            measnum = 0
            today = datetime.datetime.utcfromtimestamp(time.time()).date()

        pdir = OUT_PATH + POWER_DIR

        save_data = 1
        save_power = 1

        freqs, spettro, rawdata, rms, rfpower = get_raw_meas(tpm_obj(TPM), debug=options.debug)

        for rx in xrange(len(spettro) / 2):
            if rx in np.transpose(PHASE_0_MAP)[0].astype(np.int):
                for p, pol in enumerate(["X", "Y"]):
                    fpath = OUT_PATH + DATA_PATH
                    if not os.path.exists(fpath):
                        os.makedirs(fpath)
                    fpath += TILE_PATH
                    if not os.path.exists(fpath):
                        os.makedirs(fpath)
                    rxpath = str("RX-%02d_" % (int(rx + 1)))
                    rxpath += [x[1] for x in PHASE_0_MAP if (x[0] == rx)][0]
                    rxpath += "/"
                    if not os.path.exists(fpath + rxpath):
                        os.makedirs(fpath + rxpath)
                    fname = "Pol-" + pol + "/"
                    if not os.path.exists(fpath + rxpath + fname):
                        os.makedirs(fpath + rxpath + fname)
                    fname += str("TPM-%02d" % (int(TPM.split(".")[-1]))) + str(
                        "_RX-%02d_" % (int(rx + 1)))  # + "_BASE-"
                    fname += [x[1] for x in PHASE_0_MAP if (x[0] == rx)][0]
                    fname += "_Pol-" + pol + "_" + ora
                    pname = pdir + "POWER_" + [x[1] for x in PHASE_0_MAP if (x[0] == rx)][0] + "_Pol-" + pol + ".csv"
                    rfpow = rfpower[(rx * 2)]
                    if save_power:
                        with open(pname, "a") as pfile:
                            msg = str("%3.1f" % (epoch)) + "\t" + orario.replace("  ", "\t") + "\t" + str(
                                "%3.1f" % (rfpow))
                            pfile.write(msg + "\n")

                    if save_data:
                        with open(fpath + rxpath + fname + ".tdd", "wb") as f:
                            f.write(struct.pack(">d", len(rawdata[(rx * 2) + p])))
                            f.write(struct.pack(">" + str(len(rawdata[(rx * 2) + p])) + "b",
                                                *rawdata[(rx * 2) + p]))

    except KeyboardInterrupt:
        print "\n\nProgram terminated!\n\n"
