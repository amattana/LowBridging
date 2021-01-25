import numpy as np
import os
import glob
import datetime
import calendar
from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def dt_to_timestamp(d):
    return calendar.timegm(d.timetuple())


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


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %sb-temp_converter [options]")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/data_logger/Raw/",
                      help="Directory where raw data logger files are located")

    (opts, args) = parser.parse_args(argv[1:])

    path = opts.directory
    if not path[-1] == "/":
        path += "/"
    lista = sorted(glob.glob(opts.directory + "*.txt"))
    temperature = []
    timestamps = []
    for t, l in enumerate(lista):
        print "Processing file: ", l
        with open(l) as f:
            data = f.readlines()
        dati = []
        tempi = []
        for d in data:
            try:
                test_num = int(d[0])
                tempi += [dt_to_timestamp(datetime.datetime.strptime(d.split(",")[1], "%Y-%m-%d %H:%M:%S"))]
                dati += [float(d.split(",")[2])]
            except:
                #print "Skipping record: ", d
                pass
        timestamps += tempi
        temperature += dati

    with open("/storage/monitoring/data_logger/AAVS2_Data_Logger.txt", "w") as f:
        for n, t in enumerate(timestamps):
            f.write("%d\t%s\t%f\n" % (t, datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(t) ,"%Y-%m-%d\t%H:%M:%S"), temperature[n]))

    print "\nOutput file: /storage/monitoring/data_logger/AAVS2_Data_Logger.txt"
    print "Written %d records\n" % len(temperature)

    t_start = timestamps[0]
    t_stop = timestamps[-1]
    delta_h = (t_stop - t_start) / 3600
    x = np.array(range(t_stop - t_start)) + t_start

    xticks = np.array(range(delta_h)) * 3600 + t_start
    xticklabels = [f if f != 0 else datetime.datetime.strftime(
        datetime.datetime.utcfromtimestamp(t_start) + datetime.timedelta(n / 24), "%Y-%m-%d") for n, f in
                   enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) % 24)]

    decimation = 24 * 15
    xticks = xticks[12::decimation]
    xticklabels = xticklabels[12::decimation]


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

    gs = GridSpec(1, 1, left=0.08, top=0.935, bottom=0.15, right=0.94)
    fig = plt.figure(figsize=(14, 9), facecolor='w')
    ax = fig.add_subplot(gs[0, 0])

    ax.plot(timestamps, temperature, color="purple", lw=0, marker=".", markersize=3)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=90)
    ax.set_yticks(range(100)[::2])
    ax.set_ylim(10, 70)
    ax.set_xlim(t_start, t_stop)
    ax.set_title("SmartBox Temperature vs External Temperature", fontsize=18)
    ax.set_ylabel("Celsius deg", fontsize=14)
    ax.set_xlabel("Time", fontsize=14)
    ax.grid()
    ax2 = ax.twinx()
    ax2.plot(w_time, w_temp, color="r", lw=0, marker=".", markersize=3)
    ax2.set_yticks(range(100)[::2])ph
    ax2.set_ylabel("Celsius deg", fontsize=14)
    ax2.set_ylim(10, 70)
    plt.show()
