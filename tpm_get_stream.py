#!/usr/bin/env python

'''

  Low Bridging Phase 0 Logger.

  It produces for each antenna and for both pols:
    -  Time domain binary data (first double word (64b) is the lenght of the following double word (64b) elements)
    -  Spectra binary data (first double word (64b) is the lenght of the following double word (64b) elements)
    -  Picture of the spectra

  Logging period can be specified in minutes with parameter -t (--time)

  When hit Ctrl+C (Keyboard Interrupt Signal) it produces
    -  A Movie (MPEG4 avi) for each antenna saved in the videos folder with subfolders for each pol

'''

__author__ = "Andrea Mattana"
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
from tpm_utils import *
from bsp.tpm import *

DEVNULL = open(os.devnull, 'w')

from gui_utils import *
from rf_jig import *
from rfjig_bsp import *
from ip_scan import *

from optparse import OptionParser


# Other stuff
import numpy as np
import struct
import datetime
import time

import urllib3
# Test application, security unimportant:
urllib3.disable_warnings()
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Some globals
OUT_PATH = "/storage/bridging/"
DATA_PATH = "DATA/"

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
    return cells



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


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--station",
                      dest="station",
                      default="SKALA-4",
                      help="The station type (def: SKALA-4, alternatives: EDA-2)")

    parser.add_option("--tile",
                      dest="tile",
                      default="10", type=int,
                      help="Numer of the Tile (def: 10)")

    parser.add_option("-d", "--debug", action='store_true',
                      dest="debug",
                      default=False,
                      help="If set the program runs in debug mode")

    (options, args) = parser.parse_args()

    if options.debug:
        print "[" + str(options.station) + "/" + "%02d"%(options.tile) + "] DEBUG MODE: Using saved data !!!\n"

    nsamples = 1024
    rbw = (800000.0 / 2 ** 17) * (2 ** 17 / nsamples)

    # Search for TPMs
    TILE = str(options.tile)
    TILE_PATH = "TILE-%02d/"%(int(TILE))
    data = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y/%m/%d")
    ora = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%H:%M:%S")

    # Creating Main data Directory
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)
        print "Generating main directory for data... (" + OUT_PATH + ")"

    # Creating Directory for today's data
    OUT_PATH = OUT_PATH + datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y-%m-%d/")
    try:
        if not os.path.exists(OUT_PATH):
            os.makedirs(OUT_PATH)
            print "Generating directory for today data... (" + OUT_PATH + ")"
    except:
        print "Directory " + OUT_PATH + " already exist..."

    OUT_PATH = OUT_PATH + options.station + "/"
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)

    ## Creating Directory to store the videos
    if not os.path.exists(OUT_PATH + "IMG"):
        os.makedirs(OUT_PATH + "IMG")

    # Search for the antenna file
    if not os.path.isfile("STATIONS/MAP_" + options.station + ".txt"):
        cells = read_from_google(GOOGLE_SPREADSHEET_NAME, options.station)
    else:
        cells = read_from_local(options.station)

    TPM = str(list(set([x['TPM'] for x in cells if x['Tile'] == str(options.tile)]))[0])
    board_ip = "10.0.10." + TPM
    TILE = "%02d"%(int(options.tile))
    ANT_NAMES = []
    for i in range(1, 17):
        print TILE, i, list(set([x['Antenna'] for x in cells if (x['TPM'] == TPM and x['RX'] == str(i))]))
        ANT_NAMES += ["ANT-%03d"%(int(list(set([x['Antenna'] for x in cells if (x['TPM'] == TPM and x['RX'] == str(i))]))[0]))]

    freqs, spettro, rawdata, rms, rfpower = get_raw_meas(tpm_obj(board_ip), debug=options.debug)
    orario = datetime.datetime.utcnow()
    ora = str(orario).replace(":","").replace(" ","_").replace(".","_")

    for rx in xrange(len(spettro) / 2):
        for p, pol in enumerate(["X", "Y"]):
            fpath = OUT_PATH + DATA_PATH
            if not os.path.exists(fpath):
                os.makedirs(fpath)
            fpath += TILE_PATH
            if not os.path.exists(fpath):
                os.makedirs(fpath)
            rxpath = ANT_NAMES[rx] + "/"
            if not os.path.exists(fpath + rxpath):
                os.makedirs(fpath + rxpath)
            fname = "POL-" + pol + "/"
            if not os.path.exists(fpath + rxpath + fname):
                os.makedirs(fpath + rxpath + fname)
            fname += "TILE-" + TILE + "_" + ANT_NAMES[rx] + "_POL-" + pol + "_" + ora

            with open(fpath + rxpath + fname + ".raw", "wb") as f:
                f.write(struct.pack(">" + str(len(rawdata[(rx * 2) + p])) + "b",
                                    *rawdata[(rx * 2) + p]))
