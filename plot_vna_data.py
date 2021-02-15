from optparse import OptionParser
import sys
import os
import glob
import struct
import time
import numpy as np
from matplotlib import pyplot as plt
import datetime
import calendar
import warnings
warnings.filterwarnings("ignore")
from matplotlib.gridspec import GridSpec

COLORE=["b", "g"]
ERASE_LINE = '\x1b[2K'


def dt_to_timestamp(d):
    return calendar.timegm(d.timetuple())


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


def readfile(filename, tdd=False):
    with open(filename,"rb") as f:
        if tdd:
            l = f.read(8)
        vettore = f.read()
    vett=struct.unpack(str(len(vettore))+'b', vettore)
    return vett


def calcSpectra(vett):
    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett * window)
    N = len(spettro)
    acf = 2  # amplitude correction factor
    cplx = ((acf * spettro) / N)
    spettro[:] = abs((acf * spettro) / N)
    # print len(vett), len(spettro), len(np.real(spettro))
    return np.real(spettro), cplx


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
            prec = p
        else:
            if np.abs(p + off - unwrapped[-1]) > 300:
                if p > prec:
                    off = off - 360
                else:
                    off = off + 360
            unwrapped += [p + off]
            prec = p
    return unwrapped


if __name__ == "__main__":
    # Command line options
    p = OptionParser()
    p.set_usage('read_vna_data.py [options]')
    p.set_description(__doc__)
    p.add_option("--dir", action="store", dest="dir", default="", help="Directory containing tsv files to be plotted")
    p.add_option("--weather", action="store_true", dest="weather", default=False, help="Plot Weather data if available")
    p.add_option("--phase", action="store_true", dest="phase", default=False, help="Plot Phase instead of Magnitude")

    opts, args = p.parse_args(sys.argv[1:])
    if opts.dir == "" or not os.path.isdir(opts.dir):
        print "\nERROR: Missing argument or the given path does not exist"
        exit()

    data_path = opts.dir
    if data_path[-1] == "/":
        data_path = data_path[:-1]
    lista = sorted(glob.glob(data_path + "/*.tsv"))
    records = []

    gs = GridSpec(1, 1, left=0.08, top=0.935, bottom=0.12, right=0.78)
    fig = plt.figure(figsize=(14, 9), facecolor='w')
    ax = fig.add_subplot(gs[0, 0])

    s21 = 3
    offset = 2.
    #offset = 20.
    if opts.phase:
        s21 = 5
        offset = 0.005

    print
    for nl, l in enumerate(lista):
        sys.stdout.write(ERASE_LINE + "\r[%d/%d] Reading file %s..." % (nl+1, len(lista), l[l.rfind("/")+1:]))
        sys.stdout.flush()

        with open(l) as f:
            data = f.readlines()

        tempi = []
        pol_x = []
        pol_y = []
        for d in data:
            tempi += [int(d.split()[0])]  # Local time correction for AWST Time
            pol_x += [float(d.split()[s21]) - (nl/offset)]
            pol_y += [float(d.split()[s21 + 1]) - (nl/offset)]

        if opts.phase:
            pol_x = np.array(pol_x) - pol_x[0]
            pol_x = unwrap(pol_x)
            pol_y = np.array(pol_y) - pol_y[0]
            pol_y = unwrap(pol_y)
            ymin = np.minimum(min(pol_x)-100, min(pol_y)-1200)
            ymax = np.maximum(max(pol_x)+100, max(pol_y)+200)
        else:
            pol_x = moving_average(pol_x, 20)
            #pol_x = pol_x[19:]
            pol_x = np.array(pol_x) - pol_x[0]
            pol_y = moving_average(pol_y, 20)
            #pol_y = pol_y[19:]
            pol_y = np.array(pol_y) - pol_y[0]
            tempi = tempi[19:]
            ymin = -1.4
            #ymin = -0.2
            ymax = 0.2
            #ymax = 0.05

        ax.plot(tempi, np.array(pol_x) - (nl/offset), color='b', lw=1.5)
        ax.plot(tempi, np.array(pol_y) - (nl/offset), color='g', lw=1.5)
        ax.annotate(l.split(".")[0][l.rfind("_")+1:], (tempi[30], pol_x[30] + 0.01 - (nl/offset)),
                    fontsize=12, color='r', fontweight="bold")

    ax.set_ylim(ymin, ymax)
    ax.grid()

    awst = 60 * 60 * 8
    t_start = tempi[0]
    t_stop = tempi[-1]
    delta_h = (t_stop - t_start) / 3600
    x = np.array(range(t_stop - t_start + 100)) + t_start + awst

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
    ax.set_xlabel("Local time", fontsize=12)
    ax.set_title(data_path[data_path.rfind("/")+1:])
    if opts.phase:
        ax.set_ylabel("Phase (norm deg)", fontsize=12)
    else:
        ax.set_ylabel("Magnitude (norm dB)", fontsize=12)

    t_start = t_start - awst  # Local time correction for AWST Time
    t_stop = t_stop - awst  # Local time correction for AWST Time

    if opts.weather:
        print "Loading Temperature data...",
        wdata = sorted(glob.glob(data_path + "/*TEMPERATURE*.csv"))
        temp_time = []
        temp_data = []
        if wdata:
            with open(wdata[0]) as s:
                data = s.readlines()
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
        wdata = sorted(glob.glob(data_path + "/*RAIN*.csv"))
        rain_time = []
        rain_data = []
        if wdata:
            with open(wdata[0]) as s:
                data = s.readlines()
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
        wdata = sorted(glob.glob(data_path + "/*WINDSPEED*.csv"))
        wind_time = []
        wind_data = []
        if wdata:
            with open(wdata[0]) as s:
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
        sun_time = []
        sun_data = []
        wdata = sorted(glob.glob(data_path + "/*SOLAR*.csv"))
        if wdata:
            with open(wdata[0]) as s:
                data = s.readlines()
            for s in data:
                if s[0:2] == "0x":
                    tstamp = dt_to_timestamp(datetime.datetime.strptime(s.split(",")[1], " %Y-%m-%d %H:%M:%S.%f"))
                    if t_start <= tstamp <= t_stop:
                        sun_time += [tstamp]
                        sun_data += [float(s.split(",")[2])]
                    if tstamp > t_stop:
                        break
        print "done! Found %d records" % len(sun_data)

        if len(rain_data):
            ax_rain = ax.twinx()
            ax_rain.plot(np.array(rain_time) + awst, rain_data, color='steelblue', lw=1.5)
            ax_rain.set_ylim(0, 50)
            ax_rain.set_ylabel('Rain (mm)', color='steelblue')
            ax_rain.tick_params(axis='y', labelcolor='steelblue')
            ax_rain.spines["right"].set_position(("axes", 1.16))

        if len(wind_data):
            ax_wind = ax.twinx()
            ax_wind.plot(np.array(wind_time) + awst, wind_data, color='orange', lw=1.5)
            ax_wind.set_yticks(range(0, 201, 5))
            ax_wind.set_ylim(0, 100)
            ax_wind.set_ylabel('WindSpeed (mm)', color='orange')
            ax_wind.tick_params(axis='y', labelcolor='orange')
            ax_wind.spines["right"].set_position(("axes", 1.22))

        if len(sun_data):
            ax_sun = ax.twinx()
            ax_sun.plot(np.array(sun_time) + awst, sun_data, color='k', lw=1.5)
            ax_sun.set_ylim(0, 2000)
            ax_sun.set_ylabel('Solar Radiation (W/m^2)', color='k')
            ax_sun.tick_params(axis='y', labelcolor='k')
            ax_sun.spines["right"].set_position(("axes", 1.08))

        if len(temp_data):
            ax_temp = ax.twinx()
            ax_temp.plot(np.array(temp_time) + awst, temp_data, color='r', lw=1.5)
            ax_temp.set_yticks(range(0, 201, 5))
            ax_temp.set_ylim(0, 100)
            ax_temp.set_ylabel('Temperature (Celsius degrees)', color='r')
            ax_temp.tick_params(axis='y', labelcolor='r')
            ax_temp.spines["right"].set_position(("axes", 1))

    plt.show()
