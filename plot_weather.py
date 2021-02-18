from optparse import OptionParser
import sys
import os
import glob
import struct
import numpy as np
from matplotlib import pyplot as plt
import datetime
import calendar
import warnings
warnings.filterwarnings("ignore")
from matplotlib.gridspec import GridSpec


def dt_to_timestamp(d):
    return calendar.timegm(d.timetuple())


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


def calcolaspettro(dati, nsamples=131072):
    n = nsamples  # split and average number, from 128k to 16 of 8k # aavs1 federico
    sp = [dati[x:x + n] for x in xrange(0, len(dati), n)]
    mediato = np.zeros(len(calcSpectra(sp[0])[0]))
    #cpl = np.zeros(len(mediato))
    for k in sp:
        singolo, cplx_val = calcSpectra(k)
        mediato[:] += singolo
    #cpl[:] = cplx_val
    # singoli[:] /= 16 # originale
    mediato[:] /= (2 ** 17 / nsamples)  # federico
    with np.errstate(divide='ignore', invalid='ignore'):
        mediato[:] = 20 * np.log10(mediato / 127.0)
    return mediato, cplx_val


def moving_average(xx, w):
    return np.convolve(xx, np.ones(w), 'valid') / w


def unwrap(dati):
    off = 0
    unwrapped = []
    for n, p in enumerate(dati):
        if not n:
            unwrapped += [p]
        else:
            if np.abs(p + off - unwrapped[-1]) > 150:
                if p > 0:
                    off = off - 360
                else:
                    off = off + 360
            unwrapped += [p + off]
    return unwrapped


if __name__ == "__main__":
    # Command line options
    p = OptionParser()
    p.set_usage('tpm_plot_channel_power.py [options]')
    p.set_description(__doc__)
    p.add_option("--start", action="store", dest="start", default="", help="Start time for filter (YYYY-mm-DD_HH:MM:SS)")
    p.add_option("--stop", action="store", dest="stop", default="", help="Stop time for filter (YYYY-mm-DD_HH:MM:SS)")
    p.add_option("--date", action="store", dest="date", default="", help="Day to be processed (YYYY-mm-dd)")
    opts, args = p.parse_args(sys.argv[1:])

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

    gs = GridSpec(1, 1, left=0.08, top=0.935, bottom=0.12, right=0.86)
    fig = plt.figure(figsize=(14, 9), facecolor='w')
    ax = fig.add_subplot(gs[0, 0])

    delta_h = (t_stop - t_start) / 3600
    x = np.array(range(t_stop - t_start + 100)) + t_start

    xticks = np.array(range(delta_h)) * 3600 + t_start
    xticklabels = [f if f != 0 else datetime.datetime.strftime(
        datetime.datetime.utcfromtimestamp(t_start) + datetime.timedelta(
            (datetime.datetime.utcfromtimestamp(t_start).hour + n) / 24), "%Y-%m-%d") for n, f in
                   enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) % 24)]

    decimation = 3
    xticks = xticks[::decimation]
    xticklabels = xticklabels[::decimation]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)

    ax.set_xlim(t_start, t_stop)
    #ax.set_ylim(ymin-2, ymax+1)
    ax.set_xlabel("UTC time")
    ax.set_title("MRO Weather")
    ax.set_ylabel("External Temperature")

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
        if datetime.datetime.strptime(ts_to_datestring(t_stop, "%Y-%m"), "%Y-%m") >= datetime.datetime.strptime(
                wf[-11:-4], "%Y-%m"):
            if datetime.datetime.strptime(ts_to_datestring(t_start, "%Y-%m"), "%Y-%m") <= \
                    datetime.datetime.strptime(wf[-11:-4], "%Y-%m"):
                with open(wf) as s:
                    data = s.readlines()
                for s in data:
                    if s[0:2] == "0x":
                        try:
                            tstamp = dt_to_timestamp(
                                datetime.datetime.strptime(s.split(",")[1], " %Y-%m-%d %H:%M:%S.%f"))
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

    if len(temp_data):
        ax.plot(temp_time, temp_data, color='r', lw=1.5)
        ax.set_yticks(range(0, 201, 5))
        ax.set_ylim(0, 70)
        ax.set_ylabel('Temperature (Celsius degrees)', color='r')
        ax.tick_params(axis='y', labelcolor='r')

    if len(wind_data):
        ax_wind = ax.twinx()
        ax_wind.plot(wind_time, wind_data, color='orange', lw=1.5)
        ax_wind.set_yticks(range(0, 201, 5))
        ax_wind.set_ylim(0, 100)
        ax_wind.set_ylabel('WindSpeed (mm)', color='orange')
        ax_wind.tick_params(axis='y', labelcolor='orange')
        ax_wind.spines["right"].set_position(("axes", 1.12))

    if len(rain_data):
        ax_rain = ax.twinx()
        ax_rain.plot(rain_time, rain_data, color='steelblue', lw=1.5)
        ax_rain.set_ylim(0, 20)
        ax_rain.set_ylabel('Rain (mm)', color='steelblue')
        ax_rain.tick_params(axis='y', labelcolor='steelblue')
        ax_rain.spines["right"].set_position(("axes", 1.06))

    if len(sun_data):
        ax_sun = ax.twinx()
        ax_sun.plot(sun_time, sun_data, color='k', lw=1.5)
        ax_sun.set_ylim(0, 2000)
        ax_sun.set_ylabel('Solar Radiation (W/m^2)', color='k')
        ax_sun.tick_params(axis='y', labelcolor='k')
        ax_sun.spines["right"].set_position(("axes", 1))

    if len(temp_data):
        ax.plot(temp_time, temp_data, color='r', lw=1.5)

    plt.show()

