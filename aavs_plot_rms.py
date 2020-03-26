from matplotlib import pyplot as plt
import os
import numpy as np
from matplotlib.gridspec import GridSpec
from aavs_utils import ts_to_datestring, dt_to_timestamp
import datetime
import glob

t_start = 0
t_stop = 0


def read_data(path, tile, channel, pol):
    global t_start, t_stop
    p = 0
    if pol.upper() == "Y":
        p = 1
    lista = sorted(glob.glob(path + ("*Tile-%02d.txt" % (tile))))
    dati = []
    x = []
    if len(lista):
        for n, l in enumerate(lista):
            if not n == len(lista) - 1:
                f_next = lista[n + 1].split("/")[-1][:17]
                # print "next", f_next, dt_to_timestamp(datetime.datetime.strptime(f_next, "%Y-%m-%d_%H%M%S"))
                if t_start >= dt_to_timestamp(datetime.datetime.strptime(f_next, "%Y-%m-%d_%H%M%S")):
                    pass
            f_date = l.split("/")[-1][:17]
            # print "current: ", f_date, dt_to_timestamp(datetime.datetime.strptime(f_date, "%Y-%m-%d_%H%M%S"))
            if t_stop <= dt_to_timestamp(datetime.datetime.strptime(f_date, "%Y-%m-%d_%H%M%S")):
                pass
            else:
                with open(l) as f:
                    data = f.readlines()
                if len(data):
                    for d in data:
                        record = d.split()
                        if len(record) == 35:
                            try:
                                t_stamp = int(float(record[0]))
                                if t_start <= t_stamp <= t_stop:
                                    dati += [float(record[3 + ((channel - 1) * 2) + p])]
                                    x += [t_stamp]
                            except:
                                pass
    return x, dati


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv

    parser = OptionParser(usage="usage: %aavs_plot_rms [options]")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/rms",
                      help="Directory containing RMS data (default: /storage/monitoring/rms/)")
    # parser.add_option("--file", action="store", dest="fname",
    #                   default="", help="Input filename with rms data")
    parser.add_option("--station", action="store", dest="station",
                      default="AAVS2", help="Station name (default: AAVS2)")
    parser.add_option("--tile", action="store", dest="tile", type=int,
                      default=1, help="Tile Number (default: 1)")
    parser.add_option("--input", action="store", dest="channel", type=int,
                      default=1, help="SmartBox Input (default: 1)")
    parser.add_option("--pol", action="store", dest="pol", type=str,
                      default="X", help="Polarization (default: X)")
    parser.add_option("--list", action="store", dest="lista", type=str,
                      default="", help="List of signals to plot, a string where tuple element are comma separated 'tile-input-pol,tile-input-pol'")
    parser.add_option("--date", action="store", dest="date",
                      default="all", help="Date in YYYY-MM-DD (required, default 'all')")

    (opts, args) = parser.parse_args(argv[1:])

    try:
        if "all" in opts.date.lower():
            proc_date = datetime.datetime.strptime("2020-03-01", "%Y-%m-%d")
            t_start = dt_to_timestamp(proc_date)
            t_stop = dt_to_timestamp(datetime.datetime.utcnow())
            print "All data available will be processed!"
        else:
            proc_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
            t_start = dt_to_timestamp(proc_date)
            t_stop = dt_to_timestamp(proc_date) + (60 * 60 * 24)
            print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
            print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
    except:
        print "Wrong date format or missing required argument (" + opts.date + ")"
        exit(1)

    plt.ion()

    if os.path.exists(opts.directory):
        path = opts.directory
        if not path[-1] == "/":
            path = path + "/"
        path += opts.station.upper() + "/"

        plt.ion()
        gs = GridSpec(1, 1, left=0.1, bottom=0.075, top=0.95, right=0.98)
        fig = plt.figure(figsize=(12, 7), facecolor='w')
        ax = fig.add_subplot(gs[0, 0])

        if "all" in opts.date.lower():
            delta = (dt_to_timestamp(datetime.datetime.utcnow().date() + datetime.timedelta(1)) -
                     dt_to_timestamp(datetime.datetime(2020, 03, 01)))
            delta_h = delta / 3600
            x = np.array(range(delta)) + t_start
        else:
            delta_h = 24
            x = np.array(range(24 * 60 * 60)) + t_start
        xticks = np.array(range(delta_h)) * 3600 + t_start
        ax.plot(x, x, color='w')
        ax.set_xticks(xticks)
        ax.set_xticklabels(np.array(range(delta_h)) % 24)

        if not opts.lista:
            data_list = [(opts.tile, opts.channel, pol)]
        else:
            data_list = []
            for d in opts.lista.split(","):
                data_list += [(int(d.split("-")[0]), int(d.split("-")[1]), d.split("-")[2])]

        for d in data_list:
            x, dati = read_data(path, d[0], d[1], d[2])
            print "Found %d valid records for Tile-%02d Input #%02d Pol-%s\n" % (len(dati), d[0], d[1], d[2].upper())
            ax.plot(x, dati, linestyle='None', marker=".", markersize=2,
                    label="Tile-%02d Input %02d Pol %s" % (d[0], d[1], d[2].upper()))

        ax.set_xlim(x[0], x[-1])
        ax.set_ylim(0, 50)
        ax.set_ylabel("ADC RMS")
        ax.set_xlabel("UTC Time (hours)")
        ax.set_title("ADC RMS     Start Time: %s      End Time: %s" % (ts_to_datestring(x[0]), ts_to_datestring(x[-1])))
        ax.legend(markerscale=8)
        plt.show()

    else:
        print "\nThe given path does not exists! (%s)\n" % opts.directory

