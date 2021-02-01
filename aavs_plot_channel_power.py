from optparse import OptionParser
import sys
import os
import glob
import numpy as np
from matplotlib import pyplot as plt
import datetime
import calendar
import warnings
warnings.filterwarnings("ignore")
from matplotlib.gridspec import GridSpec

data_path = "/storage/monitoring/power/"
COLORE=["b", "orange", "r", "g"]
ERASE_LINE = '\x1b[2K'


def dt_to_timestamp(d):
    return calendar.timegm(d.timetuple())


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


def get_ant_map():
    adu_remap = [0, 1, 2, 3, 8, 9, 10, 11, 15, 14, 13, 12, 7, 6, 5, 4]
    with open("aavs_map.txt") as fmap:
        records = fmap.readlines()
    ant_map = []
    for r in records:
        if len(r.split()) > 2:
            ant_map += [[int(r.split()[0]), adu_remap[int(r.split()[1])-1], int(r.split()[2])]]
    return ant_map


if __name__ == "__main__":
    # Command line options
    p = OptionParser()
    p.set_usage('aavs_plot_channel_power.py [options]')
    p.set_description(__doc__)
    p.add_option("--date", action="store", dest="date", default="", help="Month to be processed (YYYY-mm)")
    #p.add_option("--pol", action="store", dest="pol", default="", help="Polarization (default: both)")
    p.add_option("--freq", action="store", dest="freq", default=159, help="Frequency (default: 159)")
    p.add_option("--station", action="store", dest="station", default="AAVS2", help="Station Name (default: AAVS2)")
    p.add_option("--window", action="store", dest="window", default=3, help="Plot time window (default: 3 days)")
    opts, args = p.parse_args(sys.argv[1:])

    if not opts.date == "":
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m")
            t_start = dt_to_timestamp(t_date)
            if not t_date.month == 12:
                t_stop = dt_to_timestamp(datetime.datetime(t_date.year, t_date.month + 1, 1))
            else:
                t_stop = dt_to_timestamp(datetime.datetime(t_date.year + 1, 1, 1))
            print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
            print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
        except:
            print "Bad date format detected (must be YYYY-MM)"
            exit()
    else:
        print "Missing Argument 'date'\n"
        exit()

    t_day = t_start
    h24 = 60 * 60 * 24
    time_window = (h24 * opts.window)
    range_db_min = -25
    range_db_max = 5

    gs = GridSpec(1, 1, left=0.07, top=0.935, bottom=0.12, right=0.73)
    fig = plt.figure(figsize=(14, 9), facecolor='w')
    ax = fig.add_subplot(gs[0, 0])

    ant_map = get_ant_map()
    ant_data = {}
    if not os.path.isdir(data_path + opts.station + "/" + opts.date + "/FREQ-%03dMHz" % int(opts.freq)):
        print "\nERROR: Cannot find path: ", data_path + opts.station + "/" + opts.date + "/FREQ-%03dMHz" % \
                                             int(opts.freq)
        exit()
    files = sorted(glob.glob(data_path + opts.station + "/" + opts.date + "/FREQ-%03dMHz" % int(opts.freq) + "/" +
                             opts.station + "_POWER*txt"))
    out_path = data_path + opts.station + "/" + opts.date + "/FREQ-%03dMHz/pictures" % int(opts.freq)
    if not os.path.exists(out_path):
        os.mkdir(out_path)
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
    with open("/storage/monitoring/weather/MRO_WINDSPEED.csv") as s:
        data = s.readlines()
    wind_time = []
    wind_data = []
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

    POLS = ['X', 'Y']
    for tile in range(16):
        # Loading tile data
        for a in range(16):
            sys.stdout.write(ERASE_LINE + "\r[%03d/%03d] Loading Antenna %03d data..." %
                             (a, 16, int(ant_map[(tile * 16) + a][2])))
            sys.stdout.flush()
            ant_data["%03d_tstamp" % int(ant_map[(tile * 16) + a][2])] = []
            ant_data["%03d_Xdata" % int(ant_map[(tile * 16) + a][2])] = []
            ant_data["%03d_Ydata" % int(ant_map[(tile * 16) + a][2])] = []
            with open(files[(tile * 16) + a]) as f:
                dati = f.readlines()
            x_norm_factor = 0
            y_norm_factor = 0
            for d in dati:
                try:
                    t = int(d.split()[0])
                    x = float(d.split()[3])
                    y = float(d.split()[4])
                    ant_data["%03d_tstamp" % int(ant_map[(tile * 16) + a][2])] += [t]
                    ant_data["%03d_Xdata" % int(ant_map[(tile * 16) + a][2])] += [x - x_norm_factor]
                    ant_data["%03d_Ydata" % int(ant_map[(tile * 16) + a][2])] += [y - y_norm_factor]
                    if len(ant_data["%03d_tstamp" % int(ant_map[(tile * 16) + a][2])]) == 1:
                        x_norm_factor = x
                        y_norm_factor = y
                except:
                    pass
        sys.stdout.write(ERASE_LINE + "\rAntenna data loaded!\n")
        sys.stdout.flush()

        t_day = t_start
        yticks = []
        yticklabels = []
        for ant in range(16):
            yticks += [-ant]
            yticklabels += ["ANT-%03d" % (int(ant_map[(tile * 16) + ant][2]))]
        while t_day < t_stop:
            t_end = t_day + time_window
            print "Processing Tile-%02d, date from %s to %s" % (tile + 1, ts_to_datestring(t_day), ts_to_datestring(t_end))
            for pol in POLS:
                fig.clf()
                ax = fig.add_subplot(gs[0, 0])
                ax.cla()
                for ant in range(16):
                    ax.plot(ant_data["%03d_tstamp" % (int(ant_map[(tile * 16) + ant][2]))],
                            np.array(ant_data["%03d_%sdata" % (int(ant_map[(tile * 16) + ant][2]), pol)]) - ant,
                            lw=0, marker=".", markersize=1)
                ax.set_yticks(yticks)
                ax.set_yticklabels(yticklabels, fontsize=10)
                ax.grid()

                ax.set_xlim(t_day, t_end)
                ax.set_ylim(range_db_min, range_db_max)
                ax.set_xlabel("UTC Time")
                #ax.set_ylabel("dB")

                delta_h = (t_end - t_day) / 3600
                x = np.array(range(t_end - t_day)) + t_day

                xticks = np.array(range(delta_h)) * 3600 + t_day
                xticklabels = [f if f != 0 else datetime.datetime.strftime(
                    datetime.datetime.utcfromtimestamp(t_day) + datetime.timedelta(
                        (datetime.datetime.utcfromtimestamp(t_day).hour + n) / 24), "%Y-%m-%d") for n, f in
                               enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_day).hour) % 24)]

                decimation = 3
                xticks = xticks[::decimation]
                xticklabels = xticklabels[::decimation]
                ax.set_xticks(xticks)
                ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)
                ax.set_title("Station %s   Tile-%02d   Pol-%s   from %s  to  %s" %
                             (opts.station, tile + 1, pol, ts_to_datestring(t_day, formato="%Y-%m-%d"),
                              ts_to_datestring(t_end, formato="%Y-%m-%d")))
                fname = opts.station + "_TILE-%02d_%s" % (tile + 1 ,ts_to_datestring(t_day, formato="%Y-%m-%d_Pol-") +
                                                          pol + ".png")

                ax_db = ax.twinx()
                ax_db.set_ylabel("dB")
                ax_db.set_yticks(np.array(range(200))-100)
                ax_db.set_ylim(range_db_min, range_db_max)
                ax_db.tick_params(axis='y', labelcolor='k')
                ax_db.spines["right"].set_position(("axes", 1))

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
                    ax_rain.plot(rain_time, rain_data, color='steelblue', lw=1.5)
                    ax_rain.set_ylim(0, 40)
                    ax_rain.set_ylabel('Rain (mm)', color='steelblue')
                    ax_rain.tick_params(axis='y', labelcolor='steelblue')
                    ax_rain.spines["right"].set_position(("axes", 1.24))

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

                if not os.path.exists(out_path + ts_to_datestring(t_day, formato="/%Y-%m-%d")):
                    os.mkdir(out_path + ts_to_datestring(t_day, formato="/%Y-%m-%d"))

                plt.savefig(out_path + ts_to_datestring(t_day, formato="/%Y-%m-%d/") + fname)
            t_day = t_day + time_window

