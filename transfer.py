#!/usr/bin/env python

'''

  Transfer data from AAVS1-server to CERBERUS
'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2018, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import os, glob
from optparse import OptionParser


DEF_PATH = "/data/data_2/2018-11-LOW-BRIDGING/"
SPG_DIR = "SPECTROGRAM/"
TPM_INPUTS = ["RX-01_EDA2", "RX-02_SKALA-4"]
POLS = ["Pol-X", "Pol-Y"]


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--data", dest="data", default="", help="Date in format YYYY-MM-DD")
	parser.add_option("--novideo", action='store_true', dest="novideo", default=False, help="If set do not produce videos (to save time)")
	parser.add_option("--nopower", action='store_true', dest="nopower", default=False, help="If set do not produce power plots (to save time)")
	parser.add_option("--notrigger", action='store_true', dest="notrigger", default=False, help="If set do not copy trigger plots (to save time)")
	parser.add_option("--nospectrogram", action='store_true', dest="nospectrogram", default=False, help="If set do not produce spectrograms (to save time)")

	(options, args) = parser.parse_args()

	if options.data == "":
		print "\nInput missing (date)!\n\nExiting....\n"
		exit(0)
	else:
		data = options.data

	CMD_VIDEO_A = "ffmpeg -y -f image2 -i " + DEF_PATH + data + "/IMG/PLOT-A/%*.png -vcodec libx264 " + DEF_PATH + data + "/VIDEO/LB_PHASE-0_A_"
	CMD_VIDEO_B = "ffmpeg -y -f image2 -i " + DEF_PATH + data + "/IMG/PLOT-B/%*.png -vcodec libx264 " + DEF_PATH + data + "/VIDEO/LB_PHASE-0_B_"

	if os.path.isdir(DEF_PATH + data):
		#os.system("cd " + DEF_PATH + data)
		print "\nGenerating Directories on Cerberus..."
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/POWER" + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/POWER" + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/POWER/CH-160" + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/VIDEO" + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/TRIGGER" + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/SPECTROGRAM" + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/SPECTROGRAM/"+ TPM_INPUTS[0] + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/SPECTROGRAM/"+ TPM_INPUTS[0] + "/" + POLS[0] + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/SPECTROGRAM/"+ TPM_INPUTS[0] + "/" + POLS[1] + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/SPECTROGRAM/"+ TPM_INPUTS[1] + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/SPECTROGRAM/"+ TPM_INPUTS[1] + "/" + POLS[0] + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/SPECTROGRAM/"+ TPM_INPUTS[1] + "/" + POLS[1] + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/SPECTROGRAM" + "\"")

		if not options.novideo:
			print "\nGenerating Videos... "
			os.system("mkdir " + DEF_PATH + data + "/VIDEO")
			print "\n\n*  [1/2] " + CMD_VIDEO_A+data+".avi ...\n\n"
			os.system(CMD_VIDEO_A+data+".avi")
			print "\n\n*  [1/2] " + CMD_VIDEO_A+data+".avi ...done!"
			print "\n*  [2/2] " + CMD_VIDEO_B+data+".avi ...\n\n"
			os.system(CMD_VIDEO_B+data+".avi")
			print "\n*  [2/2] " + CMD_VIDEO_B+data+".avi ...done!\n"

		if not options.nopower:
			print "\nGenerating Power Plot..."
			os.system("~/work/LowBridging/power_plot.py -a --dir=" + DEF_PATH + data + "/POWER/" )

		print "\nCopying data to Cerberus...\n\n"

		if not options.notrigger:
			print "\nListing triggered data..."
			lista = sorted(glob.glob(DEF_PATH + data + "/TRIGGER/" + TPM_INPUTS[0] + "/" + POLS[0] + "/*png"))
			for l in lista:
				os.system("scp " + DEF_PATH + data + "/IMG/PLOT-A/*" + l[-10:-4] + "* aavs@cerberus.mwa128t.org:/home/aavs/mattana/" + data + "/TRIGGER/")
				os.system("scp " + DEF_PATH + data + "/IMG/PLOT-B/*" + l[-10:-4] + "* aavs@cerberus.mwa128t.org:/home/aavs/mattana/" + data + "/TRIGGER/")
			os.system("scp -r " + DEF_PATH + data + "/TRIGGER aavs@cerberus.mwa128t.org:/home/aavs/mattana/" + data + "/")

		if not options.novideo:
			os.system("scp " + DEF_PATH + data + "/VIDEO/LB_PHASE-0_*avi aavs@cerberus.mwa128t.org:/home/aavs/mattana/" + data + "/VIDEO/")

		if not options.nopower:
			os.system("scp " + DEF_PATH + data + "/POWER/*png aavs@cerberus.mwa128t.org:/home/aavs/mattana/" + data + "/POWER/")
			os.system("scp " + DEF_PATH + data + "/POWER/*csv aavs@cerberus.mwa128t.org:/home/aavs/mattana/" + data + "/POWER/")

		if not options.nospectrogram:
			for tpm_rx in TPM_INPUTS:
				for pol in POLS:
					print "\nGenerating Spectrograms for " + tpm_rx + " " + pol + "..."
					os.system("~/work/LowBridging/tpm_tdd_view.py --average=16  --start-freq=0 --stop-freq=400 --power --channel=160 --recursive --water --dir=" + DEF_PATH + data + "/DATA/" + tpm_rx + "/" + pol)
					os.system("scp -r " + DEF_PATH + data + "/DATA/" + tpm_rx + "/" + pol + "/SPECTROGRAMS* aavs@cerberus.mwa128t.org:/home/aavs/mattana/" + data + "/SPECTROGRAM/" + tpm_rx + "/" + pol + "/")
			lista_bands = os.listdir(DEF_PATH + SPG_DIR)
			lista_bands = [x for x in lista_bands if x.startswith('SPECTROGRAM')]
			for band in lista_bands:
				os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/SPECTROGRAM/" + band + "\"")
				for tpm_rx in TPM_INPUTS:
					os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/SPECTROGRAM/" + band + "/" + tpm_rx + "\"")
					for pol in POLS:
						os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/SPECTROGRAM/" + band + "/" + tpm_rx + "/" + pol + "\"")
						os.system("scp " + DEF_PATH + SPG_DIR + band + "/" + tpm_rx + "/" + pol + "/*" + data + "* aavs@cerberus.mwa128t.org:/home/aavs/mattana/SPECTROGRAM/" + band + "/" + tpm_rx + "/" + pol + "/")
			os.system("~/work/LowBridging/power_plot.py --ymin=-50 --ymax=-30 --all --dir=" + DEF_PATH + data + "/POWER/CH-160/")
			os.system("scp " + DEF_PATH + data + "/POWER/CH-160/* aavs@cerberus.mwa128t.org:/home/aavs/mattana/" + data + "/POWER/CH-160/")

		print "\nSuccessfully executed!!\n"
	else:
		print "\nMalformed input data or no existing directory " + DEF_PATH + data + "\n"
