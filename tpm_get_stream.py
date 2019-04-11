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
OUT_PATH = "/data/data_2/2018-11-LOW-BRIDGING/"
WWW_PATH = "/data/data_2/2018-11-LOW-BRIDGING/WWW/"
DATA_PATH = "DATA/"
POWER_DIR = "POWER/"
TRIGGER_DIR = "TRIGGER/"
POWER_DAY = "~/work/LowBridging/power_plot.py --silent -a --dir=" + OUT_PATH

PHASE_0_MAP = [[0, "EDA-2"], [1, "SKALA-4.0"], [4, "SKALA-2"], [5, "SKALA-4.1"]]


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-s", "--time_spectra",
                      dest="dtime",
                      default=60,
                      help="Time interval in minutes (Default: 60 seconds)")

    parser.add_option("-p", "--time_power",
                      dest="ptime",
                      default=5,
                      help="Time interval in seconds (Default: 5 seconds)")

    parser.add_option("-n", "--number",
                      dest="num",
                      default=-1,
                      help="Number of measurements, if not given or negative neverending")

    parser.add_option("-b", "--board",
                      dest="board",
                      default="10.0.10.2",
                      help="Board ip (def: 10.0.10.2)")

    parser.add_option("-t", "--trigger",
                      dest="trigger",
                      default=10,
                      help="Power trigger in dBm. If RF power is higher than the trigger extra data is saved")

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
    data = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y/%m/%d")
    ora = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%H:%M:%S")

    # Creating Main data Directory
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)
        print "Generating main directory for data... (" + OUT_PATH + ")"

    # Creating Directory for today's data
    OUT_PATH = OUT_PATH + datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y-%m-%d/")
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)
        print "Generating directory for today data... (" + OUT_PATH + ")"

    ## Creating Directory to store the videos
    if not os.path.exists(OUT_PATH + "IMG"):
        os.makedirs(OUT_PATH + "IMG")
        os.makedirs(OUT_PATH + "IMG/PLOT-A")
        os.makedirs(OUT_PATH + "IMG/PLOT-B")
    if not os.path.exists(OUT_PATH + POWER_DIR):
        os.makedirs(OUT_PATH + POWER_DIR)
    if not os.path.exists(OUT_PATH + TRIGGER_DIR):
        os.makedirs(OUT_PATH + TRIGGER_DIR)

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
            tot_triggered = 0
            today = datetime.datetime.utcfromtimestamp(time.time()).date()

        tpath = OUT_PATH + TRIGGER_DIR
        pdir = OUT_PATH + POWER_DIR

        save_data = 1
        if ((measnum == 0) or (int(epoch) - last_meas >= (int(options.dtime)))):
            save_data = 1
            measnum = measnum + 1
            last_meas = int(epoch)

        save_power = 0
        if ((measnum == 0) or (int(epoch) - last_power >= int(options.ptime))):
            save_power = 1
            last_power = int(epoch)

        sys.stdout.write(str(TPM) + " " + orario + "  Saved: " + str(measnum) + ",  Triggered: " + str(tot_triggered))
        sys.stdout.flush()

        #tpm = int(TPM.split(".")[-1])
        freqs, spettro, rawdata, rms, rfpower = get_raw_meas(tpm_obj(TPM), debug=options.debug)
        triggered = False
        for rx in xrange(len(spettro) / 2):
            if rx in np.transpose(PHASE_0_MAP)[0].astype(np.int):
                if ((rfpower[(rx * 2)] > float(options.trigger)) or (
                        rfpower[(rx * 2) + 1] > float(options.trigger))):
                    triggered = True
        if triggered and not mask_trigger:
            tot_triggered = tot_triggered + 1
            trigger_time = int(epoch)
        for rx in xrange(len(spettro) / 2):
            if rx in np.transpose(PHASE_0_MAP)[0].astype(np.int):
                for pol in ["X", "Y"]:
                    fpath = OUT_PATH + DATA_PATH
                    rxpath = str("RX-%02d_" % (int(rx + 1)))
                    rxpath += [x[1] for x in PHASE_0_MAP if (x[0] == rx)][0]
                    rxpath += "/"
                    if not os.path.exists(fpath + rxpath):
                        os.makedirs(fpath + rxpath)
                    fname = "Pol-" + pol + "/"
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


                    if triggered and not mask_trigger:
                        with open(tpath + rxpath + fname + ".tdd", "wb") as f:
                            f.write(struct.pack(">d", len(rawdata[(rx * 2) + p])))
                            f.write(struct.pack(">" + str(len(rawdata[(rx * 2) + p])) + "b",
                                                *rawdata[(rx * 2) + p]))

                    if save_data:
                        with open(fpath + rxpath + fname + ".tdd", "wb") as f:
                            f.write(struct.pack(">d", len(rawdata[(rx * 2) + p])))
                            f.write(struct.pack(">" + str(len(rawdata[(rx * 2) + p])) + "b",
                                                *rawdata[(rx * 2) + p]))

    except KeyboardInterrupt:
        print "\n\nProgram terminated!\n\n"
