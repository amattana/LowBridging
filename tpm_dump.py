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

# Some globals
OUT_PATH = "/data/data_2/2018-11-LOW-BRIDGING/"
DATA_PATH = "DATA/"
POWER_DIR = "POWER/"
TRIGGER_DIR = "TRIGGER/"
POWER_DAY = "~/work/LowBridging/power_plot.py --silent -a --dir="+OUT_PATH

PHASE_0_MAP = [[0, "EDA2"], [1, "SKALA-4"], [2, "SKALA-2"], [3, "SKALA-41"]]


# rms_remap = [1, 0, 3, 2, 5, 4, 7, 6, 17, 16, 19, 18, 21, 20, 23, 22, 30, 31, 28, 29, 26, 27, 24, 25, 14, 15, 12, 13, 10, 11,
#         8, 9]


def plotta(dati, kname, pol, rfpow):
	my_dpi = 96
	plt.figure(figsize=(1000 / my_dpi, 600 / my_dpi), dpi=my_dpi)
	if pol == "X" or pol == 0:
		plt.plot(np.linspace(2, 400, len(dati[2:])), dati[2:], color='b')
	else:
		plt.plot(np.linspace(2, 400, len(dati[2:])), dati[2:], color='g')
	plt.xlim(0, 400)
	plt.ylim(-80, 0)
	plt.grid(True)
	plt.annotate("RF Power: " + "%3.1f" % (rfpow) + " dBm", (15, -7), fontsize=16)
	titolo = kname[kname.rfind("/") + 1:].replace("_", "  ")
	titolo = titolo[:-4] + ":" + titolo[-4:-2] + ":" + titolo[-2:] + " UTC"
	plt.title(titolo, fontsize=18)
	plt.savefig(kname + ".png")
	# print "SAVED: ",kname+".png"
	plt.close()


def plottali4(spettro, rfpower, ora):
	gs = gridspec.GridSpec(2, 2)
	figA = plt.figure(figsize=(12, 7), facecolor='w')
	p4_ax = []
	p4_ax += [figA.add_subplot(gs[0])]
	p4_ax += [figA.add_subplot(gs[1])]
	p4_ax += [figA.add_subplot(gs[2])]
	p4_ax += [figA.add_subplot(gs[3])]

	for cnt in xrange(len(PHASE_0_MAP)):

		p4_ax[cnt].cla()
		p4_ax[cnt].plot(np.linspace(0, 400, len(spettro[(PHASE_0_MAP[cnt][0] * 2)][1:])), spettro[(PHASE_0_MAP[cnt][0] * 2)][1:], color='b')
		p4_ax[cnt].plot(np.linspace(0, 400, len(spettro[(PHASE_0_MAP[cnt][0] * 2) + 1][1:])), spettro[(PHASE_0_MAP[cnt][0] * 2) + 1][1:], color='g')
		p4_ax[cnt].set_xlim(0, 400)
		p4_ax[cnt].set_ylim(-80, 0)
		p4_ax[cnt].set_xlabel('MHz')
		p4_ax[cnt].set_ylabel("dBm")
		p4_ax[cnt].set_title(PHASE_0_MAP[cnt][1] + " Pol X", fontsize=15)
		# ax1.annotate("RF Power: " + "%3.1f" % (rfpower[rms_remap[(PHASE_0_MAP[0][0]*2)]]) + " dBm", (10, -17), fontsize=16)
		p4_ax[cnt].annotate("RF Power: " + "%3.1f" % (rfpower[(PHASE_0_MAP[cnt][0] * 2)]) + " dBm", (10, -17), fontsize=16)
		p4_ax[cnt].grid(True)

	# plt.title(fname.split("/")[-1][:-4].replace("_","  "), fontsize=18)
	titolo = ora[:-7] + "  " + ora[-6:-4] + ":" + ora[-4:-2] + ":" + ora[-2:] + " UTC"
	figA.suptitle(titolo, fontsize=16)
	plt.tight_layout(rect=[0, 0.03, 1, 0.95])
	plt.savefig(OUT_PATH + "IMG/PLOT-A/LB_PHASE-0_A_" + ora + ".png")
	plt.close()


# plt.show()


def plottali2(spettro, rfpower, ora):
	RBW = 400000.0 / len(spettro[(PHASE_0_MAP[0][0] * 2)][1:])
	gs = gridspec.GridSpec(2, 1)
	figB = plt.figure(figsize=(12, 7), facecolor='w')
	p2_ax = []
	p2_ax += [figB.add_subplot(gs[0])]
	p2_ax += [figB.add_subplot(gs[1])]


	p2_ax[0].cla()
	p2_ax[0].plot(np.linspace(0, 400, len(spettro[(PHASE_0_MAP[0][0] * 2)][1:])), spettro[(PHASE_0_MAP[0][0] * 2)][1:],
				  color='b')
	p2_ax[0].plot(np.linspace(0, 400, len(spettro[(PHASE_0_MAP[0][0] * 2) + 1][1:])),
				  spettro[(PHASE_0_MAP[0][0] * 2) + 1][1:], color='g')
	p2_ax[0].set_xlim(0, 400)
	p2_ax[0].set_ylim(-80, 0)
	p2_ax[0].set_xlabel('MHz')
	p2_ax[0].set_ylabel("dBm")
	p2_ax[0].set_title(PHASE_0_MAP[0][1], fontsize=16)
	# ax1.annotate("RF Power: " + "%3.1f" % (rfpower[rms_remap[(PHASE_0_MAP[0][0]*2)]]) + " dBm", (12, -8), fontsize=16, color='b')
	# ax1.annotate("RF Power: " + "%3.1f" % (rfpower[rms_remap[(PHASE_0_MAP[0][0]*2)+1]]) + " dBm", (12, -17), fontsize=16, color='g')
	# p2_ax[0].annotate("TIME: " + orario + " UTC", (260, -7), fontsize=14, color='b')
	p2_ax[0].annotate("RF Power: " + "%3.1f" % (rfpower[(PHASE_0_MAP[0][0] * 2)]) + " dBm", (12, -8), fontsize=16,
					  color='b')
	p2_ax[0].annotate("RF Power: " + "%3.1f" % (rfpower[(PHASE_0_MAP[0][0] * 2) + 1]) + " dBm", (12, -17), fontsize=16,
					  color='g')
	p2_ax[0].annotate("RBW: " + str("%3.1f" % RBW) + "KHz", (320, -15), fontsize=12)
	p2_ax[0].grid(True)

	p2_ax[1].cla()
	p2_ax[1].plot(np.linspace(0, 400, len(spettro[(PHASE_0_MAP[1][0] * 2)][1:])), spettro[(PHASE_0_MAP[1][0] * 2)][1:],
				  color='b')
	p2_ax[1].plot(np.linspace(0, 400, len(spettro[(PHASE_0_MAP[1][0] * 2) + 1][1:])),
				  spettro[(PHASE_0_MAP[1][0] * 2) + 1][1:], color='g')
	p2_ax[1].set_xlim(0, 400)
	p2_ax[1].set_ylim(-80, 0)
	p2_ax[1].set_xlabel('MHz')
	p2_ax[1].set_ylabel("dBm")
	p2_ax[1].set_title(" " + PHASE_0_MAP[1][1] + " ", fontsize=16)
	# ax2.annotate("RF Power: " + "%3.1f" % (rfpower[rms_remap[(PHASE_0_MAP[1][0]*2)]]) + " dBm", (12, -8), fontsize=16, color='b')
	# ax2.annotate("RF Power: " + "%3.1f" % (rfpower[rms_remap[(PHASE_0_MAP[1][0]*2)+1]]) + " dBm", (12, -17), fontsize=16, color='g')
	p2_ax[1].annotate("RF Power: " + "%3.1f" % (rfpower[(PHASE_0_MAP[1][0] * 2)]) + " dBm", (12, -8), fontsize=16,
					  color='b')
	p2_ax[1].annotate("RF Power: " + "%3.1f" % (rfpower[(PHASE_0_MAP[1][0] * 2) + 1]) + " dBm", (12, -17), fontsize=16,
					  color='g')
	p2_ax[1].annotate("RBW: " + str("%3.1f" % RBW) + "KHz", (320, -15), fontsize=12)
	p2_ax[1].grid(True)

	titolo = ora[:-7] + "  " + ora[-6:-4] + ":" + ora[-4:-2] + ":" + ora[-2:] + " UTC"
	figB.suptitle(titolo, fontsize=16)
	plt.tight_layout(rect=[0, 0.03, 1, 0.95])
	plt.savefig(OUT_PATH + "IMG/PLOT-B/LB_PHASE-0_B_" + ora + ".png")

	plt.close()


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

	# parser.add_option("-i", "--inputs",
	#                  dest="inputs",
	#                  default="0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31",
	#                  help="Which input to dump (def: all 32, otherwise i.e: 0,1,2,3)")

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

	print "\n######################################################"
	print "\n TPM Data Logger"
	print "\n   - Time interval is " + str(options.dtime) + " seconds"
	# print "\n\nReading AAVS1 Google Spreadsheet"

	if options.debug:
		print "   - # DEBUG MODE: Using saved data !!!\n"

		# Read google Spreadsheet
	# cells = loadAAVSdata()
	# tpm_used = max([a['TPM'] for a in cells if not a['TPM'] == ""])+1
	tpm_used = 1

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

	plt.ioff()
	counter = 0
	try:
		# num = long(options.num)
		ora = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y/%m/%d  %H:%M:%S")
		today = datetime.datetime.utcfromtimestamp(time.time()).date()
		sys.stdout.write(ora + " Starting Acquisitions...\n\n")
		sys.stdout.flush()
		measnum = 0
		tot_triggered = 0

		last_meas = last_power = trigger_time = time.time()
		mask_trigger = False

		while True:
			counter = counter + 1
			epoch = time.time()
			actual_time = datetime.datetime.utcfromtimestamp(epoch)
			ora = datetime.datetime.strftime(actual_time, "%Y-%m-%d_%H%M%S")
			orario = datetime.datetime.strftime(actual_time, "%Y/%m/%d  %H:%M:%S")

			# Creating Directory for today's data
			if not actual_time.date() == today:
				#os.system(POWER_DAY+today.strftime("%Y-%m-%d")+"/POWER/")
				OUT_PATH = OUT_PATH[:-11] + datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()),
																	   "%Y-%m-%d/")
				measnum = 0
				tot_triggered = 0
				today = datetime.datetime.utcfromtimestamp(time.time()).date()

			tpath = OUT_PATH + TRIGGER_DIR
			pdir = OUT_PATH + POWER_DIR
			if not os.path.exists(OUT_PATH):
				os.makedirs(OUT_PATH)
				sys.stdout.write("\nNew day... ")
				sys.stdout.flush()

			## Creating Directory to store the videos
			if not os.path.exists(OUT_PATH + "IMG"):
				os.makedirs(OUT_PATH + "IMG")
				os.makedirs(OUT_PATH + "IMG/PLOT-A")
				os.makedirs(OUT_PATH + "IMG/PLOT-B")
			if not os.path.exists(pdir):
				os.makedirs(pdir)
			if not os.path.exists(tpath):
				os.makedirs(tpath)

			save_data = 0
			if ((measnum == 0) or (int(epoch) - last_meas >= (int(options.dtime)))):
				save_data = 1
				measnum = measnum + 1
				last_meas = int(epoch)

			save_power = 0
			if ((measnum == 0) or (int(epoch) - last_power >= int(options.ptime))):
				save_power = 1
				last_power = int(epoch)

			sys.stdout.write("\r" + orario + "  Saved: " + str(measnum) + ",  Triggered: " + str(tot_triggered))
			sys.stdout.flush()

			for i in TPMs:
				tpm = int(i.split(".")[-1])
				freqs, spettro, rawdata, rms, rfpower = get_raw_meas(tpm_obj(i), debug=options.debug)
				triggered = False
				for rx in xrange(len(spettro) / 2):
					if rx in np.transpose(PHASE_0_MAP)[0].astype(np.int):
						if ((rfpower[(rx * 2)] > float(options.trigger)) or (
							rfpower[(rx * 2) + 1] > float(options.trigger))):
							triggered = True
						# print "\n",rx, rfpower[(rx * 2)], rfpower[(rx * 2) + 1],  float(options.trigger), (rfpower[(rx * 2)] > float(options.trigger))
				if triggered and not mask_trigger:
					tot_triggered = tot_triggered + 1
					trigger_time = int(epoch)
				# print "\n", options.trigger, triggered, len(spettro)/2, rfpower
				for rx in xrange(len(spettro) / 2):
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
								if not os.path.exists(tpath + rxpath + fname):
									os.makedirs(tpath + rxpath + fname)
								fname += str("TPM-%02d" % (int(i.split(".")[-1]))) + str(
									"_RX-%02d_" % (int(rx + 1)))  # + "_BASE-"
								fname += [x[1] for x in PHASE_0_MAP if (x[0] == rx)][0]
								fname += "_Pol-X_" + ora
								pname = pdir + "POWER_" + [x[1] for x in PHASE_0_MAP if (x[0] == rx)][0] + "_Pol-X.csv"
								rfpow = rfpower[(rx * 2)]
								if save_power:
									with open(pname, "a") as pfile:
										msg = str("%3.1f" % (epoch)) + "\t" + orario.replace("  ", "\t") + "\t" + str(
											"%3.1f" % (rfpow))
										pfile.write(msg + "\n")

							else:
								pol = "Y"
								fname = "Pol-Y/"
								if not os.path.exists(fpath + rxpath + fname):
									os.makedirs(fpath + rxpath + fname)
								if not os.path.exists(tpath + rxpath + fname):
									os.makedirs(tpath + rxpath + fname)
								fname += str("TPM-%02d" % (int(i.split(".")[-1]))) + str(
									"_RX-%02d_" % (int(rx + 1)))  # +"_BASE-"
								fname += [x[1] for x in PHASE_0_MAP if (x[0] == rx)][0]
								fname += "_Pol-Y_" + ora
								# Save the total power every measurements
								rfpow = rfpower[(rx * 2) + 1]
								if save_power:
									pname = pdir + "POWER_" + [x[1] for x in PHASE_0_MAP if (x[0] == rx)][
										0] + "_Pol-Y.csv"
									with open(pname, "a") as pfile:
										msg = str("%3.1f" % (epoch)) + "\t" + orario.replace("  ", "\t") + "\t" + str(
											"%3.1f" % (rfpow))
										pfile.write(msg + "\n")

							if triggered and not mask_trigger:
								with open(tpath + rxpath + fname + ".tdd", "wb") as f:
									f.write(struct.pack(">d", len(rawdata[(rx * 2) + p])))
									f.write(struct.pack(">" + str(len(rawdata[(rx * 2) + p])) + "b",
														*rawdata[(rx * 2) + p]))
								plotta(spettro[(rx * 2) + p], tpath + rxpath + fname, pol, rfpow)

							if save_data:
								with open(fpath + rxpath + fname + ".tdd", "wb") as f:
									f.write(struct.pack(">d", len(rawdata[(rx * 2) + p])))
									f.write(struct.pack(">" + str(len(rawdata[(rx * 2) + p])) + "b",
														*rawdata[(rx * 2) + p]))
								plotta(spettro[(rx * 2) + p], fpath + rxpath + fname, pol, rfpow)

				plottali4(spettro, rfpower, ora)
				plottali2(spettro, rfpower, ora)
			if triggered:
				mask_trigger = True
			if int(epoch) - trigger_time >= 60:
				mask_trigger = False
			# if not actual_time.date() == today:
			# plot the power of the day


	except KeyboardInterrupt:
		print "\n\nProgram terminated!\n\n"
