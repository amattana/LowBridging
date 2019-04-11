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
import os
from optparse import OptionParser
import urllib3
# Test application, security unimportant:
urllib3.disable_warnings()
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
from openpyxl import load_workbook


PYSKA_DIR = "/home/mattana/work/SKA-AAVS1/tools/pyska/"
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
    cells = []
    try:
        sheet = client.open(docname).worksheet(sheetname)
        print "Successfully connected to the google doc!"

        # Extract and print all of the values
        cells = sheet.get_all_records()
        for i in range(len(cells)):
            cells[i]['East'] = float(cells[i]['East'].replace(",","."))
            cells[i]['North'] = float(cells[i]['North'].replace(",", "."))
            #print cells[i]['Antenna'], cells[i]['North'], cells[i]['East']
    except:
        print "ERROR: Google Spreadsheet Name (or Sheet Name) is not correct! {", docname, sheetname, "}"
    return cells


def dump(job_q, results_q):
    DEVNULL = open(os.devnull, 'w')
    while True:
        FPGA_IP, Tile, debug = job_q.get()
        if FPGA_IP == None:
            break
        try:
            Tile = "--tile=%d" % (Tile)
            print "Starting process:",'python', 'tpm_get_stream.py', '-b', FPGA_IP, Tile, debug
            if subprocess.call(['python', 'tpm_get_stream.py', '-b', FPGA_IP, Tile, debug], stdout=DEVNULL) == 0:
            #if subprocess.call(['python', 'tpm_get_stream.py', '--board=', FPGA_IP, '--debug'], stdout=DEVNULL) == 0:
                results_q.put(FPGA_IP)
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

    jobs = multiprocessing.Queue()
    results = multiprocessing.Queue()

    pool = [multiprocessing.Process(target=dump, args=(jobs, results))
            for i in range(pool_size)]

    for p in pool:
        p.start()

    for i in STATION['TPMs']:
        tile = list(set(x['Tile'] for x in STATION['CELLS'] if x['TPM'] == int(i)))[0]
        jobs.put(('10.0.10.{0}'.format(i), tile, STATION['DEBUG']))
        # time.sleep(1)

    for p in pool:
        jobs.put((None, None, None))

    for p in pool:
        p.join()

    print
    lista_ip = []
    while not results.empty():
        lista_ip += [results.get()]
    if lista_ip == []:
        print "No iTPM boards found!"
    else:
        lista_ip = sort_ip_list(lista_ip)
        for ip in lista_ip:
            print ip
        #print lista_ip
    return lista_ip


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
    if not os.path.isfile("MAP_" + options.station + ".txt"):
        cells = read_from_google(GOOGLE_SPREADSHEET_NAME, options.station)
        #print len(cells)
    TPMs = list(set([x['TPM'] for x in cells]))
    TILES = list(set([x['Tile'] for x in cells]))

    STATION = {}
    STATION['NAME'] = options.station
    STATION['TPMs'] = TPMs
    STATION['TILES'] = TILES
    STATION['DEBUG'] = debug
    STATION['CELLS'] = cells

    print "\nDetected %d Tiles with %d antennas connected to %d TPMs\n"%(len(TILES), len(cells), len(TPMs))
    #print "Searching for TPMs: ", TPMs
    # Starting Acquisition Processes
    a = save_TPMs(STATION)
