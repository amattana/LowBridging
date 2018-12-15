#!/usr/bin/env python

'''

  Transfer triggered data from AAVS1-server to CERBERUS
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
if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--data", dest="data", default="", help="Date in format YYYY-MM-DD")
	#parser.add_option("-d", "--debug", action='store_true', dest="debug", default=False, help="If set the program runs in debug mode")

	(options, args) = parser.parse_args()

	if options.data == "":
		print "\nInput missing (date)!\n\nExiting....\n"
		exit(0)
	else:
		data = options.data

	if os.path.isdir(DEF_PATH + data):
		#os.system("cd " + DEF_PATH + data)
		print "\nGenerating Directories on Cerberus..."
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "\"")
		os.system("ssh aavs@10.128.0.1 \"mkdir -p /home/aavs/mattana/" + data + "/TRIGGER" + "\"")

		print "\nCopying triggered data..."
		lista = sorted(glob.glob(DEF_PATH + data + "/TRIGGER/RX-01_EDA2/Pol-X/*png"))
		for l in lista:
			os.system("scp " + DEF_PATH + data + "/IMG/PLOT-A/*" + l[-10:-4] + "* aavs@cerberus.mwa128t.org:/home/aavs/mattana/" + data + "/TRIGGER/")
			os.system("scp " + DEF_PATH + data + "/IMG/PLOT-B/*" + l[-10:-4] + "* aavs@cerberus.mwa128t.org:/home/aavs/mattana/" + data + "/TRIGGER/")
		print "\nSuccessfully executed!!\n"
	else:
		print "\nMalformed input data or no existing directory " + DEF_PATH + data + "\n"
