#! /usr/bin/env python

import os
from time import sleep, time
import logging
from datetime import datetime
import subprocess


def fndh_status(fndh):
    p = subprocess.Popen(fndh + " status", stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    status = []
    for o in output.split("\n")[:-2]:
        status += [o.split()[3][:-1]]
        status += [float(o.split()[4])]
        status += [int(o.split()[6])]
    return status


def gen_msg(stat):
    ms = ""
    for s in stat:
        ms += str(s) + "\t"
    out = ms[:-1] + "\n"
    return out


if __name__ == "__main__":

    # Use OptionParse to get command-line arguments
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %aavs_save_data [options]")
    parser.add_option("--period", action="store", dest="period",
                      type="int", default="5", help="Acquisition period in seconds [default: 5]")
    parser.add_option("--folder", action="store", dest="folder",
                      type="str", default="./fndh_data/", help="Destination folder [default: ./fndh_data/]")
    parser.add_option("--station", action="store", dest="station",
                      type="str", default="AAVS2", help="Station name [default: AAVS2]")

    (conf, args) = parser.parse_args(argv[1:])

    # Set logging
    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    line_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch = logging.StreamHandler(stdout)
    ch.setFormatter(line_format)
    log.addHandler(ch)

    dest = conf.folder
    if not os.path.exists(dest):
        os.mkdir(dest)
    if not dest[-1] == "/":
        dest += "/"
    fname = dest + datetime.strftime(datetime.utcnow(), "%Y-%m-%d_%H%M%S_FNDH_" + conf.station + "_DATA.tsv")

    f = open(fname, "w")
    try:
        while True:
            record = ""
            tempo = time()
            record += str(tempo) + "\t" + gen_msg(fndh_status(conf.station.lower()))
            f.write(record)
            f.flush()
            #sys.stdout.write("\r")
            print record
            sleep(conf.period)

    except KeyboardInterrupt:
        f.flush()
        f.close()




