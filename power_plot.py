#!/usr/bin/env python

'''

  SKA Low Bridging Phase-0, Plot the SKALA-4 and EDA2 total power on the MRO field

  Inputs: a power file acquired with tpm_dump.py

  Outputs: Plots

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2018, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import datetime, glob, os, easygui
from matplotlib import pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import pytz
from optparse import OptionParser

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-w", "--week", action='store_true',
					  dest="week",
					  default=False,
					  help="Plot a week graph")

	parser.add_option("-a", "--all", action='store_true',
					  dest="all",
					  default=False,
					  help="Plot all the antenna in the same plot")

	parser.add_option("--silent", action='store_true',
					  dest="silent",
					  default=False,
					  help="Do not print any messages")

	parser.add_option("-d", "--dir",
					  dest="dir",
					  default="",
					  help="Directory to be processed")

	# parser.add_option("-b", "--band",
	# 				  dest="band",
	# 				  default="",
	# 				  help="If given limit the display to the selected band (i.e.: 400-416)")
	#
	# parser.add_option("-s", "--skip",
	# 				  dest="skip",
	# 				  default=0,
	# 				  help="Jump to n file")
	#
	# parser.add_option("-p", "--prefix",
	# 				  dest="prefix",
	# 				  default="AAVS2",
	# 				  help="Project prefix added at the beginning of the output filename")

	(options, args) = parser.parse_args()

	wday = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]

	# lista = sorted(glob.glob("data/data_2/*.txt"))
	if options.dir == "":
		datafile = easygui.fileopenbox(msg='Please select the CVS file', default="/data/data_2/2018-11-LOW-BRIDGING/")
		if datafile == None:
			print "\nNo file selected, exiting...\n"
			exit(0)
	else:
		datafile = "/data/data_2/2018-11-LOW-BRIDGING/" + options.dir + "/POWER/"
		#print "\n", datafile, "\n", sorted(glob.glob(datafile + "*.csv"))
		datafile = sorted(glob.glob(datafile + "*.csv"))[0]
		#print "\n\n", datafile

	datapath = datafile[:datafile.rfind("/") + 1]
	for i in datapath.split("/"):
		#print i
		try:
			giorno = datetime.datetime.strptime(i, "%Y-%m-%d")
		except:
			pass
	giorno = giorno.strftime("%Y-%m-%d_")

	if options.all:
		datafiles = sorted(glob.glob(datapath + "*.csv"))
	else:
		datafiles = [datafile]
	for d in xrange(len(datafiles)):
		datafiles[d] = datafiles[d][datafiles[d].rfind("/") + 1:]
	datafile = datafile[datafile.rfind("/") + 1:]
	antname = datafile[0][6:-4].replace("_", " ")
	# datafiles = sorted(glob.glob(datapath + "/*.CSV"))
	#print datapath, datafile  # , len(datafiles)

	if options.week:
		ax = [[]]
		ax = ax * 7
		dx = [[]]
		dx = dx * 7
		gs = gridspec.GridSpec(7, 2, width_ratios=[1, 10], height_ratios=[1, 1, 1, 1, 1, 1, 1])
		fig = plt.figure(figsize=(9, 12), facecolor='w')
	else:
		ax = [[]]
		dx = [[]]
		gs = gridspec.GridSpec(1, 2, width_ratios=[1, 10], height_ratios=[1])
		fig = plt.figure(figsize=(9, 6), facecolor='w')

	#plt.ion()
	plt.ioff()

	for i in xrange(len(ax)):
		dx[i] = fig.add_subplot(gs[i * 2])
		dx[i].plot(range(10), color='w')
		dx[i].set_axis_off()
		if options.week:
			dx[i].annotate(wday[i], (-11, -10), fontsize=16)
		# dx[i].annotate("16/04/2017",(1,2.5),fontsize=10)

		ax[i] = fig.add_subplot(gs[i * 2 + 1])
		ax[i].grid(True)
		ax[i].set_xticks([0, 10800, 21600, 32400, 43200, 54000, 64800, 75600, 86400])
		ax[i].set_xticklabels(["0", "3", "6", "9", "12", "15", "18", "21", "24"])
		ax[i].set_xlim([0, 86400])
		ax[i].set_ylim([-25, 15])
		ax[i].set_xlabel("Day Hours")
		ax[i].set_ylabel("dBm")

	# ax[0].set_title("Weekly Total Power (dBm/hours)")
	ax[0].set_title("Total Power in dBm")
	plt.tight_layout()

	H_per_day = 24
	MIN_per_hour = 60
	MEAS_per_min = 60
	# pst = pytz.timezone('Europe/Rome')

	x = np.zeros(H_per_day * MIN_per_hour * MEAS_per_min)
	x += H_per_day * MIN_per_hour * MEAS_per_min
	tot_power = np.zeros(H_per_day * MIN_per_hour * MEAS_per_min)
	tot_power -= 100
	cnt = 0

	for counter, df in enumerate(datafiles):
		antname = df[6:-4].replace("_", " ")
		with open(datapath + df) as f:
			data = f.readlines()
		# print "Generating images for file: ",l

		cnt = 0
		for d in data:

			dati = d.replace("\n", "").replace("  ", "\t").split("\t")
			t = datetime.datetime.utcfromtimestamp(float(dati[0]))
			# t = pytz.UTC.localize(t)
			# t = t.astimezone(pst)
			day = datetime.datetime(t.year, t.month, t.day)
			# t = t.replace(tzinfo=None)

			x[cnt] = (t - day).seconds
			if float(dati[-1]) > -50:
				tot_power[cnt] = float(dati[-1])
			else:
				tot_power[cnt] = None

			cnt = cnt + 1

		if options.week:
			weekday = t.weekday()
		else:
			weekday = 0

		if counter == 0:
			dx[weekday].cla()
			dx[weekday].plot(np.array(range(50)) - 40, color='w')
			dx[weekday].set_axis_off()
			dx[weekday].annotate(wday[t.weekday()], (0, -25), fontsize=16)
			dx[weekday].annotate(datetime.datetime.strftime(t, "%d/%m/%Y"), (0, -27), fontsize=10)

		# ax[weekday].cla()
		ax[weekday].plot(x[:cnt], tot_power[:cnt], label=antname)
		if counter == 0:
			ax[weekday].grid(True)
			ax[weekday].set_xticks([0, 10800, 21600, 32400, 43200, 54000, 64800, 75600, 86400])
			ax[weekday].set_xticklabels(["0", "3", "6", "9", "12", "15", "18", "21", "24"])
			ax[weekday].set_xlim([0, 86400])
			ax[weekday].set_ylim([-80, -30])
			ax[weekday].set_xlabel("Day Hours (UTC)")
			ax[weekday].set_ylabel("dBm")


			# if weekday == 6:
			#     ax[0].set_title("Weekly Total Power (dBm/hours)")
			#     plt.tight_layout()
			#     weeknumber = "%02d" % (day.isocalendar()[1])
			#     if not os.path.isdir("data/weekly"):
			#         os.makedirs("data/weekly")
			#     fig.savefig("data/weekly/SAD_RFI_2018_WEEK-" + weeknumber + ".png")
			#     print "\n\nSaved week image: " + "data/weekly/SAD_RFI_2018_WEEK-" + weeknumber + ".png\n"
			#
			#     for i in xrange(len(ax)):
			#         dx[i].cla()
			#         dx[i].plot(range(10), color='w')
			#         dx[i].set_axis_off()
			#         #dx[i].annotate(wday[i], (1, 4.5), fontsize=16)
			#
			#         ax[i].cla()
			#         ax[i].grid(True)
			#         #ax[i].set_xticks([0, 1080, 2160, 3240, 4320, 5400, 6480, 7560, 8640])
			#         #ax[i].set_xticklabels(["0", "3", "6", "9", "12", "15", "18", "21", "24"])
			#         #ax[i].set_xlim([0, 8640])
			#         #ax[i].set_ylim([-25, -5])

		# ax[0].set_title("Weekly Total Power (dBm/hours)")
	if len(datafiles) == 1:
		ax[0].set_title(antname + "   Total Power")
	else:
		ax[0].set_title("Total Power")
	ax[0].legend()
	plt.tight_layout(rect=[0, 0.03, 1, 0.95])

	#plt.show()
	# weeknumber = "%02d" % (day.isocalendar()[1])
	# if not os.path.isdir("data/weekly"):
	#    os.makedirs("data/weekly")
	fig.savefig(datapath + giorno + "POWER.png")
	if not options.silent:
		print "\n\nSaved image: " + datapath + giorno + "POWER.png\n"
		print "\nExecution terminated!\n"
