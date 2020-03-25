from matplotlib import pyplot as plt
import os
import numpy as np
from matplotlib.gridspec import GridSpec
from aavs_utils import ts_to_datestring, dt_to_timestamp
import datetime
import glob

if __name__ == "__main__":

    # Use OptionParse to get command-line arguments
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
    parser.add_option("--input", action="store", dest="input", type=int,
                      default=1, help="SmartBox Input (default: 1)")
    parser.add_option("--pol", action="store", dest="pol", type=str,
                      default="X", help="Polarization (default: X)")
    parser.add_option("--date", action="store", dest="date",
                      default="2020-03-25", help="Date in YYYY-MM-DD (required)")

    (opts, args) = parser.parse_args(argv[1:])

    try:
        proc_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
        t_start = dt_to_timestamp(proc_date)
        t_stop = dt_to_timestamp(proc_date) + (60 * 60 * 24)
        print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
        print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
    except:
        print "Wrong date format or missing required argument (" + opts.date + ")"
        exit(1)

    plt.ion()

    pol = 0
    if opts.pol.upper() == "Y":
        pol = 1

    if os.path.exists(opts.directory):
        path = opts.directory
        if not path[-1] == "/":
            path = path + "/"
        path += opts.station.upper() + "/"
        lista = sorted(glob.glob(path + ("*Tile-%02d.txt"%(opts.tile))))

        dati = []
        x = []
        xtick = []
        xticklabel = []
        hours = -1
        if len(lista):
            for n, l in enumerate(lista):
                if not n == len(lista) - 1:
                    f_next = lista[n+1].split("/")[-1][:17]
                    #print "next", f_next, dt_to_timestamp(datetime.datetime.strptime(f_next, "%Y-%m-%d_%H%M%S"))
                    if t_start >= dt_to_timestamp(datetime.datetime.strptime(f_next, "%Y-%m-%d_%H%M%S")):
                        pass
                f_date = l.split("/")[-1][:17]
                #print "current: ", f_date, dt_to_timestamp(datetime.datetime.strptime(f_date, "%Y-%m-%d_%H%M%S"))
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
                                        dati += [float(record[3 + ((int(opts.input) - 1) * 2) + pol])]
                                        x += [t_stamp]
                                        if not datetime.datetime.utcfromtimestamp(t_stamp).hour == hours:
                                            xtick += [t_stamp]
                                            xticklabel += [str(datetime.datetime.utcfromtimestamp(t_stamp).hour)]
                                            hours = datetime.datetime.utcfromtimestamp(t_stamp).hour
                                except:
                                    pass
        print "Found %d valid records\n"%(len(dati))
        plt.ioff()
        gs = GridSpec(1, 1, left=0.1, bottom=0.075, top=0.95)
        fig = plt.figure(figsize=(14, 9), facecolor='w')
        #fig = plt.figure(facecolor='w')
        ax = fig.add_subplot(gs[0, 0])

        ax.plot(np.array(range(24 * 60 * 60)) + t_start, np.zeros(24 * 60 * 60), color='w')
        ax.set_xticks((np.array(range(24)) * 60 * 60) + t_start)
        ax.set_xticklabels(np.array(range(24)))

        ax.plot(x, dati, color='b', linestyle='None', marker=".", label="Tile-%02d Input %d Pol %s" % (opts.tile, opts.input, opts.pol))
        #ax.set_xticks(xtick)
        #ax.set_xticklabels(xticklabel)
        ax.set_xlim(x[0], x[-1])
        ax.set_ylim(0, 50)
        ax.set_ylabel("ADC RMS")
        ax.set_xlabel("UTC Time (hours)")
        ax.set_title("Tile-%02d Input %d Pol %s" % (opts.tile, opts.input, opts.pol))
        plt.tight_layout()
        plt.show()
        # if len(dati):
        #     d = np.array(dati)
        #     t = np.transpose(np.array(d))
        #
        #     gs = GridSpec(2 * int(np.ceil(np.sqrt(nplot))) + 1, int(np.ceil(np.sqrt(nplot))), hspace=1.5, wspace=0.6, left=0.06, right=0.96, bottom=0.08, top=0.98)
        #     fig = plt.figure(figsize=(15, 9), facecolor='w')
        #
        #     ax = []
        #     ax2 = []
        #     curr_lines = []
        #     volt_lines = []
        #     ax_title = fig.add_subplot(gs[0, :])
        #     ax_title.plot(np.arange(20), np.arange(20), color="w")
        #     ax_title.set_xlim(-20, 20)
        #     ax_title.set_ylim(-20, 20)
        #     ax_title.set_axis_off()
        #     title = ""
        #     if "aavs2" in opts.station.lower():
        #         title += "Station AAVS2  "
        #     elif "eda2" in opts.station.lower():
        #         title += "Station EDA2  "
        #     title += "SmartBoxes Monitor from " + ts_to_datestring(x[0]) + " to " + ts_to_datestring(x[-1])
        #     ax_title.annotate(title, (-17, 0), fontsize=18, color='black')
        #     ax_title.annotate("Currents of SmartBox Input 1-8", (-16, -20), fontsize=10, color='b')
        #     ax_title.annotate("Currents of SmartBox Input 9-16", (-8, -20), fontsize=10, color='g')
        #     ax_title.annotate("Voltages of SmartBox Input 1-8", (1, -20), fontsize=10, color='r')
        #     ax_title.annotate("Voltages of SmartBox Input 9-16", (8, -20), fontsize=10, color='k')
        #     # xtick = (np.arange(5) * ((x[-1] - x[0]) / 4)) + x[0]
        #     # xticklabel = []
        #     # for c in xtick:
        #     #     xticklabel += [ts_to_datestring(c)[-11:]]
        #     for i in range(nplot):
        #         ax += [fig.add_subplot(gs[1 + 2*(i/4):1 + 2*(i/4 + 1), i % 4])]
        #         ax2 += [ax[i].twinx()]
        #         #ax[i].set_xlabel("time", fontsize=6)
        #         ax[i].set_ylabel("mA")
        #         ax[i].set_ylim(300, 450)
        #         ax[i].set_xlim(x[0], x[-1])
        #         ax[i].set_xticks(xtick)
        #         ax[i].set_xticklabels(xticklabel, fontsize=8, rotation=90)
        #         ax[i].set_title("TILE-%02d"%(i+1), fontsize=10)
        #         ax[i].grid()
        #         ax2[i].set_ylim(0, 60)
        #         ax2[i].set_ylabel("Volt")
        #         line, = ax[i].plot(x, xrange(len(dati)), color="g", linewidth=0.5)
        #         curr_lines += [line]
        #         line, = ax[i].plot(x, xrange(len(dati)), color="b", linewidth=0.5)
        #         curr_lines += [line]
        #         line, = ax2[i].plot(x, xrange(len(dati)), color="k", linewidth=1)
        #         volt_lines += [line]
        #         line, = ax2[i].plot(x, xrange(len(dati)), color="r", linewidth=1)
        #         volt_lines += [line]
        #         if i >= 12:
        #             ax[i].set_xlabel("utc time")
        #
        #     for ant in range(nplot):
        #         curr_lines[2 * ant].set_ydata(np.array(t[6 * (ant + 1)], dtype=np.int))
        #         curr_lines[2 * ant + 1].set_ydata(np.array(t[6 * (ant + 1) - 3], dtype=np.int))
        #         volt_lines[2 * ant].set_ydata(np.array(t[6 * (ant + 1) - 1], dtype=np.float))
        #         volt_lines[2 * ant + 1].set_ydata(np.array(t[6 * (ant + 1) - 4], dtype=np.float))
        #
        #         #print "Plot", 2 * ant, np.array(t[6 * (ant + 1)], dtype=np.float)[0:5], np.array(t[6 * (ant + 1) - 1], dtype=np.float)[0:5]
        #         #print "Plot", 2 * ant + 1, np.array(t[6 * (ant + 1) - 3], dtype=np.float)[0:5], np.array(t[6 * (ant + 1) - 4], dtype=np.float)[0:5]
        #     plt.draw()
        #     plt.show(block=True)

    else:
        print "\nThe given path does not exists! (%s)\n" % opts.directory

