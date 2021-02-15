#!/usr/bin/env python

'''

  Lab Test Purposes

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2021, Istituto di RadioAstronomia, INAF, Italy"
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
#from bsp.tpm import *

DEVNULL = open(os.devnull, 'w')

# Other stuff
import numpy as np
import struct
import datetime
import time
import os

# Some globals
OUT_PATH = "/storage/lab/"


if __name__ == "__main__":
	from optparse import OptionParser
	parser = OptionParser()

	parser.add_option("-b", "--board",
					  dest="board",
					  default="10.0.10.1",
					  help="Board ip (def: 10.0.10.1)")

	parser.add_option("--input", action='store',
					  dest="input",
					  default=1,
					  help="Numbers of TPM input fiber to save (comma separated)")

	(opts, args) = parser.parse_args()

	print "\n######################################################"
	print "\n TPM Data Logger (Faster Version)"
	print "\n   - Time interval is as fast as possible!"
	# print "\n\nReading AAVS1 Google Spreadsheet"

	nsamples = 1024
	rbw = (800000.0 / 2 ** 17) * (2 ** 17 / nsamples)

	# Search for TPMs
	data = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y/%m/%d")
	ora = datetime.datetime.strftime(datetime.datetime.utcnow(), "%H:%M:%S")

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
		today = datetime.datetime.utcnow()
		ora = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y/%m/%d  %H:%M:%S")
		today = today.date()
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
				today = datetime.datetime.utcnow().date()

			if not os.path.exists(OUT_PATH):
				os.makedirs(OUT_PATH)
				sys.stdout.write("\nNew day... ")
				sys.stdout.flush()

			measnum = measnum + 1

			sys.stdout.write("\r" + orario + "  Saved: " + str(measnum))
			sys.stdout.flush()

			tpm = opts.board
			freqs, spettro, rawdata, adu_rms, power_rf = get_raw_meas(tpm_obj(tpm), debug=False)

			for rx in opts.input.split(","):
				for p, pol in enumerate(["X", "Y"]):
					fpath = OUT_PATH
					rxpath = str("RX-%02d/" % (int(rx)))
					if not os.path.exists(fpath + rxpath):
						os.makedirs(fpath + rxpath)
					fname = "Pol-%s/" % pol
					if not os.path.exists(fpath + rxpath + fname):
						os.makedirs(fpath + rxpath + fname)
					fname += str("TPM-%02d_RX-%02d_Pol-%s_" % (int(tpm.split(".")[-1]), int(rx), pol)) + ora

					with open(fpath + rxpath + fname + ".raw", "wb") as f:
						#f.write(struct.pack(">" + str(len(rawdata[((rx-1) * 2) + p])) + "b", *rawdata[((rx-1) * 2) + p]))
						f.write(struct.pack(">" + str(len(rawdata[((int(rx)-1) * 2) + p])) + "b", *rawdata[((int(rx)-1) * 2) + p]))
						f.flush()

			sys.stdout.write("\rMeasurement number # %d" % measnum)
			sys.stdout.flush()

	except KeyboardInterrupt:
		print "\n\nProgram terminated!\n\n"
