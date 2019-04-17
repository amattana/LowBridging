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
IMG_DIR = "/IMG/"
GOOGLE_SPREADSHEET_NAME = "BRIDGING"

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
        print "Successfully connected to the google doc!"

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
    return celle


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
            #print "Starting process:",'python', 'tpm_get_stream.py', '--station='+Station, "--tile=%d" % (int(Tile)), Debug
            if subprocess.call(['python', 'tpm_get_stream.py', '--station='+Station, "--tile=%d" % (int(Tile)), Debug], stdout=DEVNULL) == 0:
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
        jobs.put((STATION['NAME'], tile, STATION['DEBUG']))
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

    parser.add_option("--resolution",
                      dest="resolution",
                      default=2000, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")

    (options, args) = parser.parse_args()
    debug = ""
    if options.debug:
        debug += "--debug"

    # Search for the antenna file
    if not os.path.isfile("STATIONS/MAP_" + options.station + ".txt"):
        keys, cells = read_from_google(GOOGLE_SPREADSHEET_NAME, options.station)
        write_to_local(options.station, cells)
    else:
        cells = read_from_local(options.station)

    #TPMs = sorted(list(set([x['TPM'] for x in cells])))
    #TILES = sorted(list(set([x['Tile'] for x in cells])))

    DATA = str(datetime.datetime.utcnow().date())

    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 17)
    rbw = int(closest(resolutions, options.resolution))
    avg = 2 ** rbw

    nsamples = 2 ** 17 / avg
    x_axes = np.linspace(0,400,(nsamples/2)+1)

    STATION = {}
    STATION['NAME'] = options.station
    #STATION['TPMs'] = TPMs
    STATION['DEBUG'] = debug
    STATION['CELLS'] = cells

    tile_active = []
    #tiles = os.listdir(WORK_DIR + DATA + "/DATA/")
    for tile in range(1,16+1):
        #print list(set(x['Power'] for x in cells if x['Tile'] == str(int(tile[-2:]))))
        if "ON" in list(set(x['Power'] for x in cells if x['Tile'] == str(tile))):
            tile_active += [str(tile)]
    STATION['TILES'] = tile_active

    print "\nDetected %d Tiles with %d antennas\n"%(len(tile_active), 16*len(tile_active))
    #print "Searching for TPMs: ", TPMs
    # Starting Acquisition Processes
    a = save_TPMs(STATION)


    # gridspec inside gridspec
    outer_grid = gridspec.GridSpec(len(tile_active), 1, hspace=0.5, left=0.02, right=0.98, bottom=0.05, top=0.95)

    fig = plt.figure(figsize=(14, 2.5 * len(tile_active)), facecolor='w')
    plt.ioff()
    t_axes = []
    axes = []
    for i in range(len(tile_active)):
        #print tile_active[i]
        gs = gridspec.GridSpecFromSubplotSpec(2, 16, wspace=0.05, hspace=0.5, subplot_spec=outer_grid[i])
        #gs.update(left=0.05, right=0.95, wspace=0.05, hspace=0.5)
        t_axes += [[plt.subplot(gs[0:2, 0:2]), plt.subplot(gs[0:2, 2:4]), plt.subplot(gs[0, 5:7]), plt.subplot(gs[1, 5:7])]]
        t_axes[i][0].set_axis_off()
        t_axes[i][0].plot([0.001,0.002], color='w')
        t_axes[i][0].set_xlim(-20, 20)
        t_axes[i][0].set_ylim(-20, 20)
        t_axes[i][0].annotate("Tile "+str(tile_active[i]), (-15, -4), fontsize=24, color='black')
        t_axes[i][1].set_axis_off()
        t_axes[i][1].plot([0.001,0.002], color='w')
        t_axes[i][1].set_xlim(-20, 20)
        t_axes[i][1].set_ylim(-20, 20)
        circle1 = plt.Circle((0, 0), 19, color='wheat', fill=False, linewidth=2.5)
        t_axes[i][1].add_artist(circle1)

        t_axes[i][2].plot([0.001,0.002], color='w')
        t_axes[i][2].set_xlim(-20, 20)
        t_axes[i][2].set_ylim(-20, 20)
        t_axes[i][2].get_xaxis().set_visible(False)
        t_axes[i][2].get_yaxis().set_visible(False)
        t_axes[i][2].set_title("Power Pol X", fontsize=10)

        t_axes[i][3].plot([0.001,0.002], color='w')
        t_axes[i][3].set_xlim(-20, 20)
        t_axes[i][3].set_ylim(-20, 20)
        t_axes[i][3].get_xaxis().set_visible(False)
        t_axes[i][3].get_yaxis().set_visible(False)
        t_axes[i][3].set_title("Power Pol y", fontsize=10)

        for r in range(2):
            for c in range(8):
                axes += [plt.subplot(gs[(r, c+8)])]
    fig.show()

    ax_tile = 0
    for n, tile in enumerate(tile_active):
        ax_ant = 0
        #ants = os.listdir(WORK_DIR + DATA + "/DATA/TILE-%02d"%tile)
        ants = []
        for j in range(16):
            #print j, tile, [x['Antenna'] for x in cells if ((x['Tile'] == tile) and (x['RX'] == str(j+1)))]
            ants += ["ANT-%03d"%int([x['Antenna'] for x in cells if ((x['Tile'] == tile) and (x['RX'] == str(j+1)))][0])]
        #print ants
        for ant in ants:
            axes[ax_ant + (ax_tile * 16)].cla()
            for pol, col in [("/POL-X/", "b"), ("/POL-Y/", "g")]:
                fname = WORK_DIR + DATA + "/DATA/TILE-%02d"%int(tile) + "/" + ant + pol
                fname += sorted(os.listdir(WORK_DIR + DATA + "/DATA/TILE-%02d"%int(tile) + "/" + ant + pol), reverse=True)[0]

                with open(fname, "r") as f:
                    a = f.read()
                data = struct.unpack(">" + str(len(a)) + "b", a)
                singolo = calcolaspettro(data, nsamples)

                axes[ax_ant+(ax_tile*16)].plot(x_axes, singolo, color=col)
            axes[ax_ant+(ax_tile*16)].set_ylim(-80, 0)
            axes[ax_ant+(ax_tile*16)].get_xaxis().set_visible(False)
            axes[ax_ant+(ax_tile*16)].get_yaxis().set_visible(False)
            #axes[ax_ant+(ax_tile*16)].set_xlabel('MHz')
            #axes[ax_ant+(ax_tile*16)].set_ylabel("dBm")
            axes[ax_ant+(ax_tile*16)].set_title(ant[-7:], fontsize=10)
            #axes[ax_ant+(ax_tile*16)].grid(True)
            ax_ant = ax_ant + 1

            t_axes[n][1].plot(3, 3, marker='+', markersize=6, linestyle='None', color='k')

        ax_tile = ax_tile + 1
        t_acq = fname[-28:-4]

            #print tile, t_acq
    #plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.canvas.draw()
    time.sleep(1)
    plt.savefig(WORK_DIR + DATA + IMG_DIR + "IMG_" + fname[-28:-11] + ".png")





