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
                      default="",
                      help="A station configuration file to get LMC network infos")

    (options, args) = parser.parse_args()

    board_ip = options.ip

    if os.path.exists(conf_file):
        with open(conf_file, 'r') as f:
            c = yaml.load(f)

    #print c
    print "Connecting to board "+options.ip+"..."

    try:
        tile = Tile(ip=options.ip, port=10000, lmc_ip=c['network']['lmc']['lmc_ip'], lmc_port=c['network']['lmc']['lmc_port'])
        tile.connect()

        print "Connection successfully!\n"

        adu_rms = tile.get_adc_rms()

        print len(adu_rms)
        print adu_rms
        exit(0)

        print "\n\n TPM INPUT\tPol-X Level\tPol-Y Level"
        print "\n    #\t\t   (dBm)\t   (dBm)"
        print "\n-----------------------------------------------------"
        for rx in xrange(len(spettro) / 2):
            print "\n INPUT %02d\t"%(rx+1),
            for p, pol in enumerate(["X", "Y"]):
                print "   %3.1f\t\t"%(rfpower[(rx*2)+p]),
        print "\n\n"

    except:
        print "\n\nExiting with errors\n"
