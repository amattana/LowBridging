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

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

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
POWER_DAY = "~/work/LowBridging/power_plot.py --silent -a --dir="+OUT_PATH

PHASE_0_MAP = [[0, "EDA-2"], [1, "SKALA-4.0"], [4, "SKALA-2"], [5, "SKALA-4.1"]]


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-n", "--number",
					  dest="num",
					  default=-1,
					  help="Number of measurements, if not given or negative neverending")

	parser.add_option("-b", "--board",
					  dest="board",
					  default="10.0.10.2",
					  help="Board ip (def: 10.0.10.2)")

	parser.add_option("-d", "--debug", action='store_true',
					  dest="debug",
					  default=False,
					  help="If set the program runs in debug mode")

	(options, args) = parser.parse_args()

	print "\n######################################################"
	print "\n TPM Data Logger (Faster Version)"
	print "\n   - Time interval is as fast as possible!"
	# print "\n\nReading AAVS1 Google Spreadsheet"

	if options.debug:
		print "   - # DEBUG MODE: Using saved data !!!\n"

		# Read google Spreadsheet
	# cells = loadAAVSdata()
	# tpm_used = max([a['TPM'] for a in cells if not a['TPM'] == ""])+1
	tpm_used = 1

	nsamples = 1024
	rbw = (800000.0 / 2 ** 17) * (2 ** 17 / nsamples)

	# inputs = options.inputs.split(",")

	# Search for TPMs
	TPMs = [str(options.board)]
	data = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y/%m/%d")
	ora = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%H:%M:%S")
	# print "Start Logging on " + data + " at " + ora
	# TPMs = ['10.0.10.{0}'.format(i+1) for i in xrange(16)]

	# Creating Main data Directory
	if not os.path.exists(OUT_PATH):
		os.makedirs(OUT_PATH)
		print "Generating main directory for data... (" + OUT_PATH + ")"

	# Creating Directory for today's data
	OUT_PATH = OUT_PATH + datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y-%m-%d/")
	if not os.path.exists(OUT_PATH):
		os.makedirs(OUT_PATH)
		print "Generating directory for today data... (" + OUT_PATH + ")"

	counter = 0
	try:
		# num = long(options.num)
		ora = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y/%m/%d  %H:%M:%S")
		today = datetime.datetime.utcfromtimestamp(time.time()).date()
		sys.stdout.write(ora + " Starting Acquisitions...\n\n")
		sys.stdout.flush()
		measnum = 0

		while True:
			counter = counter + 1
			epoch = time.time()
			actual_time = datetime.datetime.utcfromtimestamp(epoch)
			ora = datetime.datetime.strftime(actual_time, "%Y-%m-%d_%H%M%S%f")[:-3]
			orario = datetime.datetime.strftime(actual_time, "%Y/%m/%d  %H:%M:%S")

			# Creating Directory for today's data
			if not actual_time.date() == today:
				#os.system(POWER_DAY+today.strftime("%Y-%m-%d")+"/POWER/")
				OUT_PATH = OUT_PATH[:-11] + datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()),
																	   "%Y-%m-%d/")
				measnum = 0
				today = datetime.datetime.utcfromtimestamp(time.time()).date()

			if not os.path.exists(OUT_PATH):
				os.makedirs(OUT_PATH)
				sys.stdout.write("\nNew day... ")
				sys.stdout.flush()

			measnum = measnum + 1

			sys.stdout.write("\r" + orario + "  Saved: " + str(measnum) )
			sys.stdout.flush()

			for i in TPMs:
				tpm = int(i.split(".")[-1])
				rawdata = get_adc_samples(tpm_obj(i), debug=options.debug)
				for rx in xrange(len(rawdata) / 2):
					if rx in np.transpose(PHASE_0_MAP)[0].astype(np.int):
						for p in xrange(2):
							fpath = OUT_PATH + DATA_PATH
							rxpath = str("RX-%02d_" % (int(rx + 1)))
							rxpath += [x[1] for x in PHASE_0_MAP if (x[0] == rx)][0]
							rxpath += "/"
							if not os.path.exists(fpath + rxpath):
								os.makedirs(fpath + rxpath)
							if p % 2 == 0:
								pol = "X"
								fname = "Pol-X/"
								if not os.path.exists(fpath + rxpath + fname):
									os.makedirs(fpath + rxpath + fname)
								fname += str("TPM-%02d" % (int(i.split(".")[-1]))) + str(
									"_RX-%02d_" % (int(rx + 1)))  # + "_BASE-"
								fname += [x[1] for x in PHASE_0_MAP if (x[0] == rx)][0]
								fname += "_Pol-X_" + ora

							else:
								pol = "Y"
								fname = "Pol-Y/"
								if not os.path.exists(fpath + rxpath + fname):
									os.makedirs(fpath + rxpath + fname)
								fname += str("TPM-%02d" % (int(i.split(".")[-1]))) + str(
									"_RX-%02d_" % (int(rx + 1)))  # +"_BASE-"
								fname += [x[1] for x in PHASE_0_MAP if (x[0] == rx)][0]
								fname += "_Pol-Y_" + ora


							with open(fpath + rxpath + fname + ".tdd", "wb") as f:
								f.write(struct.pack(">d", len(rawdata[(rx * 2) + p])))
								f.write(struct.pack(">" + str(len(rawdata[(rx * 2) + p])) + "b",
													*rawdata[(rx * 2) + p]))

	except KeyboardInterrupt:
		print "\n\nProgram terminated!\n\n"
