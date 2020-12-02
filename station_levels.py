#!/usr/bin/env python

'''

  Shows TPM Levels

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2020, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

from aavs_calibration.common import get_antenna_positions, get_antenna_tile_names
from pyaavs import station
import numpy as np

from optparse import OptionParser

conf_file = "/opt/aavs/config/aavs2.yml"


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--ip",
                      dest="ip",
                      default="",
                      help="The board IP")

    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs2.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS2)")

    parser.add_option("--rms", action="store_true",
                      dest="rms",
                      default=False,
                      help="Display also RMS values")

    (options, args) = parser.parse_args()

    # Check if a configuration file was defined
    if options.config is None:
        print "A station configuration file is required, exiting"
        exit()

    # Load configuration file
    station.load_configuration_file(options.config)
    station_name = station.configuration['station']['name']

    # Grab antenna base numbers and positions
    base, x, y = get_antenna_positions(station_name)

    remap = [0, 1, 2, 3, 8, 9, 10, 11, 15, 14, 13, 12, 7, 6, 5, 4]

    # Store number of tiles
    nof_tiles = len(station.configuration['tiles'])

    # Create station instance
    aavs_station = station.Station(station.configuration)
    aavs_station.connect()

    for tile in station.tiles:

        adu_rms = np.array(tile.get_adc_rms())
        volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
        power_adc = 10 * np.log10(
            np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
        power_rf = power_adc + 12  # single ended to diff net loose 12 dBm

        print "\n\n=========================================================="
        print " Tile-%02d\n" % (int(tile.get_tile_id()))

        if not options.rms:
            print "\n TPM INPUT\tPol-X Level\tPol-Y Level"
            print "\n    #\t\t (dBm)\t\t (dBm)"
            print "\n-----------------------------------------------------"
        else:
            print "\n TPM INPUT\tPol-X Level\tPol-Y Level"
            print "\n    #\t\t  (dBm)\tRMS\t (dBm)\tRMS"
            print "\n-----------------------------------------------------"

        for rx in xrange(len(power_adc) / 2):
            print "\n INPUT %02d"%(rx+1),
            for p, pol in enumerate(["X", "Y"]):
                print "\t%3.1f"%(power_rf[(rx*2)+p]),
                if options.rms:
                    print "\t%3.1f" % (adu_rms[(rx * 2) + p]),
                else:
                    print "\t",
            if (rx+1) % 4 == 0:
                print
        print "\n"

