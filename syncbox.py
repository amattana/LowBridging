#!/usr/bin/env python

from valon_synth import Synthesizer as Sync
from optparse import OptionParser
import time

OUT_A = 0 # frequency output channel A
OUT_B = 8 # frequnecy output channel B 

EXTERNAL = 1 # external 10 MHz reference
INTERNAL = 0 # internal 10 MHz reference

if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("--freq",
                      dest="freq",
                      default=0,
                      help="Set Frequency in MHz")

    parser.add_option("--reference", 
                      dest="reference",
                      default="external",
                      help="PLL reference (external/internal) [def: external]")

    parser.add_option("--save", action="store_true",
                      dest="save",
                      default=False,
                      help="Save configuration on internal flash memory")

    (options, args) = parser.parse_args()

    try:
        sync = Sync("/dev/ttyUSB0")
        print "\nSuccesfully connected to the Valon Synthesizer on port /dev/ttyUSB0\n"
    except:
        print "\nCannot connect to the Valon Synthesizer on port /dev/ttyUSB0\n"
        exit(0)

    if not options.freq == 0:
        sync.set_frequency(OUT_A, int(options.freq))
        sync.set_frequency(OUT_B, int(options.freq))

    if options.reference == "external":
        sync.set_ref_select(EXTERNAL)
    else:
        sync.set_ref_select(INTERNAL)

    fa = sync.get_frequency(OUT_A)
    time.sleep(0.3)
    fb = sync.get_frequency(OUT_B)
    time.sleep(0.3)
    fref = sync.get_ref_select()
    time.sleep(0.3)
    la = sync.get_rf_level(OUT_A)
    time.sleep(0.3)
    lb = sync.get_rf_level(OUT_B)
    time.sleep(0.3)

    print "Channel A Output Frequency:", fa, "MHz with level", la, "dBm"
    print "Channel B Output Frequency:", fb, "MHz with level", lb, "dBm"
    if fref == 0:
        print "\nReference Input Signal set to INTERNAL\n"
    else:
        print "\nReference Input Signal set to EXTERNAL\n"

    if options.save:
        saved = sync.flash()
        if saved:
            print "\nConfiguration correctly saved!"
        else:
            print "\nConfiguration not saved!!!"














