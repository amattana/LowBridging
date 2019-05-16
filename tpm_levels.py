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


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--board",
                      dest="board",
                      default="",
                      help="The board IP")

    (options, args) = parser.parse_args()

    board_ip = options.board

    freqs, spettro, rawdata, rms, rfpower = get_raw_meas(tpm_obj(board_ip), debug=False)

    print "\n\nTPM INPUT\tPol-X Level\tPol-Y Level\n----------------------------------------------------------"
    for rx in xrange(len(spettro) / 2):
        print "\nINPUT %02d\t\t"%(rx+1),
        for p, pol in enumerate(["X", "Y"]):
            print "%3.1f dBm\t\t"%(rms[(rx*2)+p]),
    print

