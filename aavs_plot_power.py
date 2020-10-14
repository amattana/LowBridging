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
    parser.add_option("--tile", action="store", dest="tile", type=str,
                      default="1", help="Tile Number")
    parser.add_option("--antenna", action="store", dest="antenna", type=int,
                      default=0, help="Antenna Name")
    parser.add_option("--equalize", action="store_true", dest="eq",
                      default=False, help="Equalize antennas power")
    parser.add_option("--weather", action="store_true", dest="weather",
                      default=False, help="Add weather info (if available)")
    parser.add_option("--sbtemp", action="store_true", dest="sbtemp",
                      default=False, help="Plot the SmartBox Temperature if available")
    parser.add_option("--temp", action="store_true", dest="temp",
                      default=False, help="Plot the Temperature if available")
    parser.add_option("--wind", action="store_true", dest="wind",
                      default=False, help="Plot the Wind data if available")
    parser.add_option("--rain", action="store_true", dest="rain",
                      default=False, help="Plot the Rain data if available")
    parser.add_option("--startfreq", action="store", dest="startfreq", type="int",
                      default=0, help="Start Frequency")
    parser.add_option("--stopfreq", action="store", dest="stopfreq", type="int",
                      default=400, help="Stop Frequency")
    (opts, args) = parser.parse_args(argv[1:])

    path = opts.directory
    if not path[-1] == "/":
        path += "/"
    station = opts.station.upper()
    path += station + "/"
    if "all" in opts.tile.lower():
        tiles = ["TILE-%02d"%(int(k)+1) for k in range(16)]
    else:
        tiles = ["TILE-%02d"%(int(k)) for k in opts.tile.split(",")]

    if opts.date:
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
            t_start = dt_to_timestamp(t_date)
            t_stop = dt_to_timestamp(t_date) + (60 * 60 * 24)
            print "Start Time:  " + ts_to_datestring(t_start) + "    Timestamp: " + str(t_start)
            print "Stop  Time:  " + ts_to_datestring(t_stop) + "    Timestamp: " + str(t_stop)
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

    if opts.eq:
        print "Equalization activated!"

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

    if "all" in opts.date.lower():
        delta = (dt_to_timestamp(datetime.datetime.utcnow().date() + datetime.timedelta(1)) -
                 dt_to_timestamp(datetime.datetime(2020, 03, 01)))
        delta_h = delta / 3600
        x = np.array(range(delta)) + t_start
    else:
        delta_h = (t_stop - t_start) / 3600
        x = np.array(range(t_stop - t_start)) + t_start

    xticks = np.array(range(delta_h)) * 3600 + t_start
    asse_x = np.linspace(0, 400, 512)
    fmin = closest(asse_x, float(opts.startfreq))
    fmax = closest(asse_x, float(opts.stopfreq))

    plt.ioff()
    gs = GridSpec(1, 1, left=0.04, right=0.86, bottom=0.2, top=0.96)
    fig = plt.figure(figsize=(14, 9), facecolor='w')
    for t in tiles:
        lista = sorted(glob.glob(path + t + "_*"))
        print "Found", len(lista), "Antenna Directories"
        for pol in ["X", "Y"]:
            # try:
                fig.clf()
                ax = fig.add_subplot(gs[0])
                ax.set_xticks(xticks)
                ax.set_xticklabels((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) % 24,
                                         rotation=90, fontsize=8)
                full_data = []
                full_time = []
                orari = []
                for k, l in enumerate(lista):
                    fname = l + "/data/POWER_" + ts_to_datestring(t_start, formato="%Y-%m-%d") + "_" + l.split("/")[-1] + "_POL-" + pol + "_BAND-" + \
                            str(opts.startfreq) + "-" + str(opts.stopfreq) + "MHz.txt"
                    if os.path.exists(fname):
                        with open(fname) as f:
                            data = f.readlines()
                        dati = []
                        tempi = []
                        for d in data:
                            dati += [float(d.split()[1])]
                            tempi += [int(d.split()[0])]
                            if not k:
                                orari += [datetime.datetime.utcfromtimestamp(int(d.split()[0]))]
                        if opts.eq:
                            if not k:
                                eq_value = dati[0]
                            dati = (np.array(dati) - dati[0]).tolist()
                        full_data += [dati]
                        full_time += [tempi]
                    else:
                        print "Missing file: ", fname
                        break
                #ax.cla()
                xmin = full_time[0][0]
                xmax = full_time[-1][-1]
                ymin = np.ceil(np.mean(full_data[0]) - 5)
                ymax = np.ceil(np.mean(full_data[0]) + 5)
                for n, l in enumerate(lista):
                    ax.plot(full_time[n], full_data[n], label=l.split("/")[-1])
                    xmin = min(full_time[n][0], xmin)
                    xmax = max(full_time[n][-1], xmax)
                    ymin = min(np.ceil(np.mean(full_data[n])) - 8, ymin)
                    ymax = max(np.ceil(np.mean(full_data[n])) + 4, ymax)
                #print xmin, xmax, ymin, ymax
                ax.set_xlim(xmin, xmax)
                if opts.eq:
                    ax.set_ylim(-8, 4)
                else:
                    ax.set_ylim(ymin, ymax)
                ax.set_xlabel("UTC Time", fontsize=14)
                ax.set_ylabel("dB", fontsize=14)
                ax.grid()
                ax.legend(fontsize=8)
                ax.set_title(opts.date + "  " + t + "  POL-" + pol, fontsize=16)
                x_tick = []
                x_tick_label = []
                if len(w_data):
                    y_wdir = []
                    angle_wdir = []
                step = orari[0].hour
                for z in range(len(orari)):
                    if orari[z].hour == step:
                        x_tick += [full_time[0][z]]
                        x_tick_label += [str(step)]
                        step = step + 1
                        if len(w_data):
                            y_wdir += [w_wind[int(closest(np.array(w_time), full_time[0][z]))]]
                            angle_wdir += [w_wdir[int(closest(np.array(w_time), full_time[0][z]))]]

                x_tick += [full_time[0][-1]]
                x_tick_label += [str(step)]
                #ax.set_xticks(x_tick)
                #ax.set_xticklabels(x_tick_label)
                ax.legend(fancybox=True, framealpha=1, shadow=True, borderpad=1, ncol=8, bbox_to_anchor=(-0.02, -0.2),
                          loc='lower left', fontsize='small')
                #fig.tight_layout()

                if len(w_data):
                    ax_weather = ax.twinx()
                    ax_weather.set_ylabel('Temperature (C)', color='r')
                    #ax_weather.set_xlim(t_stamps[0], t_stamps[-1])
                    ax_weather.set_ylim(70, 15)
                    ax_weather.set_yticks(np.arange(15, 70, 5))
                    ax_weather.set_yticklabels(np.arange(15, 70, 5), color='r')
                    ax_weather.plot(w_time, w_temp, color='r', lw=1.5, label='External Temp')
                    if opts.sbtemp:
                        sb_tempi, sb_dati = get_sbtemp(t_start, t_stop)
                        if sb_dati:
                            ax_weather.plot(sb_tempi, sb_dati, color='purple', lw=1.5, label='SmartBox Internal Temp')
                        else:
                            print "\nNo SmartBox Temperature available!"
                    ax_weather.legend(fancybox=True, framealpha=1, shadow=True, borderpad=1, ncol=8,#bbox_to_anchor=(1-0.2, 1-0.2)
                                      loc="lower right", fontsize='small')

                    ax_wind = ax.twinx()
                    #ax_wind.plot(z_wind, color='orange', lw=1.5)
                    ax_wind.plot(w_time, w_wind, color='orange', lw=1.5)
                    ax_wind.set_ylim(80, 0)
                    ax_wind.set_ylabel('Wind (Km/h)', color='orange')
                    ax_wind.tick_params(axis='y', labelcolor='orange')
                    ax_wind.spines["right"].set_position(("axes", 1.06))

                    ax_rain = ax.twinx()
                    #ax_rain.plot(z_rain, color='cyan', lw=1.5)
                    ax_rain.plot(w_time, w_rain, color='cyan', lw=3)
                    ax_rain.set_ylim(100, 0)
                    ax_rain.set_ylabel('Rain (mm)', color='cyan')
                    ax_rain.tick_params(axis='y', labelcolor='cyan')
                    ax_rain.spines["right"].set_position(("axes", 1.12))
                    #ax_weather.plot(z_temp, color='r', lw=1.5)

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
                    #fig.subplots_adjust(right=0.86)

                if not os.path.exists(path + "processed-pic"):
                    os.mkdir(path + "processed-pic")
                fname = path + "processed-pic/POWER_" + ts_to_datestring(t_start, formato="%Y-%m-%d_%H%M%S_to_")
                fname += ts_to_datestring(t_stop, formato="%Y-%m-%d_%H%M%S") + "_" + t + "_POL-" + pol
                if fmin == fmax:
                    fname += "_FREQ_%3.1f_MHz.png" % asse_x[fmin]
                else:
                    fname += "_BAND_%3.1f-%3.1f_MHz.png" % (asse_x[fmin], asse_x[fmax])
                print "Saving " + fname,

                fig.savefig(fname)
                print " ...done!"
            # except:
            #     print "No files found for POL-" + pol + " " + t