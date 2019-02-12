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
from scipy.interpolate import make_interp_spline, BSpline

def weighted_moving_average(x,y,step_size=0.05,width=1):
    bin_centers  = np.arange(np.min(x),np.max(x)-0.5*step_size,step_size)+0.5*step_size
    bin_avg = np.zeros(len(bin_centers))

    #We're going to weight with a Gaussian function
    def gaussian(x,amp=1,mean=0,sigma=1):
        return amp*np.exp(-(x-mean)**2/(2*sigma**2))

    for index in range(0,len(bin_centers)):
        bin_center = bin_centers[index]
        weights = gaussian(x,mean=bin_center,sigma=width)
        bin_avg[index] = np.average(y,weights=weights)

    return (bin_centers,bin_avg)

BASE_DIR = "/data/data_2/2018-11-LOW-BRIDGING/"
POWER_DIR = "POWER/"

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

	parser.add_option("--ymin",
					  dest="ymin",
					  default=-20,
					  help="Y Min for range of plot")

	parser.add_option("--ymax",
					  dest="ymax",
					  default=10,
					  help="Y Max for range of plot")

	parser.add_option("--sigma",
					  dest="sigma",
					  default=10,
					  help="Moving Average Sigma (def: 10)")

	parser.add_option("--smooth", action='store_true',
					  dest="smooth",
					  default=False,
					  help="Smooth the raw data series with moving average")

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

	#wday = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"] # IT
	wday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]  # EN

	# lista = sorted(glob.glob("data/data_2/*.txt"))
	if options.dir == "":
		datafile = easygui.fileopenbox(msg='Please select the CVS file', default="/data/data_2/2018-11-LOW-BRIDGING/")
		if datafile == None:
			print "\nNo file selected, exiting...\n"
			exit(0)
	else:
		datafile = options.dir
		if not datafile[-1] == "/":
			datafile = datafile[:] + "/"
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
		ax[i].set_ylim([int(options.ymin), int(options.ymax)])
		ax[i].set_xlabel("Day Hours")
		ax[i].set_ylabel("dBm")

	# ax[0].set_title("Weekly Total Power (dBm/hours)")
	ax[0].set_title("Total Power in dBm")
	plt.tight_layout()

	H_per_day = 24
	MIN_per_hour = 60
	MEAS_per_min = 60
	# pst = pytz.timezone('Europe/Rome')

	#x = np.zeros(H_per_day * MIN_per_hour * MEAS_per_min)
	#x += H_per_day * MIN_per_hour * MEAS_per_min
	#tot_power = np.zeros(H_per_day * MIN_per_hour * MEAS_per_min)
	#tot_power += -100

	for counter, df in enumerate(datafiles):
		antname = df[6:-4].replace("_", " ")
		with open(datapath + df) as f:
			data = f.readlines()
		# print "Generating images for file: ",l

		tot_power = []
		x = []
		cnt = 0
		for d in data:

			dati = d.replace("\n", "").replace("  ", "\t").split("\t")
			t = datetime.datetime.strptime(dati[1]+" "+dati[2],"%Y/%m/%d %H:%M:%S")
			# t = pytz.UTC.localize(t)
			# t = t.astimezone(pst)
			day = datetime.datetime(t.year, t.month, t.day)
			# t = t.replace(tzinfo=None)

			x += [(t - day).seconds]
			tot_power += [float(dati[3])]

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
		#ax[weekday].plot(x[:cnt], tot_power[:cnt], label=antname)

		if options.smooth:
			T = np.array(x)
			xnew = np.linspace(T.min(),T.max(),1000)
			spl = make_interp_spline(T, tot_power, k=3) #BSpline object
			power_smooth = spl(xnew)
			#ax[weekday].plot(xnew, power_smooth, label=antname)

			sigma = int(options.sigma)
			y_gau = np.zeros(len(power_smooth))
			gau_x = np.linspace(-2.7*sigma, 2.7*sigma, 6*sigma)
			gaussian_func = lambda z, sigma: 1/np.sqrt(2*np.pi*sigma**2) * np.exp(-(z**2)/(2*sigma**2))
			gau_mask = gaussian_func(gau_x, sigma)
			y_gau = np.convolve(power_smooth, gau_mask, 'same')
			y_gau = y_gau[3*sigma:-5*sigma]

		else:
			y_gau = tot_power


		ax[weekday].plot(np.linspace(0,len(tot_power),len(y_gau)), y_gau, label=antname)

		#print len(tot_power)
		#ax[weekday].plot(x, tot_power, label=antname)
		if counter == 0:
			ax[weekday].grid(True)
			#ax[weekday].set_xticks([0, 10800, 21600, 32400, 43200, 54000, 64800, 75600, 86400])
			ax[weekday].set_xticks(np.linspace(0,len(tot_power),9))
			ax[weekday].set_xticklabels(["0", "3", "6", "9", "12", "15", "18", "21", "24"])
			ax[weekday].set_xlim([0, len(tot_power)])
			ax[weekday].set_ylim([int(options.ymin), int(options.ymax)])
			ax[weekday].set_yticks(np.arange(int(options.ymin), int(options.ymax) + 1, 2))
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
		titolo = antname + "   Total Power"
	else:
		titolo = "Total Power"
	if not datapath.split("/")[-2] == "POWER":
		titolo += " of Frequency Channel " + datapath.split("/")[-2].split("-")[1] + " MHz"
	ax[0].set_title(titolo)
	ax[0].legend(fontsize=10)
	plt.tight_layout(rect=[0, 0.03, 1, 0.95])

	#plt.show()
	# weeknumber = "%02d" % (day.isocalendar()[1])
	# if not os.path.isdir("data/weekly"):
	#    os.makedirs("data/weekly")

	fname = BASE_DIR + POWER_DIR
	if not datapath.split("/")[-2] == "POWER":
		fname += "SINGLE_CHANNEL"
	else:
		fname += "FULL_BAND"
	if not os.path.exists(fname):
		os.makedirs(fname)
	if options.smooth:
		fname += "/SMOOTHED"
		if not os.path.exists(fname):
			os.makedirs(fname)
	fname += "/" + giorno + datapath[datapath.index("POWER"):-1].replace("/","_")+".png"
	fig.savefig(fname)
	if not options.silent:
		print "\nSaved image: " + fname
		#print "\nExecution terminated!\n"
