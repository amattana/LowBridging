from matplotlib import pyplot as plt
import os
import numpy as np
from matplotlib.gridspec import GridSpec
import datetime
import glob
from aavs_utils import dt_to_timestamp, ts_to_datestring, mro_daily_weather, diclist_to_array

t_start = 0
t_stop = 0


def read_data(path, tile, channel, pol):
    global t_start, t_stop
    p = 0
    if pol.upper() == "Y":
        p = 1
    lista = sorted(glob.glob(path + ("*Tile-%02d.txt" % (tile))))
    dati = []
    x = []
    if len(lista):
        for n, l in enumerate(lista):
            if not n == len(lista) - 1:
                f_next = lista[n + 1].split("/")[-1][:17]
                # print "next", f_next, dt_to_timestamp(datetime.datetime.strptime(f_next, "%Y-%m-%d_%H%M%S"))
                if t_start >= dt_to_timestamp(datetime.datetime.strptime(f_next, "%Y-%m-%d_%H%M%S")):
                    pass
            f_date = l.split("/")[-1][:17]
            # print "current: ", f_date, dt_to_timestamp(datetime.datetime.strptime(f_date, "%Y-%m-%d_%H%M%S"))
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
                                    dati += [float(record[3 + ((channel - 1) * 2) + p])]
                                    x += [t_stamp]
                            except:
                                pass
    return x, dati


if __name__ == "__main__":
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
    parser.add_option("--input", action="store", dest="channel", type=int,
                      default=1, help="SmartBox Input (default: 1)")
    parser.add_option("--pol", action="store", dest="pol", type=str,
                      default="X", help="Polarization (default: X)")
    parser.add_option("--list", action="store", dest="lista", type=str,
                      default="", help="List of signals to plot, a string where tuple element are comma separated 'tile-input-pol,tile-input-pol'")
    parser.add_option("--date", action="store", dest="date",
                      default="all", help="Date in YYYY-MM-DD (required, default 'all')")
    parser.add_option("--weather", action="store_true", dest="weather",
                      default=False, help="Add weather info (if available)")
    (opts, args) = parser.parse_args(argv[1:])

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
            print "\nWeather data acquired, %d records"%len(w_temp)#, "  ", w_temp[0:8]
        else:
            print "\nNo weather data available\n"

    plt.ion()

    if os.path.exists(opts.directory):
        path = opts.directory
        if not path[-1] == "/":
            path = path + "/"
        path += opts.station.upper() + "/"

        plt.ion()
        gs = GridSpec(1, 1, left=0.1, bottom=0.075, top=0.95, right=0.98)
        fig = plt.figure(figsize=(12, 7), facecolor='w')
        ax = fig.add_subplot(gs[0, 0])

        if "all" in opts.date.lower():
            delta = (dt_to_timestamp(datetime.datetime.utcnow().date() + datetime.timedelta(1)) -
                     dt_to_timestamp(datetime.datetime(2020, 03, 01)))
            delta_h = delta / 3600
            x = np.array(range(delta)) + t_start
        else:
            delta_h = 24
            x = np.array(range(24 * 60 * 60)) + t_start
        xticks = np.array(range(delta_h)) * 3600 + t_start
        ax.plot(x, x, color='w')
        ax.set_xticks(xticks)
        ax.set_xticklabels(np.array(range(delta_h)) % 24)

        if not opts.lista:
            data_list = [(opts.tile, opts.channel, pol)]
        else:
            data_list = []
            for d in opts.lista.split(","):
                data_list += [(int(d.split("-")[0]), int(d.split("-")[1]), d.split("-")[2])]

        for d in data_list:
            x, dati = read_data(path, d[0], d[1], d[2])
            print "Found %d valid records for Tile-%02d Input #%02d Pol-%s\n" % (len(dati), d[0], d[1], d[2].upper())
            ax.plot(x, dati, linestyle='None', marker=".", markersize=2,
                    label="Tile-%02d Input %02d Pol %s" % (d[0], d[1], d[2].upper()))

        ax.set_xlim(x[0], x[-1])
        ax.set_ylim(0, 50)
        ax.set_ylabel("ADC RMS")
        ax.set_xlabel("UTC Time (hours)")
        ax.set_title("ADC RMS     Start Time: %s      End Time: %s" % (ts_to_datestring(x[0]), ts_to_datestring(x[-1])))
        ax.legend(markerscale=8)

        if len(w_data):
            ax_weather = ax.twinx()
            ax_weather.set_ylabel('Temperature (C)', color='r')
            #ax_weather.set_xlim(t_stamps[0], t_stamps[-1])
            ax_weather.set_ylim(50, 0)
            ax_weather.set_yticks(np.arange(15, 50, 5))
            ax_weather.set_yticklabels(np.arange(15, 50, 5), color='r')

            ax_wind = ax_power.twinx()
            ax_wind.plot(w_time, w_wind, color='orange', lw=1.5)
            ax_wind.set_ylim(0, 80)
            ax_wind.set_ylabel('Wind (Km/h)', color='orange')
            ax_wind.tick_params(axis='y', labelcolor='orange')
            ax_wind.spines["right"].set_position(("axes", 1.06))

            ax_rain = ax_power.twinx()
            ax_rain.plot(w_time, w_rain, color='cyan', lw=1.5)
            ax_rain.set_ylim(0, 100)
            ax_rain.set_ylabel('Rain (mm)', color='cyan')
            ax_rain.tick_params(axis='y', labelcolor='cyan')
            ax_rain.spines["right"].set_position(("axes", 1.12))
            ax_weather.plot(w_time, w_temp, color='r', lw=1.5)

            # Draw wind direction
            for a in range(len(w_wdir)):
                if not a % 4:
                    m = MarkerStyle(">")
                    m._transform.rotate_deg(w_wdir[a])
                    # print a, xticks[a], w_wind[a], len(xticks), len(w_wind)
                    ax_wind.scatter(w_time[a], w_wind[a], marker=m, s=100, color='orchid')
                    m = MarkerStyle("_")
                    m._transform.rotate_deg(w_wdir[a])
                    ax_wind.scatter(w_time[a], w_wind[a], marker=m, s=500, color='orchid')
            fig.subplots_adjust(right=0.86)


        plt.show()

    else:
        print "\nThe given path does not exists! (%s)\n" % opts.directory

