import sys

from matplotlib import pyplot as plt
import glob
import os
import datetime
import numpy as np
from aavs_utils import ts_to_datestring, mro_daily_weather, diclist_to_array, dt_to_timestamp, closest, get_sbtemp
from matplotlib.markers import MarkerStyle
from matplotlib.gridspec import GridSpec


COLORS = ['b', 'g', 'orange', 'y', 'p', 'k', 'm', 'dimgrey']

if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv
    parser = OptionParser(usage="usage: %aavs_plot_power [options]")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/power/",
                      help="Directory containing Tiles data (default: /storage/monitoring/power/)")
    parser.add_option("--station", action="store", dest="station",
                      default="AAVS2", help="Station name (default: AAVS2)")
    parser.add_option("--start", action="store", dest="start",
                      default="", help="Start time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--stop", action="store", dest="stop",
                      default="", help="Stop time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--date", action="store", dest="date",
                      default="", help="Date in YYYY-MM-DD (required)")
    parser.add_option("--title", action="store", dest="title",
                      default="", help="Plot title")
    parser.add_option("--antenna", action="store", dest="antenna", type=int,
                      default=0, help="Antenna Name")
    parser.add_option("--yrange", action="store", dest="yrange",
                      default="-10,25", help="Y dB range to plot")
    parser.add_option("--filter", action="store", dest="filter",
                      default="", help="Filter for input files")
    parser.add_option("--spacer", action="store", dest="spacer", type=float,
                      default=1, help="Spacer between antenna plot in dB (default: 1)")
    parser.add_option("--weather", action="store_true", dest="weather",
                      default=False, help="Add weather info (if available)")
    parser.add_option("--noline", action="store_true", dest="noline",
                      default=False, help="Do not plot lines but just markers")
    parser.add_option("--donotnormalize", action="store_true", dest="donotnormalize",
                      default=False, help="Do not normalize at first value")
    (opts, args) = parser.parse_args(argv[1:])

    path = opts.directory
    if not path[-1] == "/":
        path += "/"

    if opts.date:
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
            t_start = dt_to_timestamp(t_date)
            t_stop = dt_to_timestamp(t_date) + (60 * 60 * 24)
            sys.stdout.write("\nStart Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start))
            sys.stdout.write("\nStop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop))
        except:
            sys.stdout.write("\nBad date format detected (must be YYYY-MM-DD)")
    else:
        if opts.start:
            try:
                t_start = dt_to_timestamp(datetime.datetime.strptime(opts.start, "%Y-%m-%d_%H:%M:%S"))
                sys.stdout.write("\nStart Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start))
            except:
                sys.stdout.write("\nBad t_start time format detected (must be YYYY-MM-DD_HH:MM:SS)")
        if opts.stop:
            try:
                t_stop = dt_to_timestamp(datetime.datetime.strptime(opts.stop, "%Y-%m-%d_%H:%M:%S"))
                sys.stdout.write("\nStop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop))
            except:
                sys.stdout.write("\nBad t_stop time format detected (must be YYYY-MM-DD_HH:MM:SS)")

    sys.stdout.write("\n")
    sys.stdout.flush()
    plt.ioff()
    if opts.weather:
        gs = GridSpec(1, 1, left=0.1, right=0.72, bottom=0.14, top=0.96)
    else:
        gs = GridSpec(1, 1, left=0.12, right=0.92, bottom=0.14, top=0.96)
    fig = plt.figure(figsize=(14, 8), facecolor='w')
    plt.rc('axes', axisbelow=True)
    ax = fig.add_subplot(gs[0, 0])
    yticks = []
    yticklabels = []
    if opts.filter == "":
        lista = sorted(glob.glob(path + "*.txt"))
    else:
        sys.stdout.write("\nLooking for files: %s" % (path + opts.filter))
        lista = sorted(glob.glob(path + opts.filter))
        sys.stdout.write("Found %d Antenna Files" % len(lista))
    for k, l in enumerate(lista):
        #print "Reading ", l
        if os.path.exists(l):
            with open(l) as f:
                data = f.readlines()
            dati = []
            tempi = []
            eq_value = 0
            for d in data:
                try:
                    dato = float(d.split("\t")[3])
                    tempi += [int(d.split("\t")[0])]
                    if not opts.donotnormalize:
                        if not len(dati):
                            eq_value = dato
                    dati += [dato - eq_value + (k * opts.spacer)]
                except:
                    #print "Error:", d
                    pass
            if len(tempi) > 0:
                if opts.noline:
                    ax.plot(tempi, dati, label=l, lw=0 , marker=".", markersize=10, zorder=3, color=COLORS[k % 8])
                else:
                    ax.plot(tempi, dati, label=l, lw=1, zorder=3, color=COLORS[k % 8]) # , marker=".", markersize=1)
                yticks += [(k * opts.spacer)]
                yticklabels += [l[l.rfind("ANT"): l.rfind("_")]]
                # if not k:
                #     t_start = tempi[0]
                #     t_stop = tempi[-1]
                # else:
                #     t_start = np.minimum(t_start, tempi[0])
                #     t_stop = np.maximum(t_stop, tempi[-1])
        else:
            sys.stdout.write("\nMissing file: ", l)
            break
    sys.stdout.flush()
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels, fontsize=9)
    ax.set_axisbelow(True)
    ax.grid(color='gray', linestyle='dashed', zorder=0)

    ax.set_xlabel("UTC Time", fontsize=10)
    delta_h = int((t_stop - t_start) / 3600)
    x = np.array(range(t_stop - t_start + 100)) + t_start

    xticks = np.array(range(delta_h)) * 3600 + t_start
    xticklabels = [f if f != 0 else datetime.datetime.strftime(
        datetime.datetime.utcfromtimestamp(t_start) + datetime.timedelta(
            (datetime.datetime.utcfromtimestamp(t_start).hour + n) / 24), "%Y-%m-%d") for n, f in
                   enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) % 24)]

    decimation = 1
    offset = 0
    try:
        offset = decimation - int(xticklabels[0]) % decimation
    except:
        pass
    xticks = xticks[offset::decimation]
    xticklabels = xticklabels[offset::decimation]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)

    ax.set_xlim(t_start, t_stop)
    ax_db = ax.twinx()
    ax_db.set_ylabel("dB")
    ax_db.set_yticks((np.array(range(200)) - 100 ) )#)/ 10.)
    ax.set_ylim(float(opts.yrange.split(",")[0]), float(opts.yrange.split(",")[1]))
    ax_db.set_ylim(float(opts.yrange.split(",")[0]), float(opts.yrange.split(",")[1]))
    ax_db.tick_params(axis='y', labelcolor='k')
    ax_db.spines["right"].set_position(("axes", 1))
    ax_db.set_axisbelow(True)
    ax_db.grid(color='gray', linestyle='dashed', zorder=0)

    if opts.title == "":
        ax.set_title(opts.directory)
    else:
        ax.set_title(opts.title)
    if opts.weather:
        sys.stdout.write("\nLoading Temperature data...")
        with open("/storage/monitoring/weather/MRO_TEMPERATURE.csv") as s:
            data = s.readlines()
        temp_time = []
        temp_data = []
        for s in data:
            if s[0:2] == "0x":
                tstamp = dt_to_timestamp(datetime.datetime.strptime(s.split(",")[1], " %Y-%m-%d %H:%M:%S.%f"))
                if t_start <= tstamp <= t_stop:
                    temp_time += [tstamp]
                    temp_data += [float(s.split(",")[2])]
                if tstamp > t_stop:
                    break
        sys.stdout.write("done! Found %d records\n" % len(temp_data))
        sys.stdout.flush()

        sys.stdout.write("Loading Rain data...")
        with open("/storage/monitoring/weather/MRO_RAIN.csv") as s:
            data = s.readlines()
        rain_time = []
        rain_data = []
        for s in data:
            if s[0:2] == "0x":
                tstamp = dt_to_timestamp(datetime.datetime.strptime(s.split(",")[1], " %Y-%m-%d %H:%M:%S.%f"))
                if t_start <= tstamp <= t_stop:
                    rain_time += [tstamp]
                    rain_data += [float(s.split(",")[2])]
                if tstamp > t_stop:
                    break
        sys.stdout.write("done! Found %d records\n" % len(rain_data))
        sys.stdout.flush()

        sys.stdout.write("Loading Wind data...")
        wind_files = sorted(glob.glob("/storage/monitoring/weather/MRO_WINDSPEED_20*.csv"))
        wind_time = []
        wind_data = []
        for wf in wind_files:
            if datetime.datetime.strptime(ts_to_datestring(t_stop, "%Y-%m"), "%Y-%m") >= datetime.datetime.strptime(wf[-11:-4], "%Y-%m"):
                if datetime.datetime.strptime(ts_to_datestring(t_start, "%Y-%m"), "%Y-%m") <= \
                        datetime.datetime.strptime(wf[-11:-4], "%Y-%m"):
                    with open(wf) as s:
                        data = s.readlines()
                    for s in data:
                        if s[0:2] == "0x":
                            try:
                                tstamp = dt_to_timestamp(datetime.datetime.strptime(s.split(",")[1], " %Y-%m-%d %H:%M:%S.%f"))
                                if t_start <= tstamp <= t_stop:
                                    wind_time += [tstamp]
                                    wind_data += [float(s.split(",")[2])]
                                if tstamp > t_stop:
                                    break
                            except:
                                pass
        sys.stdout.write("done! Found %d records\n" % len(wind_data))
        sys.stdout.flush()

        sys.stdout.write("Loading Solar data...")
        with open("/storage/monitoring/weather/MRO_SOLAR.csv") as s:
            data = s.readlines()
        sun_time = []
        sun_data = []
        for s in data:
            if s[0:2] == "0x":
                tstamp = dt_to_timestamp(datetime.datetime.strptime(s.split(",")[1], " %Y-%m-%d %H:%M:%S.%f"))
                if t_start <= tstamp <= t_stop:
                    sun_time += [tstamp]
                    sun_data += [float(s.split(",")[2])]
                if tstamp > t_stop:
                    break
        sys.stdout.write("done! Found %d records\n" % len(sun_data))
        sys.stdout.flush()

        if len(wind_data):
            ax_wind = ax.twinx()
            ax_wind.plot(wind_time, wind_data, color='orange', lw=1.5)
            ax_wind.set_yticks(range(0, 201, 5))
            ax_wind.set_ylim(0, 200)
            ax_wind.set_ylabel('WindSpeed (mm)', color='orange')
            ax_wind.tick_params(axis='y', labelcolor='orange')
            ax_wind.spines["right"].set_position(("axes", 1.32))

        if len(sun_data):
            ax_sun = ax.twinx()
            ax_sun.plot(sun_time, sun_data, color='k', lw=1.5)
            ax_sun.set_ylim(0, 5000)
            ax_sun.set_ylabel('Solar Radiation (W/m^2)', color='k')
            ax_sun.tick_params(axis='y', labelcolor='k')
            ax_sun.spines["right"].set_position(("axes", 1.16))

        if len(temp_data):
            ax_temp = ax.twinx()
            ax_temp.plot(temp_time, temp_data, color='r', lw=1.5)
            ax_temp.set_yticks(range(0, 201, 5))
            ax_temp.set_ylim(0, 200)
            ax_temp.set_ylabel('Temperature (Celsius degrees)', color='r')
            ax_temp.tick_params(axis='y', labelcolor='r')
            ax_temp.spines["right"].set_position(("axes", 1.08))

        if len(rain_data):
            ax_rain = ax.twinx()
            ax_rain.plot(rain_time, rain_data, color='steelblue', lw=2)
            ax_rain.set_ylim(0, 10)
            ax_rain.set_ylabel('Rain (mm)', color='steelblue')
            ax_rain.tick_params(axis='y', labelcolor='steelblue')
            ax_rain.spines["right"].set_position(("axes", 1.24))

    plt.show()
