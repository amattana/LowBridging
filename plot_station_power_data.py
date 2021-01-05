import matplotlib.pyplot as plt
import numpy as np
import calendar
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.markers import MarkerStyle
import datetime, time
import glob
import os
import sys
import warnings
warnings.filterwarnings("ignore")
ERASE_LINE = '\x1b[2K'

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
    parser.add_option("--dir", action="store", dest="dir",
                      default="", help="Directory containing data")
    parser.add_option("--freq", action="store", dest="freq",
                      default="160", help="Frequency of interest")

    (opts, args) = parser.parse_args(argv[1:])

    data_dir = "/storage/monitoring/power/station_power/"
    if not opts.dir == "":
        data_dir += opts.dir + "/"

    freq = opts.freq
    start_date = ""

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
                t_stop = dt_to_timestamp(datetime.datetime.strptime(opts.stop, "%Y-%m-%d_%H:%M:%S")) + 3600
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
    if opts.freq == "ecg":
        gs = GridSpec(1, 1, left=0.06, top=0.935, right=0.98)
    else:
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
    #print xticks
    #print xticklabels
    xticks = xticks[::decimation]
    xticklabels = xticklabels[::decimation]

    ax.plot(x, x, color='w')
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)

    if freq.lower() == "ecg":
        dirlist = sorted(glob.glob(data_dir + start_date + "/" + opts.station + "_*MHz"))
        for ant in range(256):
            for pol in ["X", "Y"]:
                yticks = []
                yticklabels = []
                sys.stdout.write(ERASE_LINE + "\r[%d/256] Processing Antenna: %d" % (ant + 1, ant + 1))
                sys.stdout.flush()
                ax.cla()
                ax.set_xticks(xticks)
                ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)
                for dn, dl in enumerate(dirlist):
                    f = glob.glob(dl + "/power_data/" + opts.station + "_POWER_" + start_date +
                                  "_TILE-*_ANT-%03d_POL-%s_*.txt" % (ant + 1, pol))
                    if len(f):
                        if os.path.exists(f[0]):
                            with open(f[0]) as g:
                                data = g.readlines()
                            asse_x = []
                            dati = []
                            for d in data[1:]:
                                asse_x += [int(d.split()[0])]
                                dati += [float(d.split()[3])]
                            dati = np.array(dati) - dati[0] - (1 * dn)
                            ax.plot(asse_x, dati, linestyle='None', marker=".", markersize=2)
                            yticks += [-dn]
                            yticklabels += [dl[-6:-3]]
                ax.set_xlabel("UTC time")
                ax.set_ylabel("MHz")
                ax.set_xlim(xticks[0], xticks[-1])
                ax.set_ylim(-(len(dirlist)) - 2, 2)
                ax.set_yticks(yticks)
                ax.set_yticklabels(yticklabels)
                ax.set_title("%s Antenna %03d Pol %s" % (opts.station, ant + 1, pol))
                ax.grid()
                #fig.subplots_adjust(right=0.86)
                opath = data_dir + start_date + "/ecg_pics/"
                if not os.path.isdir(opath):
                    os.mkdir(opath)
                if not os.path.isdir(opath + "Pol-" + pol):
                    os.mkdir(opath + "Pol-" + pol)
                fig.savefig(opath + "Pol-" + pol + "/" + start_date + "_" + opts.station + "_ANT-%03d_Pol-%s.png" %
                            (ant + 1, pol))
        print

    else:
        tiles = range(1, 17)
        if freq.lower() == "all":
            dirlist = sorted(glob.glob(data_dir + start_date + "/" + opts.station + "_*MHz"))
        else:
            dirlist = [data_dir + start_date + "/" + opts.station + "_" + str(freq) + "MHz"]

        print
        for dlcnt, dl in enumerate(dirlist):
            sys.stdout.write(ERASE_LINE + "\r[%d/%d] Processing directory: %s" % (dlcnt + 1, len(dirlist), dl))
            sys.stdout.flush()
            freq = dl[-6:-3]
            for pol in ["X", "Y"]:
                for t in tiles:
                    sys.stdout.write(ERASE_LINE + "\r[%d/%d] Plotting Tile-%02d, Pol-%s" %
                                     (dlcnt + 1, len(dirlist), t, pol))
                    sys.stdout.flush()
                    ax.cla()
                    ax.set_xticks(xticks)
                    ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)
                    flist = sorted(glob.glob(dl + "/power_data/" + opts.station + "_POWER_" + start_date +
                                             "_TILE-%02d_ANT*_POL-%s_*.txt" % (t, pol)))
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
                    ax.set_title("%s Tile-%02d  Pol %s  Frequency %s MHz" % (opts.station, t, pol, freq))
                    ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0., fontsize=14, markerscale=8)
                    ax.grid()
                    #fig.subplots_adjust(right=0.86)
                    opath = dl + "/tile_pics/"
                    if not os.path.isdir(opath):
                        os.mkdir(opath)
                    if not os.path.isdir(opath + "Pol-" + pol):
                        os.mkdir(opath + "Pol-" + pol)
                    fig.savefig(opath + "Pol-" + pol + "/" + start_date + "_" + opts.station + "_Tile-%02d_"  % t + freq +
                                "MHz_Pol-" + pol + ".png")
            sys.stdout.write(ERASE_LINE + "\r[%d/%d] Processed directory: %s\n" % (dlcnt + 1, len(dirlist), dl))
            sys.stdout.flush()
