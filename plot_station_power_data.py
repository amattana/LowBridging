import matplotlib.pyplot as plt
import numpy as np
import calendar
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.markers import MarkerStyle
import datetime, time
import glob
import os


def dt_to_timestamp(d):
    return calendar.timegm(d.timetuple())


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %aavs_read_data [options]")
    parser.add_option("--station", action="store", dest="station",
                      default="AAVS2", help="Station Name")
    parser.add_option("--start", action="store", dest="start",
                      default="", help="Start time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--stop", action="store", dest="stop",
                      default="", help="Stop time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--date", action="store", dest="date",
                      default="", help="Stop time for filter (YYYY-mm-DD)")

    (opts, args) = parser.parse_args(argv[1:])

    if opts.date:
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
            t_start = dt_to_timestamp(t_date)
            t_stop = dt_to_timestamp(t_date) + (60 * 60 * 24)
            print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
            print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
            data_list = [opts.date]
        except:
            print "Bad date format detected (must be YYYY-MM-DD)"
    else:
        if opts.start:
            try:
                t_start = dt_to_timestamp(datetime.datetime.strptime(opts.start, "%Y-%m-%d_%H:%M:%S"))
                print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
            except:
                print "Bad t_start time format detected (must be YYYY-MM-DD_HH:MM:SS)"
        if opts.stop:
            try:
                t_stop = dt_to_timestamp(datetime.datetime.strptime(opts.stop, "%Y-%m-%d_%H:%M:%S"))
                print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
            except:
                print "Bad t_stop time format detected (must be YYYY-MM-DD_HH:MM:SS)"
        start_date = ts_to_datestring(t_start, "%Y-%m-%d")
        data_list = [start_date]
    if not opts.start and not opts.stop and not opts.date:
        dirs = sorted(os.listdir("."))
        data_list = []
        for d in dirs:
            if d[:2] == "20":
                data_list += []

    plt.ion()
    gs = GridSpec(1, 1, left=0.06, top=0.935, right=0.8)
    fig = plt.figure(figsize=(14, 9), facecolor='w')
    ax = fig.add_subplot(gs[0, 0])

    if "all" in opts.date.lower():
        delta = (dt_to_timestamp(datetime.datetime.utcnow().date() + datetime.timedelta(1)) -
                 dt_to_timestamp(datetime.datetime(2020, 03, 01)))
        delta_h = delta / 3600
        x = np.array(range(delta)) + t_start
    else:
        delta_h = (t_stop - t_start) / 3600
        x = np.array(range(t_stop - t_start)) + t_start

    xticks = np.array(range(delta_h)) * 3600 + t_start
    xticklabels = [f if f != 0 else datetime.datetime.strftime(
        datetime.datetime.utcfromtimestamp(t_start) + datetime.timedelta(n / 24), "%m-%d") for n, f in
                   enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) % 24)]

    div = np.array([1, 2, 3, 4, 6, 8, 12, 24])
    decimation = div[closest(div, len(xticks) / 24)]
    # print decimation, len(xticks)
    xticks = xticks[::decimation]
    xticklabels = xticklabels[::decimation]

    ax.plot(x, x, color='w')
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)

    tiles = range(1, 17)
    for pol in ["X", "Y"]:
        for t in tiles:
            print "Plotting Tile-%02d, Pol-%s" % (t, pol)
            ax.cla()
            ax.set_xticks(xticks)
            ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)
            flist = sorted(glob.glob(start_date + "/" + opts.station + "/power_data/" + opts.station + "_POWER_" +
                                     start_date + "_TILE-%02d_ANT*_POL-%s_*.txt" % (t, pol)))
            y0 = 0
            for n, f in enumerate(flist):
                with open(f) as g:
                    data = g.readlines()
                asse_x = []
                dati = []
                for d in data[1:]:
                    asse_x += [int(d.split()[0])]
                    dati += [float(d.split()[3])]
                dati = np.array(dati) - dati[0] - (1 * n)
                # if not n:
                #     y0 = dati[0]
                #     dati = dati - y0
                ax.plot(asse_x, dati, label=f[f.rfind("TILE"):f.rfind("TILE") + 15], linestyle='None', marker=".", markersize=2)
            if opts.station == "AAVS2":
                ax.set_ylim(-20, y0+3)
            else:
                ax.set_ylim(-20, y0+3)
            ax.set_xlim(xticks[0], xticks[-1])
            ax.set_title("Tile-%02d  Pol %s" % (t, pol))
            ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0., fontsize=14, markerscale=8)
            ax.grid()
            #fig.subplots_adjust(right=0.86)
            if not os.path.isdir(start_date + "/" + opts.station + "/tile_pics/"):
                os.mkdir(start_date + "/" + opts.station + "/tile_pics/")
            if not os.path.isdir(start_date + "/" + opts.station + "/tile_pics/Pol-" + pol):
                os.mkdir(start_date + "/" + opts.station + "/tile_pics/Pol-" + pol)
            fig.savefig(start_date + "/" + opts.station + "/tile_pics/Pol-" + pol + "/" + start_date + "_" +
                        opts.station + "_Tile-%02d_Pol-" % t + pol + ".png")
