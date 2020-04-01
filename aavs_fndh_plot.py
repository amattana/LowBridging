from matplotlib import pyplot as plt
import os
import numpy as np
from matplotlib.gridspec import GridSpec
from aavs_utils import ts_to_datestring, dt_to_timestamp
import datetime
import glob

nplot = 16

if __name__ == "__main__":

    # Use OptionParse to get command-line arguments
    from optparse import OptionParser
    from sys import argv

    parser = OptionParser(usage="usage: %aavs_fndh_plot [options]")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/fndh_data",
                      help="Directory containing Tiles data (default: /storage/monitoring/fndh_data/)")
    # parser.add_option("--file", action="store", dest="fname",
    #                   default="", help="Input filename with rms data")
    parser.add_option("--station", action="store", dest="station",
                      default="AAVS2", help="Station name (default: AAVS2)")
    parser.add_option("--date", action="store", dest="date",
                      default="2019-12-15", help="Date in YYYY-MM-DD (required)")

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

    if os.path.exists(opts.directory):
        path = opts.directory
        if not path[-1] == "/":
            path = path + "/"
        lista = sorted(glob.glob(path + "*" + opts.station.upper() + "*"))
        dati = []
        x = []
        xtick = []
        xticklabel = []
        step = 0
        #print lista
        for l in lista:
            with open(l) as f:
                data = f.readlines()
            if len(data):
                for d in data:
                    record = d.split()
                    if len(record) == 97:
                        try:
                            tstamp = int(float(record[0]))
                            #print t_stop, tstamp, t_start
                            if t_start <= tstamp <= t_stop:
                                dati += [record]
                                x += [tstamp]
                                if datetime.datetime.utcfromtimestamp(tstamp).hour == step:
                                    xtick += [tstamp]
                                    xticklabel += [str(step)]
                                    step = step + 1
                        except:
                            pass
        print "Found %d valid records\n"%(len(dati))

        if len(dati):
            d = np.array(dati)
            t = np.transpose(np.array(d))

            gs = GridSpec(2 * int(np.ceil(np.sqrt(nplot))) + 1, int(np.ceil(np.sqrt(nplot))), hspace=1.5, wspace=0.6, left=0.06, right=0.96, bottom=0.08, top=0.98)
            fig = plt.figure(figsize=(15, 9), facecolor='w')

            ax = []
            ax2 = []
            curr_lines = []
            volt_lines = []
            ax_title = fig.add_subplot(gs[0, :])
            ax_title.plot(np.arange(20), np.arange(20), color="w")
            ax_title.set_xlim(-20, 20)
            ax_title.set_ylim(-20, 20)
            ax_title.set_axis_off()
            title = ""
            if "aavs2" in opts.station.lower():
                title += "Station AAVS2  "
            elif "eda2" in opts.station.lower():
                title += "Station EDA2  "
            title += "SmartBoxes Monitor from " + ts_to_datestring(x[0]) + " to " + ts_to_datestring(x[-1])
            ax_title.annotate(title, (-17, 0), fontsize=18, color='black')
            ax_title.annotate("Currents of SmartBox Input 1-8", (-16, -20), fontsize=10, color='b')
            ax_title.annotate("Currents of SmartBox Input 9-16", (-8, -20), fontsize=10, color='g')
            ax_title.annotate("Voltages of SmartBox Input 1-8", (1, -20), fontsize=10, color='r')
            ax_title.annotate("Voltages of SmartBox Input 9-16", (8, -20), fontsize=10, color='k')
            # xtick = (np.arange(5) * ((x[-1] - x[0]) / 4)) + x[0]
            # xticklabel = []
            # for c in xtick:
            #     xticklabel += [ts_to_datestring(c)[-11:]]
            for i in range(nplot):
                ax += [fig.add_subplot(gs[1 + 2*(i/4):1 + 2*(i/4 + 1), i % 4])]
                ax2 += [ax[i].twinx()]
                #ax[i].set_xlabel("time", fontsize=6)
                ax[i].set_ylabel("mA")
                ax[i].set_ylim(300, 450)
                ax[i].set_xlim(x[0], x[-1])
                ax[i].set_xticks(xtick)
                ax[i].set_xticklabels(xticklabel, fontsize=8, rotation=90)
                ax[i].set_title("TILE-%02d"%(i+1), fontsize=10)
                ax[i].grid()
                ax2[i].set_ylim(0, 60)
                ax2[i].set_ylabel("Volt")
                line, = ax[i].plot(x, xrange(len(dati)), color="g", linewidth=0.5)
                curr_lines += [line]
                line, = ax[i].plot(x, xrange(len(dati)), color="b", linewidth=0.5)
                curr_lines += [line]
                line, = ax2[i].plot(x, xrange(len(dati)), color="k", linewidth=1)
                volt_lines += [line]
                line, = ax2[i].plot(x, xrange(len(dati)), color="r", linewidth=1)
                volt_lines += [line]
                if i >= 12:
                    ax[i].set_xlabel("utc time")

            for ant in range(nplot):
                curr_lines[2 * ant].set_ydata(np.array(t[6 * (ant + 1)], dtype=np.int))
                curr_lines[2 * ant + 1].set_ydata(np.array(t[6 * (ant + 1) - 3], dtype=np.int))
                volt_lines[2 * ant].set_ydata(np.array(t[6 * (ant + 1) - 1], dtype=np.float))
                volt_lines[2 * ant + 1].set_ydata(np.array(t[6 * (ant + 1) - 4], dtype=np.float))

                #print "Plot", 2 * ant, np.array(t[6 * (ant + 1)], dtype=np.float)[0:5], np.array(t[6 * (ant + 1) - 1], dtype=np.float)[0:5]
                #print "Plot", 2 * ant + 1, np.array(t[6 * (ant + 1) - 3], dtype=np.float)[0:5], np.array(t[6 * (ant + 1) - 4], dtype=np.float)[0:5]
            plt.draw()
            plt.show(block=True)

        else:
            print "\nEmpty file selected!"
    else:
        print "\nThe given file name does not exists!\n"

