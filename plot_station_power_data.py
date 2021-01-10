import matplotlib.pyplot as plt
import numpy as np
import calendar
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.markers import MarkerStyle
import datetime, time
import glob
import os
import sys
#from aavs_utils import dt_to_timestamp, ts_to_datestring, closest, diclist_to_array, mro_daily_weather
import warnings
warnings.filterwarnings("ignore")
ERASE_LINE = '\x1b[2K'


def dt_to_timestamp(d):
    return calendar.timegm(d.timetuple())


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


def mro_daily_weather(fname="/storage/monitoring/weather/MRO_WEATHER.csv", date="", start="", stop=""):
    records = []
    units = {}

    try:
        if date:
            t_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            t_start = int(time.mktime(t_date.timetuple()))# + (60 * 60 * 8) # Fix Weather data written in WA Local Time
            t_stop = int(time.mktime(t_date.timetuple()) + (60 * 60 * 24))# + (60 * 60 * 8) # Fix Weather data written in WA Local Time

        elif start and stop:
            #t_start = int(time.mktime(datetime.datetime.strptime(start, "%Y-%m-%d_%H:%M:%S").timetuple()))# + (60 * 60 * 8)  # Fix Weather data written in WA Local Time
            #t_start = int(time.mktime(datetime.datetime.strptime(start, "%Y-%m-%d_%H:%M:%S").timetuple())) + (60 * 60)  # Fix Weather data written in Local Time
            t_start = dt_to_timestamp(datetime.datetime.strptime(start, "%Y-%m-%d_%H:%M:%S"))
            #print "Weather Start Time: ", t_start
            #t_stop = int(time.mktime(datetime.datetime.strptime(stop, "%Y-%m-%d_%H:%M:%S").timetuple())) + (60 * 60)  # Fix Weather data written in Local Time
            t_stop = dt_to_timestamp(datetime.datetime.strptime(stop, "%Y-%m-%d_%H:%M:%S"))
        else:
            print "Missing time argument (date | start,stop)"
            return units, records

    except ValueError:
        print "Wrong date format, expected %Y-%m-%d"
        return units, records

    #print "Looking for data between", t_start, "and", t_stop
    if os.path.exists(fname):
        with open(fname) as f:
            data = f.readlines()
        if len(data) > 4:
            units['time'] = "sec"
            units['temp'] = data[3].split(",")[1][1:].split(" ")[-1][1:-1]
            units['wind'] = data[3].split(",")[3][1:].split(" ")[-1][1:-1]
            units['wdir'] = "deg"
            units['rain'] = data[3].split(",")[6][1:].split(" ")[-1][1:-1]
            for d in data[4:]:
                #t_stamp = int(time.mktime(datetime.datetime.strptime(d.split(",")[0], "%Y-%m-%d %H:%M:%S").timetuple())) - (60 * 60 * 6)
                t_stamp = dt_to_timestamp(datetime.datetime.strptime(d.split(",")[0], "%Y-%m-%d %H:%M:%S")) - (60 * 60 * 8) # Time is in Local WA, GMT+8
                if t_start <= t_stamp <= t_stop:
                    try:
                        dati = {}
                        dati['time'] = t_stamp
                        dati['temp'] = float(d.split(",")[1])
                        dati['wind'] = float(d.split(",")[3])
                        dati['wdir'] = int(d.split(",")[5])
                        dati['rain'] = float(d.split(",")[6])
                        records += [dati]
                    except:
                        pass
    return units, records


def diclist_to_array(dic, key):
    lista = []
    for d in dic:
        lista += [d[key]]
    return lista


def get_sbtemp(start=0, stop=2585699200):
    #print "\nStart Time: ", start, "\tStop Time: ", stop
    tempi = []
    dati = []
    if os.path.exists("/storage/monitoring/data_logger/AAVS2_Data_Logger.txt"):
        with open("/storage/monitoring/data_logger/AAVS2_Data_Logger.txt") as f:
            data = f.readlines()
        for d in data:
            if start <= int(d.split()[0]) <= stop:
                tempi += [int(d.split()[0])]
                dati += [float(d.split()[3])]
    else:
        print "Unable to find the Data Logger file (/storage/monitoring/data_logger/AAVS2_Data_Logger.txt)"
    return tempi, dati


def plot_weather():
    if len(w_data):
        if opts.weather:
            ax_weather = ax.twinx()
            ax_weather.set_ylabel('Temperature (C) red: External Temp, purple: Internal SmartBox', color='r')
            ax_weather.set_ylim(range_temp_min, range_temp_max)
            ax_weather.set_yticks(np.arange(range_temp_min, range_temp_max, 5))
            ax_weather.set_yticklabels(np.arange(range_temp_min, range_temp_max, 5), color='r')
            ax_weather.plot(w_time, w_temp, color='r', lw=1.5, label='External Temp')
            ax_weather.tick_params(axis='y', labelcolor='r')
            ax_weather.spines["right"].set_position(("axes", 1.07))

            if opts.sbtemp:
                sb_tempi, sb_dati = get_sbtemp(t_start, t_stop)
                if sb_dati:
                    # ax_weather.plot(sb_tempi, sb_dati, color='purple', linestyle='None', marker=".", markersize=2, label='SmartBox Internal Temp')
                    ax_weather.plot(sb_tempi, sb_dati, color='purple', label='SmartBox Internal Temp',
                                    linestyle='None', marker=".", markersize=2)
                # else:
                #     print "\nNo SmartBox Temperature available!"
            # ax_weather.legend(fancybox=True, framealpha=1, shadow=True, borderpad=1, ncol=8,#bbox_to_anchor=(1-0.2, 1-0.2)
            #                  loc="lower right", fontsize='small')

        if opts.wind:
            ax_wind = ax.twinx()
            ax_wind.plot(w_time, w_wind, color='orange', lw=2.5, linestyle='None', marker=".", markersize=3)
            ax_wind.set_ylim(0, 100)
            ax_wind.set_ylabel('Wind (Km/h)', color='orange')
            ax_wind.tick_params(axis='y', labelcolor='orange')
            ax_wind.spines["right"].set_position(("axes", 1.16))
            # Draw wind direction
            for a in range(len(w_wdir)):
                if not a % (len(w_wdir) / 24):
                    m = MarkerStyle(">")
                    m._transform.rotate_deg(w_wdir[a])
                    # print a, xticks[a], w_wind[a], len(xticks), len(w_wind)
                    ax_wind.scatter(w_time[a], w_wind[a], marker=m, s=20, color='black')
                    m = MarkerStyle("_")
                    m._transform.rotate_deg(w_wdir[a])
                    ax_wind.scatter(w_time[a], w_wind[a], marker=m, s=100, color='black')

        if opts.rain:
            ax_rain = ax.twinx()
            ax_rain.plot(w_time, w_rain, color='cyan', lw=3)
            ax_rain.set_ylim(0, 100)
            ax_rain.set_ylabel('Rain (mm)', color='cyan')
            ax_rain.tick_params(axis='y', labelcolor='cyan')
            ax_rain.spines["right"].set_position(("axes", 1.24))

        if opts.sun:
            if len(sun_data):
                ax_sun = ax.twinx()
                ax_sun.plot(sun_time, sun_data, color='k', lw=1.5)
                ax_sun.set_ylim(0, 4000)
                ax_sun.set_ylabel('Solar Radiation (W/m^2)', color='k')
                ax_sun.tick_params(axis='y', labelcolor='k')
                ax_sun.spines["right"].set_position(("axes", 1.32))


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
    parser.add_option("--pol", action="store", dest="pol",
                      default="", help="Polarization to plot, 'both' means both in the same axes")
    parser.add_option("--groupname", action="store", dest="groupname",
                      default="", help="Antenna group name to be added to title")
    parser.add_option("--mixed", action="store_true", dest="mixed",
                      default=False, help="Plot Specific set of Antenna (antenna option required)")
    parser.add_option("--chart", action="store_true", dest="chart",
                      default=False, help="Plot lots of picture as chart useful for movies")
    parser.add_option("--rate", action="store", dest="rate",
                      default="10", help="Chart update rate in minutes (Default: 10 minutes)")
    parser.add_option("--antenna", action="store", dest="antenna",
                      default=60, help="Antenna number for chart")
    parser.add_option("--weather", action="store_true", dest="weather",
                      default=False, help="Plot all the weather info if available (Temp, Wind, Rain)")
    parser.add_option("--sbtemp", action="store_true", dest="sbtemp",
                      default=False, help="Plot the SmartBox Temperature if available")
    parser.add_option("--temp", action="store_true", dest="temp",
                      default=False, help="Plot the Temperature if available")
    parser.add_option("--wind", action="store_true", dest="wind",
                      default=False, help="Plot the Wind data if available")
    parser.add_option("--rain", action="store_true", dest="rain",
                      default=False, help="Plot the Rain data if available")
    parser.add_option("--sun", action="store_true", dest="sun",
                      default=False, help="Plot the Solar Irradiation data if available")
    parser.add_option("--rangetemp", action="store", dest="rangetemp",
                      default="20,160", help="min,max temperature range")

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

    w_data = []
    if opts.weather:
        w_units, w_data = mro_daily_weather(start=ts_to_datestring(t_start, formato="%Y-%m-%d_%H:%M:%S"),
                                             stop=ts_to_datestring(t_stop, formato="%Y-%m-%d_%H:%M:%S"))
        if len(w_data):
            w_time = diclist_to_array(w_data, 'time')
            w_temp = diclist_to_array(w_data, 'temp')
            w_wind = diclist_to_array(w_data, 'wind')
            w_wdir = diclist_to_array(w_data, 'wdir')
            w_rain = diclist_to_array(w_data, 'rain')
            print "\nWeather data acquired, %d records" % len(w_temp)#, "  ", w_temp[0:8]
        else:
            print "\nNo weather data available\n"

    if opts.sun:
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
        print "Solar Irraditation records: ", len(sun_data)

    plt.ion()
    if opts.freq == "ecg":
        if opts.weather:
            gs = GridSpec(1, 1, left=0.06, top=0.935, bottom=0.15, right=0.8)
        else:
            gs = GridSpec(1, 1, left=0.06, top=0.935, bottom=0.15, right=0.92)
    elif opts.chart:
        gs = GridSpec(1, 1, left=0.06, top=0.935, bottom=0.15, right=0.8)
    else:
        gs = GridSpec(1, 1, left=0.06, top=0.935, bottom=0.15, right=0.72)

    if opts.chart:
        t_start = t_start - (60 * 60 * 24 * 3) # Chart plot x axes starts 3 days before
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
        datetime.datetime.utcfromtimestamp(t_start) + datetime.timedelta(n / 24), "%Y-%m-%d") for n, f in
                   enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) % 24)]

    div = np.array([1, 2, 3, 4, 6, 8, 12, 24])
    decimation = div[closest(div, len(xticks) / 24)]
    # print decimation, len(xticks)
    # print xticks
    # print xticklabels
    if opts.chart:
        decimation = 3
    xticks = xticks[::decimation]
    xticklabels = xticklabels[::decimation]

    ax.plot(x, x, color='w')
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)
    if len(w_data):
        ax_weather = ax.twinx()
        range_temp_min = int(opts.rangetemp.split(",")[0])
        range_temp_max = int(opts.rangetemp.split(",")[1])

    if opts.mixed:
        if opts.antenna == "":
            print "\nAntenna Argument required!\n"
            exit()
        else:
            if opts.antenna == "ribbon":
                ant_group = []
            else:
                antenne = opts.antenna.split(",")
                ant_group = [antenne]

        if freq.lower() == "all":
            dirlist = sorted(glob.glob(data_dir + start_date + "/" + opts.station + "_*MHz"))
        else:
            dirlist = [data_dir + start_date + "/" + opts.station + "_" + str(freq) + "MHz"]

        print
        for dlcnt, dl in enumerate(dirlist):
            plt.show()
            sys.stdout.write(ERASE_LINE + "\r[%d/%d] Processing directory: %s" % (dlcnt + 1, len(dirlist), dl))
            sys.stdout.flush()
            freq = dl[-6:-3]
            if not opts.pol == "both":
                for pol in ["X", "Y"]:
                    for ng, gr in enumerate(ant_group):
                        sys.stdout.write(ERASE_LINE + "\r[%d/%d] Plotting Pol-%s of Group %d/%d" %
                                         (dlcnt + 1, len(dirlist), pol, ng + 1, len(ant_group)))
                        sys.stdout.flush()
                        plt.clf()
                        ax = fig.add_subplot(gs[0, 0])
                        ax.cla()
                        #if len(w_data):
                        #    ax_weather = ax.twinx()
                        ax.set_xticks(xticks)
                        ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)
                        yticks = []
                        yticklabels = []
                        for n, g in enumerate(gr):
                            flist = sorted(glob.glob(dl + "/power_data/" + opts.station + "_POWER_" + start_date +
                                                     "*_ANT-%03d_POL-%s_*.txt" % (int(g), pol)))
                            for f in flist:
                                with open(f) as fi:
                                    data = fi.readlines()
                                asse_x = []
                                dati = []
                                for d in data[1:]:
                                    if not float(d.split()[3]) == 0:
                                        asse_x += [int(d.split()[0])]
                                        dati += [float(d.split()[3])]
                                if len(dati):
                                    #dati = np.array(dati) - dati[0] - ((16/len(gr)) * n)
                                    dati = np.array(dati) - dati[0] - (2 * n)
                                    ax.plot(asse_x, dati, linestyle='None', marker=".", markersize=1)
                                    #yticks += [-((16/len(gr)) * n)]
                                    yticks += [-(2 * n)]
                                    yticklabels += [f[f.rfind("ANT"):f.rfind("ANT") + 7]]
                        if opts.station == "AAVS2":
                            ax.set_ylim(-20, 3)
                        else:
                            ax.set_ylim(-20, 3)
                        ax.set_xlim(xticks[0], xticks[-1])
                        ax.set_xlabel("UTC Time")

                        ax.set_yticks(yticks)
                        ax.set_yticklabels(yticklabels)
                        group_name = opts.groupname
                        tempo = "From " + opts.start.replace("_", " ") + " to " + opts.stop.replace("_", " ") + " UTC  " \
                                + group_name
                        ax.set_title("%s  Pol-%s   Frequency %sMHz  %s" % (opts.station, pol, freq, tempo))
                        #ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0., fontsize=14, markerscale=8)
                        #ax.grid()
                        ax_db = ax.twinx()
                        ax_db.set_yticks((np.arange(50)-24).tolist())
                        ax_db.set_ylim(-15, 3)
                        ax_db.set_ylabel('dB', color='k')
                        ax_db.tick_params(axis='y', labelcolor='k')
                        ax_db.spines["right"].set_position(("axes", 1))
                        ax_db.grid()
                        plot_weather()
                        gruppo = opts.antenna.replace(",", "-")
                        opath = dl + "/group_pics/"
                        if not os.path.isdir(opath):
                            os.mkdir(opath)
                        if not os.path.isdir(opath + "Pol-" + pol):
                            os.mkdir(opath + "Pol-" + pol)
                        fig.savefig(opath + "Pol-" + pol + "/" + start_date + "_" + opts.station + "_GROUP-%s_" % gruppo +
                                    freq + "MHz_Pol-" + pol + ".png")
            else:
                # single antenna
                group_reshaped = np.array(ant_group).reshape(len(ant_group) * (len(ant_group[0]))).tolist()
                for nant, ant in enumerate(group_reshaped):
                    sys.stdout.write(ERASE_LINE + "\r[%d/%d] Frequency: %s MHz --> [%d/%d] Plotting Antenna %d" %
                                     (dlcnt + 1, len(dirlist), freq,nant + 1, len(group_reshaped), int(ant)))
                    sys.stdout.flush()
                    plt.clf()
                    ax = fig.add_subplot(gs[0, 0])
                    ax.cla()
                    #if len(w_data):
                    #    ax_weather = ax.twinx()
                    ax.set_xticks(xticks)
                    ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)
                    f = sorted(glob.glob(dl + "/power_data/" + opts.station + "_POWER_" + start_date +
                                             "*_ANT-%03d_POL-X_*.txt" % (int(ant))))[0]
                    with open(f) as fi:
                        data = fi.readlines()
                    asse_x = []
                    dati = []
                    for d in data[1:]:
                        asse_x += [int(d.split()[0])]
                        dati += [float(d.split()[3])]
                    if len(dati):
                        dati = np.array(dati) - dati[0]
                        ax.plot(asse_x, dati, color='b', linestyle='None', marker=".", markersize=1)
                    f = sorted(glob.glob(dl + "/power_data/" + opts.station + "_POWER_" + start_date +
                                             "*_ANT-%03d_POL-Y_*.txt" % (int(ant))))[0]
                    with open(f) as fi:
                        data = fi.readlines()
                    asse_x = []
                    dati = []
                    for d in data[1:]:
                        asse_x += [int(d.split()[0])]
                        dati += [float(d.split()[3])]
                    if len(dati):
                        dati = np.array(dati) - dati[0]
                        ax.plot(asse_x, dati, color='g', linestyle='None', marker=".", markersize=1)

                    if opts.station == "AAVS2":
                        ax.set_ylim(-12, 6)
                    else:
                        ax.set_ylim(-12, 6)
                    ax.set_xlim(xticks[0], xticks[-1])
                    ax.set_xlabel("UTC Time")
                    tempo = "From " + opts.start.replace("_", " ") + " to " + opts.stop.replace("_", " ") + " UTC"
                    ax.set_title("%s  Antenna %d  Frequency %sMHz  %s" % (opts.station, int(ant), freq, tempo))
                    #ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0., fontsize=14, markerscale=8)
                    ax.grid()
                    plot_weather()
                    opath = dl + "/ant_pics/"
                    if not os.path.isdir(opath):
                        os.mkdir(opath)
                    fig.savefig(opath + start_date + "_" + opts.station + "_FREQ-%sMHz_ANT-%03d.png" % (freq, int(ant)))

        print

    elif not opts.chart:

        if freq.lower() == "ecg":
            # all frequencies per antenna
            dirlist = sorted(glob.glob(data_dir + start_date + "/" + opts.station + "_*MHz"))
            for ant in range(256):
                for pol in ["X", "Y"]:
                    yticks = []
                    yticklabels = []
                    sys.stdout.write(ERASE_LINE + "\r[%d/256] Processing Antenna: %d Pol-%s" % (ant + 1, ant + 1, pol))
                    sys.stdout.flush()
                    plt.clf()
                    ax = fig.add_subplot(gs[0, 0])
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
                                if len(dati):
                                    dati = np.array(dati) - dati[0] - (1 * dn)
                                    ax.plot(asse_x, dati, linestyle='None', marker=".", markersize=1)
                                    yticks += [-dn]
                                    yticklabels += [dl[-6:-3]]
                    ax.set_xlabel("UTC time")
                    ax.set_ylabel("MHz")
                    ax.set_xlim(xticks[0], xticks[-1])
                    ax.set_ylim(-(len(dirlist)) - 8, 2)
                    ax.set_yticks(yticks)
                    ax.set_yticklabels(yticklabels)
                    ax.set_title("%s Antenna %03d Pol %s   from %s to %s" % (opts.station, ant + 1, pol,
                                                                             opts.start.replace("_", " "),
                                                                             opts.stop.replace("_", " ")))
                    ax.grid()
                    plot_weather()

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
            # all tile per frequency
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
                        plt.clf()
                        ax = fig.add_subplot(gs[0, 0])
                        ax.cla()
                        if len(w_data):
                            ax_weather = ax.twinx()
                        ax.set_xticks(xticks)
                        ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)
                        flist = sorted(glob.glob(dl + "/power_data/" + opts.station + "_POWER_" + start_date +
                                                 "_TILE-%02d_ANT*_POL-%s_*.txt" % (t, pol)))
                        y0 = 0
                        yticks = []
                        yticklabels = []
                        for n, f in enumerate(flist):
                            with open(f) as g:
                                data = g.readlines()
                            asse_x = []
                            dati = []
                            for d in data[1:]:
                                asse_x += [int(d.split()[0])]
                                dati += [float(d.split()[3])]
                            if len(dati):
                                dati = np.array(dati) - dati[0] - (1 * n)
                                ax.plot(asse_x, dati, linestyle='None', marker=".", markersize=1)
                                yticks += [-n]
                                yticklabels += [f[f.rfind("ANT"):f.rfind("ANT") + 7]]
                        if opts.station == "AAVS2":
                            ax.set_ylim(-30, y0+3)
                        else:
                            ax.set_ylim(-30, y0+3)
                        ax.set_xlim(xticks[0], xticks[-1])
                        ax.set_xlabel("UTC Time")
                        ax.set_yticks(yticks)
                        ax.set_yticklabels(yticklabels)
                        tempo = "From " + opts.start.replace("_", " ") + " to " + opts.stop.replace("_", " ") + " UTC"
                        ax.set_title("%s Tile-%02d   Pol-%s   Frequency %sMHz  %s" % (opts.station, t, pol, freq, tempo))
                        #ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0., fontsize=14, markerscale=8)

                        ax.grid()
                        plot_weather()

                        opath = dl + "/tile_pics/"
                        if not os.path.isdir(opath):
                            os.mkdir(opath)
                        if not os.path.isdir(opath + "Pol-" + pol):
                            os.mkdir(opath + "Pol-" + pol)
                        fig.savefig(opath + "Pol-" + pol + "/" + start_date + "_" + opts.station + "_Tile-%02d_"  % t + freq +
                                    "MHz_Pol-" + pol + ".png")
                sys.stdout.write(ERASE_LINE + "\r[%d/%d] Processed directory: %s\n" % (dlcnt + 1, len(dirlist), dl))
                sys.stdout.flush()
    else:
        ant = int(opts.antenna)
        dl = data_dir + start_date + "/" + opts.station + "_" + str(freq) + "MHz"
        for pol in ["X", "Y"]:
            flist = sorted(glob.glob(dl + "/power_data/" + opts.station + "_POWER_" + start_date +
                                     "_TILE-*_ANT-%03d_POL-%s_*.txt" % (ant, pol)))
            for f in flist:
                print "Reading file: ", f
                with open(f) as g:
                    data = g.readlines()
                asse_x = []
                dati = []
                for d in data[1:]:
                    asse_x += [int(d.split()[0])]
                    dati += [float(d.split()[3])]
                dati = np.array(dati) - dati[0]
            if pol == "X":
                colore = "b"
            else:
                colore = "g"
            ax.plot(asse_x, dati, color=colore, linestyle='None', marker=".", markersize=2)
        ax.set_xlabel("UTC Time", fontsize=12)
        ax.set_ylabel("dB", fontsize=12)
        ax.set_yticks(np.array(range(0, 50, 2))-36)
        ax.set_ylim(-20, 4)
        ax.set_title("Antenna #%03d Chart - Frequency %d MHz" % (ant, int(freq)))
        ax.grid()
        plot_weather()

        tempo = t_start
        while tempo < t_stop - (60 * 60 * 24 * 3):
            ax.set_xlim(tempo, tempo + (60 * 60 * 24 * 3))  # 3 days window
            opath = dl + "/chart_pics"
            if not os.path.isdir(opath):
                os.mkdir(opath)
            fig.savefig(opath + "/Chart_Ant-%03d_Freq-%03d_Start_" % (ant, int(freq)) + start_date +
                        "_TStamp-%d.png" % tempo)
            tempo = tempo + (60 * int(opts.rate))
            sys.stdout.write(ERASE_LINE + "\rAntenna #%03d Chart - Processing Time: %s" %
                             (ant, datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(
                                 tempo + (60 * 60 * 24 * 3)), "%Y-%m-%d %H:%M:%S")))
            sys.stdout.flush()
        print
