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


PYSKA_DIR = "/home/mattana/work/SKA-AAVS1/tools/pyska/"
WORK_DIR = "/data/data_2/2019-LOW-BRIDGING-PHASE1/"
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
    pool_size = len(TPMs)
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

    TPMs = list(set([x['TPM'] for x in cells]))
    TILES = list(set([x['Tile'] for x in cells]))

    STATION = {}
    STATION['NAME'] = options.station
    STATION['TPMs'] = TPMs
    STATION['TILES'] = TILES
    STATION['DEBUG'] = debug
    STATION['CELLS'] = cells

    DATA = str(datetime.datetime.utcnow().date())


    print "\nDetected %d Tiles with %d antennas connected to %d TPMs\n"%(len(TILES), len(cells), len(TPMs))
    #print "Searching for TPMs: ", TPMs
    # Starting Acquisition Processes
    a = save_TPMs(STATION)

    tiles = os.listdir(WORK_DIR + DATA + "/DATA/")
    for tile in tiles:
        ants = os.listdir(WORK_DIR + DATA + "/DATA/" + tile)
        for ant in ants:
            for pol in ["/POL-X/", "/POL-Y/"]:
                fname = WORK_DIR + DATA + "/DATA/" + tile + "/" + ant + pol
                fname += sorted(os.listdir(WORK_DIR + DATA + "/DATA/" + tile + "/" + ant + pol), reverse=True)[0]
        t_acq = fname[-28:-4]
        print t_acq





