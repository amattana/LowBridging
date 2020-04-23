from matplotlib import pyplot as plt
import os
import numpy as np
from matplotlib.gridspec import GridSpec
#from aavs_utils import ts_to_datestring, dt_to_timestamp
import datetime
import glob
import calendar


def dt_to_timestamp(d):
    return calendar.timegm(d.timetuple())


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


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
                      default="", help="Date in YYYY-MM-DD (required)")
    parser.add_option("--start", action="store", dest="start",
                      default="", help="Start time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--stop", action="store", dest="stop",
                      default="", help="Stop time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--tile", action="store", dest="tile", type=str,
                      default="all", help="Comma separated Tile Numbers (default: all)")

    (opts, args) = parser.parse_args(argv[1:])

    nplot = 16
    tiles = []
    if opts.tile:
        if "all" in opts.tile:
            tiles = np.arange(16)
        else:
            tiles = [x-1 for x in np.array(opts.tile.split(","), dtype=int)]
        nplot = len(tiles)

    t_start = 0
    t_stop = 0
    if opts.date:
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
    else:
        if opts.start:
            try:
                t_start = dt_to_timestamp(datetime.datetime.strptime(opts.start, "%Y-%m-%d_%H:%M:%S"))
                print "Start Time:  " + ts_to_datestring(t_start)
            except:
                print "Bad t_start time format detected (must be YYYY-MM-DD_HH:MM:SS)"
        if opts.stop:
            try:
                t_stop = dt_to_timestamp(datetime.datetime.strptime(opts.stop, "%Y-%m-%d_%H:%M:%S"))
                print "Stop  Time:  " + ts_to_datestring(t_stop)
            except:
                print "Bad t_stop time format detected (must be YYYY-MM-DD_HH:MM:SS)"

    plt.ion()

    if os.path.exists(opts.directory):
        path = opts.directory
        if not path[-1] == "/":
            path = path + "/"
        lista = sorted(glob.glob(path + "2*" + opts.station.upper() + "*"))
        dati = []
        tempi = []
        step = 0
        for l in lista:
            with open(l) as f:
                data = f.readlines()
            if len(data):
                for d in data:
                    record = d.split()
                    if len(record) == 97:
                        try:
                            tstamp = int(float(record[0]))
                            if t_start <= tstamp <= t_stop:
                                dati += [record]
                                tempi += [tstamp]
                        except:
                            pass
        print "Found %d valid records\n"%(len(dati))

        if len(dati):
            d = np.array(dati)
            t = np.transpose(np.array(d))

            gs = GridSpec((2 * int(np.ceil(np.sqrt(nplot)))) + 1, int(np.ceil(np.sqrt(nplot))), hspace=1.5,
                          wspace=0.1 + (int(np.ceil(np.sqrt(nplot))))/10., left=0.06, right=0.96, bottom=0.08, top=0.98)
            fig = plt.figure(figsize=(15, 9), facecolor='w')

            if "all" in opts.date.lower():
                delta = (dt_to_timestamp(datetime.datetime.utcnow().date() + datetime.timedelta(1)) -
                         dt_to_timestamp(datetime.datetime(2020, 01, 01)))
                delta_h = delta / 3600
                x = np.array(range(delta)) + t_start
            else:
                delta_h = (t_stop - t_start) / 3600
                x = np.array(range(t_stop - t_start)) + t_start

            xticks = np.array(range(delta_h)) * 3600 + t_start
            xticklabels = [f if f != 0 else datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(t_start) + datetime.timedelta(n/24), "%m-%d") for n, f in enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) % 24)]

            div = np.array([1, 2, 3, 4, 6, 8, 12, 24])
            decimation = div[closest(div, len(xticks)/24)]
            #print decimation, len(xticks)
            xticks = xticks[::decimation]
            xticklabels = xticklabels[::decimation]

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
            for i in range(nplot):
                #print nplot, 1 + 2*(i/int(np.ceil(np.sqrt(nplot)))), 1 + 2*(i/int(np.ceil(np.sqrt(nplot))) + 1),  i % int(np.ceil(np.sqrt(nplot)))
                ax += [fig.add_subplot(gs[1 + 2*(i/int(np.ceil(np.sqrt(nplot)))):1 + 2*(i/int(np.ceil(np.sqrt(nplot))) + 1), i % int(np.ceil(np.sqrt(nplot)))])]
                ax2 += [ax[i].twinx()]
                #ax[i].set_xlabel("time", fontsize=6)
                ax[i].set_ylabel("mA")
                ax[i].set_ylim(300, 450)
                ax[i].set_xlim(x[0], x[-1])
                ax[i].set_xticks(xticks)
                #ax[i].set_xticklabels((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) %
                #                      24, rotation=90, fontsize=8)
                ax[i].set_xticklabels(xticklabels, rotation=90, fontsize=8)
                ax[i].set_title("TILE-%02d"%(tiles[i]+1), fontsize=10)
                ax[i].grid()
                ax2[i].set_ylim(0, 60)
                ax2[i].set_ylabel("Volt")
                line, = ax[i].plot(tempi, xrange(len(dati)), color="g", linewidth=0.5)
                curr_lines += [line]
                line, = ax[i].plot(tempi, xrange(len(dati)), color="b", linewidth=0.5)
                curr_lines += [line]
                line, = ax2[i].plot(tempi, xrange(len(dati)), color="k", linewidth=1)
                volt_lines += [line]
                line, = ax2[i].plot(tempi, xrange(len(dati)), color="r", linewidth=1)
                volt_lines += [line]
                if i >= 12:
                    ax[i].set_xlabel("utc time")

            for n, ant in enumerate(tiles):
                curr_lines[2 * n].set_ydata(np.array(t[6 * (ant + 1)], dtype=np.int))
                curr_lines[2 * n + 1].set_ydata(np.array(t[6 * (ant + 1) - 3], dtype=np.int))
                volt_lines[2 * n].set_ydata(np.array(t[6 * (ant + 1) - 1], dtype=np.float))
                volt_lines[2 * n + 1].set_ydata(np.array(t[6 * (ant + 1) - 4], dtype=np.float))

                #print "Plot", 2 * ant, np.array(t[6 * (ant + 1)], dtype=np.float)[0:5], np.array(t[6 * (ant + 1) - 1], dtype=np.float)[0:5]
                #print "Plot", 2 * ant + 1, np.array(t[6 * (ant + 1) - 3], dtype=np.float)[0:5], np.array(t[6 * (ant + 1) - 4], dtype=np.float)[0:5]
            plt.draw()
            plt.ioff()
            #plt.show(block=True)
            plt.show()

        else:
            print "\nEmpty file selected!"
    else:
        print "\nThe given file name does not exists!\n"

