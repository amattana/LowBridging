#!/usr/bin/env python

'''

   TPM Spectra Viever 

   Used to plot spectra saved using tpm_dump.py

'''

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

from matplotlib import pyplot as plt
import struct, os, easygui, glob
from optparse import OptionParser
import numpy as np
# from tpm_utils import *
import matplotlib.gridspec as gridspec
import datetime, time
from tqdm import tqdm

BASE_DIR = "/data/data_2/2018-11-LOW-BRIDGING/"
SPG_DIR = "SPECTROGRAMS_BAND_"


def calcSpectra(vett):
	window = np.hanning(len(vett))
	spettro = np.fft.rfft(vett * window)
	N = len(spettro)
	acf = 2  # amplitude correction factor
	spettro[:] = abs((acf * spettro) / N)
	return (np.real(spettro))


def calcolaspettro(dati, nsamples=131072):
	n = nsamples  # split and average number, from 128k to 16 of 8k # aavs1 federico
	sp = [dati[x:x + n] for x in xrange(0, len(dati), n)]
	mediato = np.zeros(len(calcSpectra(sp[0])))
	for k in sp:
		singolo = calcSpectra(k)
		mediato[:] += singolo
	# singoli[:] /= 16 # originale
	mediato[:] /= (2 ** 17 / nsamples)  # federico
	with np.errstate(divide='ignore', invalid='ignore'):
		mediato[:] = 20 * np.log10(mediato / 127.0)
	return mediato

def closest(serie, num):
	return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z-num)))

def dB2Linear(valueIndB):
    """
    Convert input from dB to linear scale.
    Parameters
    ----------
    valueIndB : float | np.ndarray
        Value in dB
    Returns
    -------
    valueInLinear : float | np.ndarray
        Value in Linear scale.
    Examples
    --------
    #>>> dB2Linear(30)
    1000.0
    """
    return pow(10, valueIndB / 10.0)


def linear2dB(valueInLinear):
    """
    Convert input from linear to dB scale.
    Parameters
    ----------
    valueInLinear : float | np.ndarray
        Value in Linear scale.
    Returns
    -------
    valueIndB : float | np.ndarray
        Value in dB scale.
    Examples
    --------
    #>>> linear2dB(1000)
    30.0
    """
    return 10.0 * np.log10(valueInLinear)


def dBm2Linear(valueIndBm):
    """
    Convert input from dBm to linear scale.
    Parameters
    ----------
    valueIndBm : float | np.ndarray
        Value in dBm.
    Returns
    -------
    valueInLinear : float | np.ndarray
        Value in linear scale.
    Examples
    --------
    #>>> dBm2Linear(60)
    1000.0
    """
    return dB2Linear(valueIndBm) / 1000.


def linear2dBm(valueInLinear):
    """
    Convert input from linear to dBm scale.
    Parameters
    ----------
    valueInLinear : float | np.ndarray
        Value in Linear scale
    Returns
    -------
    valueIndBm : float | np.ndarray
        Value in dBm.
    Examples
    --------
    #>>> linear2dBm(1000)
    60.0
    """
    return linear2dB(valueInLinear * 1000.)



if __name__ == "__main__":
	parser = OptionParser()

	parser.add_option("--file",
					  dest="infile",
					  default="",
					  help="Input Time Domain Data file '.tdd' saved using tpm_dump.py")

	parser.add_option("--average",
					  dest="average",
					  default=16,
					  help="Number of time domain segments to be averaged. 1 means NO average")

	parser.add_option("--dir",
					  dest="dir",
					  default="",
					  help="Directory containing tdd files")

	parser.add_option("--raw", action="store_true",
					  dest="raw",
					  default=False,
					  help="Plot also ADC Raw data")

	parser.add_option("--recursive", action="store_true",
					  dest="recursive",
					  default=False,
					  help="Plot recursively all the directory files, sorted by name")

	parser.add_option("--water", action="store_true",
					  dest="water",
					  default=False,
					  help="Plot waterfall, requires recursive mode")

	parser.add_option("--power", action="store_true",
					  dest="power",
					  default=False,
					  help="Plot Power of a channel, requires recursive mode")

	parser.add_option("--channel",
					  dest="channel",
					  default=160,
					  help="Frequency channel in MHz to be used to plot the power")

	parser.add_option("--start-freq",
					  dest="startfreq",
					  default=0, type="int",
					  help="Start Frequency for Waterfall")

	parser.add_option("--stop-freq",
					  dest="stopfreq",
					  default=400, type="int",
					  help="Stop Frequency for Waterfall")


	(options, args) = parser.parse_args()

	plt.ioff()

	nsamples = 2 ** 17 / int(options.average)

	if not options.dir == "":
		datapath = options.dir
		#print "\nListing directory:", datapath
		datafiles = sorted(glob.glob(datapath + "/*.tdd"))
		#print "Found "+str(len(datafiles))+" \"tdd\" files.\n"
		if len(datafiles) > 0:
			fname = datafiles[0]
		else:
			print "No tdd files found in directory: " + datapath + "\nExiting..."
			exit(0)
	else:
		fname = options.infile

	if fname == "":
		fname = easygui.fileopenbox(title="Choose a tdd file", default="/data/data_2/2018-11-LOW-BRIDGING/",
									filetypes="tdd")
	if not os.path.isfile(fname):
		print "Invalid file! \n"
		exit(0)

	if options.recursive:
		datapath = fname[:fname.rfind("/")]
		print "\nListing directory:", datapath
		datafiles = sorted(glob.glob(datapath + "/*.tdd"))
		print "Found "+str(len(datafiles))+" \"tdd\" files.\n"

	if int(options.average) < 1:
		print "Average value must be greater than zero!"
		exit(0)


	if options.water or options.power:
		if not options.recursive:
			print "Recursive Flag parameter Required!"
			exit(0)
		else:
			gs = gridspec.GridSpec(2, 1, height_ratios=[6, 3])
			fig = plt.figure(figsize=(10, 7), facecolor='w')

			ax1 = fig.add_subplot(gs[0])
			ax2 = fig.add_subplot(gs[1])

			bw = nsamples / 2
			asse_x = np.linspace(0, 400, bw)
			xmin = closest(asse_x,options.startfreq)
			xmax = closest(asse_x,options.stopfreq)

			spgramma = np.empty((1000, xmax-xmin+1,))
			spgramma[:] = np.nan
			dayspgramma = np.empty((10, xmax-xmin+1,))
			dayspgramma[:] = np.nan

			SPG_DIR += str("%03d" % int(options.startfreq)) + "-" + str("%03d" % int(options.stopfreq))

	else:
		if options.raw:
			gs = gridspec.GridSpec(2, 1, height_ratios=[2, 6])
			fig = plt.figure(figsize=(10, 7), facecolor='w')
			ax1 = fig.add_subplot(gs[0])
			ax2 = fig.add_subplot(gs[1])
		else:
			gs = gridspec.GridSpec(1, 1)
			fig = plt.figure(figsize=(10, 7), facecolor='w')
			ax2 = fig.add_subplot(gs[0])

	if ((not options.water) and (not options.power)):

		print "Opening file: ", fname
		with open(fname, "r") as f:
			a = f.read()
		l = struct.unpack(">d", a[0:8])[0]
		data = struct.unpack(">" + str(int(l)) + "b", a[8:])
		singolo = calcolaspettro(data, nsamples)

		adu_rms = np.sqrt(np.mean(np.power(data, 2), 0))
		volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
		power_adc = 10 * np.log10(np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
		power_rf = power_adc + 12  # single ended to diff net loose 12 dBm

		if options.raw:
			ax1.plot(data)
			ax1.set_ylim(-150, 150)
			ax1.set_xlim(0, len(data) - 1)
			ax1.set_xlabel("ADC Samples")
			ax1.set_ylabel("A/D Unit")
			ax1.grid(True)
			ax1.set_title("Time Domain Data - " + str(len(data)) + " ADC Samples (8bit)")

		if options.water:
			ax1.plot(range(100))

		ax2.plot(np.linspace(0, 400, len(singolo)), singolo)
		ax2.set_xlim(0, 400)
		ax2.set_ylim(-100, 0)
		ax2.set_xlabel('MHz')
		ax2.set_ylabel("dBm")
		ax2.set_title("Power Spectrum", fontsize=14)
		ax2.annotate("RF Power: " + "%3.1f" % (power_rf) + " dBm", (10, -15), fontsize=16)
		ax2.annotate("Averaged Spectra: " + str(options.average), (280, -15), fontsize=16)
		ax2.grid(True)

		# ax3.cla()
		# ax3.plot(range(100),color='w')
		# ax3.set_axis_off()
		# ax3.annotate(fname.split("/")[-1][:-4], (3,70), fontsize=14)
		# ax3.annotate("RF Power: " + "%3.1f" % (power_rf) + " dBm", (3, 30), fontsize=16)
		plt.title(fname.split("/")[-1][:-4].replace("_", "  "), fontsize=18)

		plt.tight_layout()

		# plt.savefig(d+"images/"+data_path.replace("/","_")+"avg.png")
		# plt.clf()
		plt.show()

		# exit()

	else:

		fname = datafiles[0]
		plt.ion()
		if not os.path.isdir(datapath + "/" + SPG_DIR):
			os.makedirs(datapath + "/" + SPG_DIR)
		RX_DIR = fname.split("/")[-3] + "/"
		POL_DIR = fname.split("/")[-2] + "/"

		if options.power:
			if not os.path.isdir(datapath+"/../../../POWER/CH-"+str(int(options.channel))):
				os.makedirs(datapath+"/../../../POWER/CH-"+str(int(options.channel)))
			pfile = open(datapath+"/../../../POWER/CH-"+str(int(options.channel))+"/POWER_CH-"+str(int(options.channel))+"_"+RX_DIR[:-1]+"_"+POL_DIR[:-1]+".csv", "w")

		with open(fname, "r") as f:
			a = f.read()
		l = struct.unpack(">d", a[0:8])[0]
		data = struct.unpack(">" + str(int(l)) + "b", a[8:])
		spettro = calcolaspettro(data, nsamples)
		max_hold = np.array(spettro)
		min_hold = np.array(spettro)
		ora_inizio = datetime.datetime.strptime(fname.split("/")[-1][-21:-4], "%Y-%m-%d_%H%M%S")

		if ((options.startfreq == 0) and (options.stopfreq == 400)):
			if "EDA2" in fname:
				wclim = (-70, -40)
				print "Setting waterfall colors for EDA2"
			else:
				wclim = (-80, -30)
				print "Setting waterfall colors for SKALA-4"
		else:
			wclim = (min(spettro[xmin:xmax+1]), max(spettro[xmin:xmax+1]))
		ax1.cla()
		if options.water:
			ax1.imshow(spgramma, interpolation='none', aspect='auto', extent=[xmin, xmax, 60, 0], cmap='jet', clim=wclim)
			ax1.set_title(" Spectrogram of "+str(len(spgramma))+" spectra")
			ax1.set_ylabel("Time (minutes)")
			ax1.set_xlabel('MHz')

		nmax_hold = np.maximum(spettro.astype(np.float), max_hold.astype(np.float))
		max_hold = nmax_hold
		nmin_hold = np.minimum(spettro.astype(np.float), min_hold.astype(np.float))
		min_hold = nmin_hold

		ax2.cla()
		x = np.linspace(0, 400, len(spettro))
		ax2.plot(x, spettro, color="b")
		ax2.plot(x, max_hold, color="r")
		ax2.plot(x, min_hold, color="g")
		ax2.set_xlim(0, 400)
		ax2.set_ylim(-100, 0)
		ax2.set_xlabel('MHz')
		ax2.set_ylabel("dBm")
		ax2.set_title("Power Spectrum", fontsize=10)
		ax2.grid(True)

		plt.title(fname.split("/")[-1][:-4].replace("_", "  "), fontsize=18)

		plt.tight_layout()
		plt.savefig(fname[:fname.rfind("/")+1]+SPG_DIR+"/"+fname.split("/")[-1][:-4]+".png")
		os.system("rm "+fname[:fname.rfind("/")+1]+SPG_DIR+"/"+fname.split("/")[-1][:-4]+".png")

		for cnt in tqdm(range(len(datafiles))):
			fname = datafiles[cnt]
			#print fname.split("/")[-1][-21:-4]
			orario = datetime.datetime.strptime(fname.split("/")[-1][-21:-4], "%Y-%m-%d_%H%M%S")
			with open(fname, "r") as f:
				a = f.read()
			l = struct.unpack(">d", a[0:8])[0]
			data = struct.unpack(">" + str(int(l)) + "b", a[8:])
			spettro = calcolaspettro(data, nsamples)

			adu_rms = np.sqrt(np.mean(np.power(data, 2), 0))
			volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
			power_adc = 10 * np.log10(
				np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
			power_rf = power_adc + 12  # single ended to diff net loose 12 dBm

			if options.power:
				centro = closest(x, float(options.channel))
				integra = linear2dBm(np.sum(dBm2Linear(spettro[centro-30:centro+30])))
				#print centro, spettro[centro-10:centro+10], integra
				#amp = spettro[closest(x, float(options.channel))]
				epoch = time.mktime(orario.timetuple())
				data = orario.strftime("%Y/%m/%d")
				ora = orario.strftime("%H:%M:%S")
				pfile.write(str(epoch)+"\t"+str(data)+"\t"+str(ora)+"\t"+str("%3.1f"%(integra))+"\n")

			if options.water:
				last, spgramma = spgramma[0], spgramma[1:]
				#print len(spgramma), len(spgramma[0]), bw, len(spettro), len(spettro[xmin:xmax+1])
				if xmin==0:
					# se xmin == 0 butto il canale zero
					spgramma = np.concatenate((spgramma, [spettro[:xmax+1].astype(np.float)]), axis=0)
				else:
					spgramma = np.concatenate((spgramma, [spettro[xmin:xmax+1].astype(np.float)]), axis=0)

			if ((orario - ora_inizio).seconds / 60. ) > 60:

				while np.isnan(spgramma[0][0]):
					last, spgramma = spgramma[0], spgramma[1:]
				dayspgramma = np.concatenate((dayspgramma, spgramma), axis=0)

				if len(spgramma) > 5:

					if options.water:
						ax1.cla()
						ax1.imshow(spgramma, interpolation='none', aspect='auto', extent=[asse_x[xmin], asse_x[xmax], 60, 0], cmap='jet', clim=wclim)
						ax1.set_title(" Spectrogram of "+str(len(spgramma))+" spectra")
						ax1.set_ylabel("Time (minutes)")
						ax1.set_xlabel('MHz')

						nmax_hold = np.maximum(spettro.astype(np.float), max_hold.astype(np.float))
						max_hold = nmax_hold
						nmin_hold = np.minimum(spettro.astype(np.float), min_hold.astype(np.float))
						min_hold = nmin_hold

						ax2.cla()
						#x = np.linspace(0, 400, len(spettro))
						ax2.plot(x, spettro, color="b")
						ax2.plot(x, max_hold, color="r")
						ax2.plot(x, min_hold, color="g")
						ax2.set_xlim(asse_x[xmin], asse_x[xmax])
						ax2.set_ylim(-100, 0)
						ax2.set_xlabel('MHz')
						ax2.set_ylabel("dBm")
						ax2.set_title("Power Spectrum", fontsize=10)
						ax2.annotate("RF Power: " + "%3.1f" % (power_rf) + " dBm", (10, -15), fontsize=16)
						ax2.annotate("Averaged Spectra: " + str(options.average), (280, -15), fontsize=16)
						ax2.grid(True)

						plt.title(fname.split("/")[-1][:-4].replace("_", "  "), fontsize=18)

						plt.tight_layout()
						#print fname[:fname.rfind("/")+1]+"PNG/"+fname.split("/")[-1][:-4]+".png"
						plt.savefig(fname[:fname.rfind("/")+1]+SPG_DIR+"/"+fname.split("/")[-1][:-4]+".png")

						spgramma = np.empty((1000, xmax-xmin+1,))
						spgramma[:] = np.nan
					ora_inizio = orario

		while np.isnan(spgramma[0][0]):
			last, spgramma = spgramma[0], spgramma[1:]
		dayspgramma = np.concatenate((dayspgramma, spgramma), axis=0)


		if len(spgramma) > 5:
			if options.water:
				ax1.cla()
				ax1.imshow(spgramma, interpolation='none', aspect='auto', extent=[asse_x[xmin], asse_x[xmax], 1, 0], cmap='jet', clim=wclim)
				ax1.set_title(" Spectrogram of " + str(len(spgramma)) + " spectra")
				ax1.set_ylabel("Time (minutes)")
				ax1.set_xlabel('MHz')

				nmax_hold = np.maximum(spettro.astype(np.float), max_hold.astype(np.float))
				max_hold = nmax_hold
				nmin_hold = np.minimum(spettro.astype(np.float), min_hold.astype(np.float))
				min_hold = nmin_hold

				ax2.cla()
				x = np.linspace(0, 400, len(spettro))
				ax2.plot(x, spettro, color="b")
				ax2.plot(x, max_hold, color="r")
				ax2.plot(x, min_hold, color="g")
				ax2.set_xlim(asse_x[xmin], asse_x[xmax])
				ax2.set_ylim(-100, 0)
				ax2.set_xlabel('MHz')
				ax2.set_ylabel("dBm")
				ax2.set_title("Power Spectrum", fontsize=10)
				ax2.annotate("RF Power: " + "%3.1f" % (power_rf) + " dBm", (10, -15), fontsize=16)
				ax2.annotate("Averaged Spectra: " + str(options.average), (280, -15), fontsize=16)
				ax2.grid(True)

				plt.title(fname.split("/")[-1][:-4].replace("_", "  "), fontsize=18)

				plt.tight_layout()
				# print fname[:fname.rfind("/")+1]+"PNG/"+fname.split("/")[-1][:-4]+".png"
				plt.savefig(fname[:fname.rfind("/") + 1] + SPG_DIR + "/" + fname.split("/")[-1][:-4] + ".png")

			#spgramma = np.empty((1000, bw - 5,))
			#spgramma[:] = np.nan
			ora_inizio = orario

		first_empty, dayspgramma = dayspgramma[:10], dayspgramma[10:]

		ax1.cla()
		if options.water:
			ax1.imshow(dayspgramma, interpolation='none', aspect='auto', extent=[asse_x[xmin], asse_x[xmax], 1, 0], cmap='jet', clim=wclim)
			ax1.set_title(" Spectrogram of " + fname.split("/")[-1][:-11].replace("_", "  "), fontsize=14)
			ax1.set_ylabel("A Day of 24 Hours")
			ax1.set_xlabel('MHz')

		nmax_hold = np.maximum(spettro.astype(np.float), max_hold.astype(np.float))
		max_hold = nmax_hold
		nmin_hold = np.minimum(spettro.astype(np.float), min_hold.astype(np.float))
		min_hold = nmin_hold

		ax2.cla()
		x = np.linspace(0, 400, len(spettro))
		ax2.plot(x, max_hold, color="r")
		ax2.plot(x, min_hold, color="g")
		ax2.set_xlim(asse_x[xmin], asse_x[xmax])
		ax2.set_ylim(-100, 0)
		ax2.set_xlabel('MHz')
		ax2.set_ylabel("dBm")
		ax2.set_title("Power Spectrum", fontsize=10)
		#ax2.annotate("RF Power: " + "%3.1f" % (power_rf) + " dBm", (10, -15), fontsize=16)
		#ax2.annotate("Averaged Spectra: " + str(options.average), (280, -15), fontsize=16)
		ax2.grid(True)

		plt.title("Max Hold and Min Hold of " + fname.split("/")[-1][:-11].replace("_", "  "), fontsize=14)

		plt.tight_layout()
		# print fname[:fname.rfind("/")+1]+"PNG/"+fname.split("/")[-1][:-4]+".png"
		if not os.path.isdir(BASE_DIR + "SPECTROGRAM/" + SPG_DIR + "/" + RX_DIR + POL_DIR):
			os.makedirs(BASE_DIR + "SPECTROGRAM/" + SPG_DIR + "/" + RX_DIR + POL_DIR)

		plt.savefig(BASE_DIR + "SPECTROGRAM/" + SPG_DIR + "/" + RX_DIR + POL_DIR + SPG_DIR[13:] + "_" + fname.split("/")[-1][:-11] + ".png")
		if options.power:
			pfile.close()



