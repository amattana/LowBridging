from matplotlib import pyplot as plt
import glob
import os
import datetime
import numpy as np
from aavs_utils import ts_to_datestring, mro_daily_weather, diclist_to_array, dt_to_timestamp, closest, get_sbtemp
from matplotlib.markers import MarkerStyle
from matplotlib.gridspec import GridSpec


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
    parser.add_option("--antenna", action="store", dest="antenna", type=int,
                      default=0, help="Antenna Name")
    parser.add_option("--weather", action="store_true", dest="weather",
                      default=False, help="Add weather info (if available)")
    (opts, args) = parser.parse_args(argv[1:])


    path = opts.directory
    if not path[-1] == "/":
        path += "/"

    # if opts.date:
    #     try:
    #         t_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
    #         t_start = dt_to_timestamp(t_date)
    #         t_stop = dt_to_timestamp(t_date) + (60 * 60 * 24)
    #         print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
    #         print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
    #     except:
    #         print "Bad date format detected (must be YYYY-MM-DD)"
    # else:
    #     if opts.start:
    #         try:
    #             t_start = dt_to_timestamp(datetime.datetime.strptime(opts.start, "%Y-%m-%d_%H:%M:%S"))
    #             print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
    #         except:
    #             print "Bad t_start time format detected (must be YYYY-MM-DD_HH:MM:SS)"
    #     if opts.stop:
    #         try:
    #             t_stop = dt_to_timestamp(datetime.datetime.strptime(opts.stop, "%Y-%m-%d_%H:%M:%S"))
    #             print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
    #         except:
    #             print "Bad t_stop time format detected (must be YYYY-MM-DD_HH:MM:SS)"
    #

    plt.ioff()
    gs = GridSpec(1, 1, left=0.1, right=0.72, bottom=0.12, top=0.96)
    fig = plt.figure(figsize=(14, 8), facecolor='w')
    ax = fig.add_subplot(gs[0, 0])
    yticks = []
    yticklabels = []
    lista = sorted(glob.glob(path + "*.txt"))
    print "Found", len(lista), "Antenna Files"
    for k, l in enumerate(lista):
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
                    if not len(dati):
                        eq_value = dato
                    dati += [dato - eq_value + k]
                except:
                    pass
            ax.plot(tempi, dati, label=l, lw=0, marker=".", markersize=1)
            yticks += [k]
            yticklabels += [l[l.rfind("ANT"): l.rfind("ANT")+13]]
        else:
            print "Missing file: ", l
            break
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels, fontsize=9)
    ax.grid()



    ax.set_xlabel("UTC Time", fontsize=10)
    t_start = tempi[0]
    t_stop = tempi[-1]
    delta_h = (t_stop - t_start) / 3600
    x = np.array(range(t_stop - t_start + 100)) + t_start

    xticks = np.array(range(delta_h)) * 3600 + t_start
    xticklabels = [f if f != 0 else datetime.datetime.strftime(
        datetime.datetime.utcfromtimestamp(t_start) + datetime.timedelta(
            (datetime.datetime.utcfromtimestamp(t_start).hour + n) / 24), "%Y-%m-%d") for n, f in
                   enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) % 24)]

    decimation = 3
    xticks = xticks[2::decimation]
    xticklabels = xticklabels[2::decimation]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)

    ax.set_xlim(t_start, t_stop)
    ax_db = ax.twinx()
    ax_db.set_ylabel("dB")
    ax_db.set_yticks(np.array(range(200)) - 100)
    ax.set_ylim(-10, 25)
    ax_db.set_ylim(-10, 25)
    ax_db.tick_params(axis='y', labelcolor='k')
    ax_db.spines["right"].set_position(("axes", 1))

    ax.set_title(opts.directory)
    if opts.weather:
        print "Loading Temperature data...",
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
        print "done! Found %d records" % len(temp_data)

        print "Loading Rain data...",
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
        print "done! Found %d records" % len(rain_data)

        print "Loading Wind data...",
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
        print "done! Found %d records" % len(wind_data)

        print "Loading Solar data...",
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
        print "done! Found %d records" % len(sun_data)

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
