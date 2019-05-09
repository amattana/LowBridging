#!/usr/bin/env python

'''

  Low Bridging Phase 1 Logger.

  It produces for each antenna and for both pols:
    -  Time domain binary data (first double word (64b) is the lenght of the following double word (64b) elements)
    -  Spectra binary data (first double word (64b) is the lenght of the following double word (64b) elements)
    -  Picture of the spectra

  Logging period depends on the load of the workstation

  When hit Ctrl+C (Keyboard Interrupt Signal) it produces
    -  A Movie (MPEG4 avi) for each antenna saved in the videos folder with subfolders for each pol

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import multiprocessing
import subprocess
import os, datetime
from optparse import OptionParser
import urllib3
# Test application, security unimportant:
urllib3.disable_warnings()
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
from openpyxl import load_workbook

import numpy as np
import struct, time
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

PYSKA_DIR = "/home/mattana/work/SKA-AAVS1/tools/pyska/"
WORK_DIR = "/data/data_2/2019-LOW-BRIDGING-PHASE1/"
WWW = "/data/monitoring/phase1/"
IMG_DIR = "/IMG/"
GOOGLE_SPREADSHEET_NAME = "BRIDGING"

FIG_W = 14
TILE_H = 2.5


def check_gspread_mtime(docname, sheetname):
    mtime = '1980-01-01T00:00:00.000Z'
    try:
        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        client = gspread.authorize(creds)
    except:
        print "ERROR: Google Credential file not found or invalid file!"

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    try:
        sheet = client.open(docname).worksheet(sheetname)
        mtime = sheet.updated

    except:
        pass
    return mtime


def read_from_google(docname, sheetname):
    try:
        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        client = gspread.authorize(creds)
    except:
        print "ERROR: Google Credential file not found or invalid file!"

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    try:
        sheet = client.open(docname).worksheet(sheetname)
        print datetime.datetime.utcnow(), "[GSP] Successfully connected to the google spreadsheet!"

        # Extract and print all of the values
        values = sheet.get_all_values()
        cells = []
        keys = values[0]
        for line in values[1:]:
            record = {}
            for n, col in enumerate(line):
                record[keys[n]] = col
            record['East'] = float(record['East'].replace(",","."))
            record['North'] = float(record['North'].replace(",", "."))

            cells += [record]
        print datetime.datetime.utcnow(), "[GSP] Google Spreadsheet Successfully downloaded!"
    except:
        print "ERROR: Google Spreadsheet Name (or Sheet Name) is not correct! {", docname, sheetname, "}"
    return keys, cells


def read_from_local(station):
    with open("STATIONS/MAP_" + station + ".txt") as f:
        lines = f.readlines()
    celle = []
    keys = lines[0].split("\t")
    for l in lines[1:]:
        record = {}
        for n, r in enumerate(l.split("\t")):
            record[keys[n]] = r
        celle += [record]
    return keys, celle


def write_to_local(station, cells):
    if not os.path.exists("STATIONS/"):
        os.makedirs("STATIONS/")
    with open("STATIONS/MAP_" + station + ".txt", "w") as f:
        header = ""
        for k in keys:
            header += str(k) + "\t"
        f.write(header[:-1])
        for record in cells:
            line = "\n"
            for k in keys:
                line += str(record[k]) + "\t"
            f.write(line[:-1])


def dump(job_q, results_q):
    DEVNULL = open(os.devnull, 'w')
    while True:
        Station, Tile, Debug = job_q.get()
        if Tile == None:
            break
        try:
            print datetime.datetime.utcnow(), "  -   Starting process:",'python', 'tpm_get_stream.py', '--station='+Station, "--tile=%d" % (int(Tile)), Debug
            if subprocess.call(['python', 'tpm_get_stream.py', '--station='+Station, "--tile=%d" % (int(Tile)), Debug], stdout=DEVNULL) == 0:
                print datetime.datetime.utcnow(), "  -   Received data from Tile ",  int(Tile)
                results_q.put(Tile)
        except:
            pass


def sort_ip_list(ip_list):
    """Sort an IP address list."""
    from IPy import IP
    ipl = [(IP(ip).int(), ip) for ip in ip_list]
    ipl.sort()
    return [ip[1] for ip in ipl]


def save_TPMs(STATION):
	t = datetime.datetime.utcnow()
	print t, "[ASK] Asking data to %d Tiles..."%(len(STATION['TILES']))
	lista_tiles = []
	for tile in STATION['TILES']:
		os.system("python tpm_get_stream.py --station=" + STATION['NAME'] + "  --tile=%d" % (int(tile['Tile'])))
		lista_tiles += [tile]
	lista_tiles = sorted(lista_tiles)
	t_end = datetime.datetime.utcnow()
	print t_end, "[RCV] Received data from %d Tiles in %d seconds\n"%(len(lista_tiles), (t_end-t).seconds)
	return lista_tiles
		


def saveParallelTPMs(STATION):
    pool_size = len(STATION['TILES'])
    t = datetime.datetime.utcnow()
    print t, "[ASK] Asking data to %d Tiles..."%(pool_size)

    jobs = multiprocessing.Queue()
    results = multiprocessing.Queue()

    pool = [multiprocessing.Process(target=dump, args=(jobs, results))
            for i in range(pool_size)]

    for p in pool:
        p.start()

    for tile in STATION['TILES']:
        jobs.put((STATION['NAME'], tile['Tile'], STATION['DEBUG']))
        # time.sleep(1)

    for p in pool:
        jobs.put((None, None, None))

    for p in pool:
        p.join()

    lista_tiles = []
    while not results.empty():
        lista_tiles += [results.get()]
    if lista_tiles == []:
        print "No iTPM boards found!"
    else:
        lista_tiles = sorted(lista_tiles)
        t_end = datetime.datetime.utcnow()
        print t_end, "[RCV] Received data from %d Tiles in %d seconds"%(len(lista_tiles), (t_end-t).seconds)
        if not pool_size == len(lista_tiles):
            print t_end, "[ERR] Tiles ok are {",
            for tile in lista_tiles:
                print ",", tile,
            print "}"
    return lista_tiles


def calcSpectra(vett):
    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett * window)
    N = len(spettro)
    acf = 2  # amplitude correction factor
    spettro[:] = abs((acf * spettro) / N)
    # print len(vett), len(spettro), len(np.real(spettro))
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
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d", "--debug", action='store_true',
                      dest="debug",
                      default=False,
                      help="If set the program runs in debug mode")

    parser.add_option("--station",
                      dest="station",
                      default="SKALA-4",
                      help="The station type (def: SKALA-4, alternatives: EDA-2)")

    parser.add_option("--project",
                      dest="project",
                      default="SKA-Low BRIDGING",
                      help="The Project name (def: SKA-Low BRIDGING)")

    parser.add_option("--resolution",
                      dest="resolution",
                      default=2000, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")

    (options, args) = parser.parse_args()
    debug = ""
    if options.debug:
        debug += "--debug"

    fig = None

    if not os.path.isdir(WWW):
        os.makedirs(WWW)
    WWW += options.station.lower()

    while True:

        # Search for the antenna file
        modified = False
        mtime = check_gspread_mtime(GOOGLE_SPREADSHEET_NAME, options.station)
        #print mtime
        if not os.path.isfile("STATIONS/MAP_" + options.station + ".txt"):
            keys, cells = read_from_google(GOOGLE_SPREADSHEET_NAME, options.station)
            write_to_local(options.station, cells)
        else:
            #print "LOCAL FILE   MTIME: ", datetime.datetime.utcfromtimestamp(os.path.getmtime("STATIONS/MAP_" + options.station + ".txt"))
            #print "GSPREADSHEET MTIME: ", datetime.datetime.strptime(mtime[:-5], "%Y-%m-%dT%H:%M:%S")
            if datetime.datetime.utcfromtimestamp(os.path.getmtime("STATIONS/MAP_" + options.station + ".txt")) < \
                    datetime.datetime.strptime(mtime[:-5], "%Y-%m-%dT%H:%M:%S"):
                print datetime.datetime.utcnow(), "[GSP] GSpread modified, updating...", \
                    datetime.datetime.utcfromtimestamp(os.path.getmtime("STATIONS/MAP_" + options.station + ".txt")), \
                    " -->", datetime.datetime.strptime(mtime[:-5], "%Y-%m-%dT%H:%M:%S")
                modified = True
                keys, cells = read_from_google(GOOGLE_SPREADSHEET_NAME, options.station)
                write_to_local(options.station, cells)
            else:
                keys, cells = read_from_local(options.station)

        DATA = str(datetime.datetime.utcnow().date())

        resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 17)
        rbw = int(closest(resolutions, options.resolution))
        avg = 2 ** rbw

        nsamples = 2 ** 17 / avg
        x_axes = np.linspace(0,400,(nsamples/2)+1)

        STATION = {}
        STATION['NAME'] = options.station
        STATION['PROJECT'] = options.project
        STATION['DEBUG'] = debug
        STATION['TILES'] = []

        tot_antenne = 0
        for tile in range(1,16+1):
            #print list(set(x['Power'] for x in cells if x['Tile'] == str(int(tile[-2:]))))
            if "ON" in list(set(x['Power'] for x in cells if x['Tile'] == str(tile))):
                #tile_active += [str(tile)]
                STATION['TILES'] += [{}]
                STATION['TILES'][-1]['Tile'] = tile
                STATION['TILES'][-1]['SmartBox'] = {}
                STATION['TILES'][-1]['SmartBox']['Name'] = "TODO"
                STATION['TILES'][-1]['SmartBox']['East'] = "TODO"
                STATION['TILES'][-1]['SmartBox']['North'] = "TODO"
                STATION['TILES'][-1]['SmartBox']['FEM'] = ["TODO","TODO","TODO","TODO"]
                STATION['TILES'][-1]['Antenne'] = []
                for rx in range(1,16+1):
                    antenna_record = [x for x in cells if ((x['Tile'] == str(tile)) and (x['RX'] == str(rx)))][0]
                    STATION['TILES'][-1]['Antenne'] += [{}]
                    STATION['TILES'][-1]['Antenne'][-1]['Name'] = "ANT-%03d" % int(antenna_record['Antenna'])
                    STATION['TILES'][-1]['Antenne'][-1]['North'] = float(antenna_record['North'])
                    STATION['TILES'][-1]['Antenne'][-1]['East'] = float(antenna_record['East'])
                    tot_antenne = tot_antenne + 1

        print "\nDetected %d Tiles with %d antennas\n"%(len(STATION['TILES']), tot_antenne)
        #print "Searching for TPMs: ", TPMs

        # Starting Acquisition Processes
        a = saveParallelTPMs(STATION)
        #a = save_TPMs(STATION)
        #print len(STATION['TILES'])

        # gridspec inside gridspec
        outer_grid = gridspec.GridSpec(len(STATION['TILES']), 1, hspace=0.8, left=0.02, right=0.98, bottom=0.1, top=0.95)

        if ((not (fig == None)) and (modified)):
            plt.close(fig)
            fig = None
            modified = False

        if fig == None:
            #print  FIG_W, TILE_H * len(STATION['TILES']) + 0.8 * len(STATION['TILES'])
            fig = plt.figure(figsize=(FIG_W, TILE_H * len(STATION['TILES']) + 0.8 * len(STATION['TILES'])), facecolor='w')
            plt.ioff()
            t_axes = []
            axes = []
            for i in range(len(STATION['TILES'])):
                #print tile_active[i]
                gs = gridspec.GridSpecFromSubplotSpec(2, 17, wspace=0.05, hspace=0.5, subplot_spec=outer_grid[i])
                t_axes += [[plt.subplot(gs[0:2, 0:3]), plt.subplot(gs[0:2, 3:5]), plt.subplot(gs[0, 6:8]), plt.subplot(gs[1, 6:8])]]

                for r in range(2):
                    for c in range(8):
                        axes += [plt.subplot(gs[(r, c+9)])]
            #fig.show()

        ax_tile = 0
        ind = np.arange(16)
        for n, tile in enumerate(STATION['TILES']):

            #print n, len(STATION['TILES'])
            t_axes[n][0].cla()
            t_axes[n][0].set_axis_off()
            t_axes[n][0].plot([0.001, 0.002], color='w')
            t_axes[n][0].set_xlim(-20, 20)
            t_axes[n][0].set_ylim(-20, 20)
            t_axes[n][0].annotate("Tile " + str(STATION['TILES'][n]['Tile']), (-11, 5), fontsize=26, color='black')

            t_axes[n][1].cla()
            t_axes[n][1].set_axis_off()
            t_axes[n][1].plot([0.001, 0.002], color='wheat')
            t_axes[n][1].set_xlim(-25, 25)
            t_axes[n][1].set_ylim(-25, 25)
            circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
            t_axes[n][1].add_artist(circle1)
            t_axes[n][1].annotate("E", (21, -1), fontsize=10, color='black')
            t_axes[n][1].annotate("W", (-25, -1), fontsize=10, color='black')
            t_axes[n][1].annotate("N", (-1, 21), fontsize=10, color='black')
            t_axes[n][1].annotate("S", (-1, -24), fontsize=10, color='black')

            t_axes[n][2].cla()
            t_axes[n][2].plot([0.001, 0.002], color='w')
            t_axes[n][2].set_xlim(-20, 20)
            t_axes[n][2].set_ylim(-20, 20)
            t_axes[n][2].set_title("Power Pol X", fontsize=10)

            t_axes[n][3].cla()
            t_axes[n][3].plot([0.001, 0.002], color='w')
            t_axes[n][3].set_xlim(-20, 20)
            t_axes[n][3].set_ylim(-20, 20)
            t_axes[n][3].set_title("Power Pol Y", fontsize=10)

            ax_ant = 0
            ants = []
            for j in range(16):
                ants += ["ANT-%03d"%int([x['Antenna'] for x in cells if ((x['Tile'] == str(tile['Tile'])) and (x['RX'] == str(j+1)))][0])]
            adu_rms = []
            for en, ant in enumerate(ants):
                axes[ax_ant + (ax_tile * 16)].cla()
                for pol, col in [("/POL-X/", "b"), ("/POL-Y/", "g")]:
                    fname = WORK_DIR + DATA + "/" + options.station + "/DATA/TILE-%02d"%int(tile['Tile']) + "/" + ant + pol
                    fname += sorted(os.listdir(WORK_DIR + DATA + "/" + options.station + "/DATA/TILE-%02d"%int(tile['Tile']) + "/" + ant + pol), reverse=True)[0]

                    #print fname
                    with open(fname, "r") as f:
                        a = f.read()
                    data = struct.unpack(">" + str(len(a)) + "b", a)
                    singolo = calcolaspettro(data, nsamples)

                    adu_rms += [np.sqrt(np.mean(np.power(data, 2), 0))]

                    axes[ax_ant+(ax_tile*16)].plot(x_axes[5:-5], singolo[5:-5], color=col)
                axes[ax_ant+(ax_tile*16)].set_xlim(0, 400)
                axes[ax_ant+(ax_tile*16)].set_ylim(-80, 0)
                if not ((en == 0) or (en == 8)):
                    axes[ax_ant+(ax_tile*16)].get_yaxis().set_visible(False)
                else:
                    axes[ax_ant+(ax_tile*16)].set_yticks([0, -20, -40, -60, -80])
                    axes[ax_ant+(ax_tile*16)].set_yticklabels([0, -20, -40, -60, -80], fontsize=8)
                    axes[ax_ant+(ax_tile*16)].set_ylabel("dB", fontsize=10)
                if (en > 7):
                    axes[ax_ant+(ax_tile*16)].set_xticks([100, 200, 300, 400])
                    axes[ax_ant+(ax_tile*16)].set_xticklabels([100, 200, 300, 400], fontsize=8, rotation=45)
                    axes[ax_ant+(ax_tile*16)].set_xlabel("MHz", fontsize=10)
                else:
                    axes[ax_ant+(ax_tile*16)].set_xticks([100, 200, 300, 400])
                    axes[ax_ant+(ax_tile*16)].set_xticklabels(["", "", "", ""], fontsize=1)
                axes[ax_ant+(ax_tile*16)].set_title(ant[-7:], fontsize=10)
                ax_ant = ax_ant + 1

                # Draw antenna positions
                t_axes[n][1].plot(float(tile['Antenne'][en]['East']), float(tile['Antenne'][en]['North']), marker='+', markersize=4, linestyle='None', color='k')

            # Plot Power X
            t_axes[n][2].cla()
            t_axes[n][2].tick_params(axis='both', which='both', labelsize=6)
            t_axes[n][2].set_xticks(xrange(1,17))
            t_axes[n][2].set_xticklabels(np.array(range(1,17)).astype("str").tolist(), fontsize=4)
            t_axes[n][2].set_yticks([15, 20])
            t_axes[n][2].set_yticklabels(["15", "20"], fontsize=7)
            t_axes[n][2].set_ylim([0, 40])
            t_axes[n][2].set_xlim([0, 16])
            t_axes[n][2].set_ylabel("RMS", fontsize=10)
            t_axes[n][2].grid()
            t_axes[n][2].bar(ind+0.5, adu_rms[0::2], 0.8, color='b')
            t_axes[n][2].set_title("Power Pol X", fontsize=10)

            # Plot Power Y
            t_axes[n][3].cla()
            t_axes[n][3].tick_params(axis='both', which='both', labelsize=6)
            t_axes[n][3].set_xticks(xrange(1,17))
            t_axes[n][3].set_xticklabels(np.array(range(1,17)).astype("str").tolist(), fontsize=4)
            t_axes[n][3].set_yticks([15, 20])
            t_axes[n][3].set_yticklabels(["15", "20"], fontsize=7)
            t_axes[n][3].set_ylim([0, 40])
            t_axes[n][3].set_xlim([0, 16])
            t_axes[n][3].set_ylabel("RMS", fontsize=10)
            t_axes[n][3].set_xlabel("Power Pol Y", fontsize=10)
            t_axes[n][3].grid()
            t_axes[n][3].bar(ind+0.5, adu_rms[1::2], 0.8, color='g')

            ax_tile = ax_tile + 1
            t_acq = fname[-28:-9]
            t_axes[n][0].annotate("Acquisition Time (UTC)", (-17.7, -6), fontsize=12, color='black')
            t_axes[n][0].annotate(t_acq[:-6].replace("_"," ")+":"+t_acq[-6:-4]+":"+t_acq[-4:-2]+"."+t_acq[-1], (-17.8, -12), fontsize=12, color='black')

        fig.canvas.draw()
        time.sleep(1)
        if not os.path.isdir(WORK_DIR):
            os.makedirs(WORK_DIR)
        if not os.path.isdir(WORK_DIR + DATA):
            os.makedirs(WORK_DIR + DATA)
        if not os.path.isdir(WORK_DIR + DATA + IMG_DIR):
            os.makedirs(WORK_DIR + DATA + IMG_DIR)

        plt.savefig(WORK_DIR + DATA + IMG_DIR + "IMG_" + fname[-28:-11] + ".png")
        if not os.path.isdir(WWW):
            os.makedirs(WWW)

        plt.savefig(WWW + "/STATION_" + STATION['NAME'] + ".png")

        time.sleep(20)





