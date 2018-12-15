#!/usr/bin/env python

'''

	AAVS2 Low Bridging Phase-0

	Generate pictures to create a movie of the spectra frames
	acquired with the Agilent Spectrum Analizer of the
	the SKALA-4 and MWA antennas on the MRO site

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2018, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import datetime, os, sys, glob
from matplotlib import pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import pytz, easygui
from optparse import OptionParser

from tqdm import tqdm

from math import log10


def mw_to_dbm(mW):
	"""This function converts a power given in mW to a power given in dBm."""
	return 10. * log10(mW)


def dbm_to_mw(dBm):
	"""This function converts a power given in dBm to a power given in mW."""
	return 10 ** ((dBm) / 10.)


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--debug", action='store_true',
					  dest="debug",
					  default=False,
					  help="If set the program runs in debug mode")

	parser.add_option("-b", "--band",
					  dest="band",
					  default="",
					  help="If given limit the display to the selected band (i.e.: 400-416)")

	parser.add_option("-s", "--skip",
					  dest="skip",
					  default=0,
					  help="Jump to n file")

	parser.add_option("-p", "--prefix",
					  dest="prefix",
					  default="",
					  help="Project prefix added at the beginning of the output filename")

	(options, args) = parser.parse_args()

	wday = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
	datafile = easygui.fileopenbox(msg='Please select the Spectrum Analyzer CVS file', default="/data/data_2/")
	if datafile == None:
		print "\nNo file selected! Exiting...\n"
		exit(0)
	datapath = datafile[:datafile.rfind("/")]
	datafiles = sorted(glob.glob(datapath + "/*.CSV"))
	#print datapath, len(datafiles)

	# print datafile
	with open(datafile) as f:
		fdata = f.readlines()
	datafile = datafile.split("/")[-1][:-4]
	if fdata[59].split(",")[0] == "Total Frames":
		nspectra = int(fdata[59].split(",")[1])
	else:
		print "The given file is not a valid SA CSV file!"
		exit(0)

	if not options.band == "":
		b_start = int(options.band.split("-")[0])
		b_stop = int(options.band.split("-")[1])
	else:
		b_stop = int(float(fdata[12].split(",")[1]) / 1000000)
		b_start = int(float(fdata[11].split(",")[1]) / 1000000)
	# bw = b_stop - b_start

	bw = int(fdata[9].split(",")[1])

	print "\n-----------------------------------------"
	print "Start Frequency:\t", b_start, "MHz"
	print "Stop Frequency:\t\t", b_stop, "MHz"
	print "Number of Points:\t", bw
	print "Resolution BW\t\t", float(fdata[16].split(",")[1]) / 1000, "KHz"
	# print "Video BW\t\t", float(fdata[17].split(",")[1])/1000, "KHz"
	print "Number of Spectra:\t", nspectra
	print "Unit:\t\t\t", fdata[9].split(",")[1][:-1]
	print "-----------------------------------------\n"

	bw_step = bw / 10.
	ytick = np.array(range(11)) * bw_step
	yticklab = [str(int(j + b_start)) for j in ytick]

	#xax = np.linspace(b_start, b_stop, bw)
	xtick = np.array(range(21)) * 100/20
	#xticklab = [str(int(j + b_start)) for j in xtick]
	xticklab = ["0","5","10","15","20","25","30","35","40","45","50","55","60","65","70","75","80","85","90","95","100"]

	gs = gridspec.GridSpec(2, 1, height_ratios=[6, 3])
	fig = plt.figure(figsize=(10, 7), facecolor='w')

	ax1 = fig.add_subplot(gs[0])
	ax2 = fig.add_subplot(gs[1])

	plt.ion()

	skip = int(options.skip)
	# H_per_day = 24
	# MIN_per_hour = 60
	# MEAS_per_min = 6
	# # pst = pytz.timezone('Europe/Rome') #  da verificare per Australia
	#
	# tot_power = np.zeros(H_per_day * MIN_per_hour * MEAS_per_min)
	# tot_power[:] = np.nan
	# cnt = 0
	#
	# spgramma = np.empty((3600,1001,))
	spgramma = np.empty((60 * 15, bw - 5,))
	spgramma[:] = np.nan
	#print len(spgramma)

	spettri = fdata[62::2]
	aux = fdata[61::2]

	# questa cagata va fatta per evitare che il primo esca male...
	s = 0
	dati = spettri[s].split(",")
	t = datetime.datetime.strptime(aux[s].split(",")[3], "%H:%M:%S %m.%d.%Y")
	# t = datetime.datetime.utcfromtimestamp(float(dati[0])) - datetime.timedelta(
	#	24107)  # +datetime.timedelta(0, 3600*2)

	# solo se in UTC allora posso localizzare
	# t = pytz.UTC.localize(t)
	# t = t.astimezone(pst)
	# t = t.replace(tzinfo=None)

	day = datetime.datetime(t.year, t.month, t.day)

	# Questo valeva in SAD dove ultimo elemento era il total power
	# if float(dati[-1]) > -50:
	# 	tot_power[(t - day).seconds / 10] = float(dati[-1])
	# else:
	# 	tot_power[(t - day).seconds / 10] = None

	# spettro = np.array(dati[1:-1])

	# se si vuole tagliare la banda
	# spettro = np.array(dati[1 + b_start:1 + b_stop])
	spettro = np.array(dati[:-1]).astype(np.float)
	max_hold = np.array(spettro)
	min_hold = np.array(spettro)

	last, spgramma = spgramma[0], spgramma[1:]
	if np.mean(spettro) < -100:
		spettro = np.empty(bw)
		spettro[:] = np.nan
		spgramma = np.concatenate((spgramma, [spettro[5:]]), axis=0)
	else:
		#spettro = np.zeros(bw)+
		#spgramma = np.concatenate((spgramma, [spettro[5:].astype(np.float)]), axis=0)
		spgramma = np.concatenate((spgramma, [spettro[5:].astype(np.float)]), axis=0)

	# print spgramma,len(spgramma)
	ax1.cla()
	# if len(spgramma)>1:
	ax1.imshow(spgramma, interpolation='none', aspect='auto', extent=[b_start+5, b_stop, 15, 0])
	ax1.set_title(" Spectrogram ")
	ax1.set_ylabel("Time (minutes)")
	ax1.set_xlabel('MHz')

	ax2.cla()
	ax2.plot(np.linspace(b_start, b_stop, bw), spettro, color='b')
	ax2.set_ylim([-120, 0])
	ax2.set_xlim([b_start + 1, b_stop])
	title = datetime.datetime.strftime(t, "%Y/%m/%d %H:%M:%S")  # +"  -  Timestamp:"+str(float(dati[0]))+"  -  Total Power: "+str(float(dati[-1]))
	ax2.set_title(title)
	#title = datetime.datetime.strftime(t, "%Y%m%d_%H%M%S")
	ax2.grid(True)
	ax2.set_xlabel('MHz')
	ax2.set_ylabel("dBm")

	plt.tight_layout()

	if not os.path.isdir(datapath + "/PNG"):
		os.makedirs(datapath + "/PNG")
	pngname = datapath + "/PNG/"
	if not options.prefix == "":
		pngname += options.prefix + "_"
	pngname += datetime.datetime.strftime(t, "%Y-%m-%d_%H%M%S") + ".png"
	fig.savefig(pngname)
	# sys.stdout.flush()

	print "\nGenerating pictures...\n"

	for datafile in datafiles:
		skip = skip - 1
		if skip < 0:
			with open(datafile) as f:
				fdata = f.readlines()
			spettri = fdata[62::2]
			aux = fdata[61::2]
			datafile = datafile.split("/")[-1][:-4]

			# questa cagata va fatta per evitare che il primo esca male...
			s = 0
			dati = spettri[s].split(",")
			t = datetime.datetime.strptime(aux[s].split(",")[3], "%H:%M:%S %m.%d.%Y")

			if fdata[59].split(",")[0] == "Total Frames":
				nspectra = int(fdata[59].split(",")[1])
				print "\nProcessing file: ", datafile
			else:
				print "The given file is not a valid SA CSV file!"
				exit(0)

			counter = 0
			for s in tqdm(range(nspectra)):
				# se mezzanotte resetto il grafico
				# if l[-6:-4] == "00":
				# 	tot_power = np.zeros(H_per_day * MIN_per_hour * MEAS_per_min)
				# 	tot_power[:] = np.nan
				# 	cnt = 0
				# 	spgramma = np.empty((360 * 24, bw,))
				# 	# spgramma = np.empty((360*24,1001,))
				# 	spgramma[:] = np.nan
				#print "S:", s, "\n",datetime.datetime.strptime(aux[s].split(",")[3], "%H:%M:%S %m.%d.%Y")
				dati = spettri[s].split(",")
				t = datetime.datetime.strptime(aux[s].split(",")[3], "%H:%M:%S %m.%d.%Y")
				day = datetime.datetime(t.year, t.month, t.day)

				# se si vuole tagliare la banda
				# spettro = np.array(dati[1 + b_start:1 + b_stop])
				spettro = np.array(dati[:-1]).astype(np.float)
				nmax_hold = np.maximum(spettro.astype(np.float), max_hold.astype(np.float))
				max_hold = nmax_hold
				nmin_hold = np.minimum(spettro.astype(np.float), min_hold.astype(np.float))
				min_hold = nmin_hold

				last, spgramma = spgramma[0], spgramma[1:]
				if np.mean(spettro) < -100:
					spettro = np.empty(bw)
					spettro[:] = np.nan
					spgramma = np.concatenate((spgramma, [spettro[5:]]), axis=0)
				else:
					#spettro = np.zeros(bw) + counter
					counter = counter + 1
					#print counter
					spgramma = np.concatenate((spgramma, [spettro[5:].astype(np.float)]), axis=0)

		else:
			print "Skipping", datafile

		ax1.cla()
		ax1.imshow(spgramma, interpolation='none', aspect='auto', extent=[b_start +5, b_stop, 15, 0], cmap='jet', clim=(-80, -40))
		#cbar = fig.colorbar(cax, ticks=[-1, 0, 1])
		#cbar.ax1.set_yticklabels(['< -1', '0', '> 1'])  # vertically oriented colorbar
		ax1.set_title(" Spectrogram ")
		ax1.set_ylabel("Time (minutes)")
		ax1.set_xlabel('MHz')

		ax2.cla()
		ax2.plot(np.linspace(b_start, b_stop, bw), spettro, color="b")
		ax2.plot(np.linspace(b_start, b_stop, bw), max_hold, color="r")
		ax2.plot(np.linspace(b_start, b_stop, bw), min_hold, color="g")
		ax2.set_ylim([-120, 0])
		#ax2.set_xticks(xtick)
		#ax2.set_xticklabels(xticklab, fontsize=10)
		ax2.set_xlim([b_start + 1, b_stop])

		title = datetime.datetime.strftime(t, "%Y/%m/%d %H:%M:%S")
		ax2.set_title(title)
		#title = datetime.datetime.strftime(t, "%Y%m%d_%H%M%S")
		ax2.grid(True)
		ax2.set_xlabel('MHz')
		ax2.set_ylabel("dBm")

		plt.tight_layout()

		pngname = datapath + "/PNG/"
		if not options.prefix == "":
			pngname += options.prefix + "_"
		pngname += datetime.datetime.strftime(t, "%Y-%m-%d_%H%M%S") + ".png"
		fig.savefig(pngname)

	print  "\n\n-----------------------------------------\n\n# Generating video....\n\n"
	if not os.path.isdir(datapath + "/VIDEO"):
		os.makedirs(datapath + "/VIDEO")
	videoname = datapath + "/VIDEO/" + datafile
	if not options.prefix == "":
		videoname += "_" + options.prefix
	videoname += ".mp4"
	cmd = "ffmpeg -f image2  -i " + datapath + "/PNG/" + "%*.png  -vcodec libx264 " + videoname
	print "\nExecuting:", cmd, "\n"
	os.system(cmd)

	print "\nExecution terminated!\n"
