#!/usr/bin/env python

'''

  Shows TPM Levels

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

from pyaavs.tile import Tile
import os
import yaml
import numpy as np

from optparse import OptionParser

conf_file = "/opt/aavs/config/aavs1.5.yml"


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--ip",
                      dest="ip",
                      default="",
                      help="The board IP")

    parser.add_option("--conf",
                      dest="conf",
                      default="/def/conf/file",
                      help="A station configuration file to get LMC network infos")

    parser.add_option("--rms", action="store_true",
                      dest="rms",
                      default=False,
                      help="Display also RMS values")

    (options, args) = parser.parse_args()

    board_ip = options.ip

    if not os.path.exists(conf_file):
        conf_file = options.conf
    if os.path.exists(conf_file):
        with open(conf_file, 'r') as f:
            c = yaml.load(f)
        lmc_ip = c['network']['lmc']['lmc_ip']
        lmc_port = c['network']['lmc']['lmc_port']
    else:
        print "\nERROR: Configuration file not found!", conf_file
        print "Trying with default lmc conf [10.0.0.100, 4660]"
        lmc_ip = "10.0.0.100"
        lmc_port = 4660
    #print c
    print "Connecting to board "+options.ip+"..."

    try:
        tile = Tile(ip=options.ip, port=10000, lmc_ip=lmc_ip, lmc_port=lmc_port)
        tile.connect()

        print "Connection successfully!\n"

        adu_rms = np.array(tile.get_adc_rms())
        volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
        power_adc = 10 * np.log10(
            np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
        power_rf = power_adc + 12  # single ended to diff net loose 12 dBm

        if not options.rms:
            print "\n\n TPM INPUT\tPol-X Level\tPol-Y Level"
            print "\n    #\t\t (dBm)\t\t (dBm)"
            print "\n-----------------------------------------------------"
        else:
            print "\n\n TPM INPUT\tPol-X Level\tPol-Y Level"
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
        print "\n\n"

    except:
        print "\n\nExiting with errors\n"
