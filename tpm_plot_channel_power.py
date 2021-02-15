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


def dB2Linear(valueIndB):
    return pow(10, valueIndB / 10.0)


def linear2dB(valueInLinear):
    return 10.0 * np.log10(valueInLinear)


def dBm2Linear(valueIndBm):
    return dB2Linear(valueIndBm) / 1000.


def linear2dBm(valueInLinear):
    return linear2dB(valueInLinear * 1000.)


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
    p.add_option("--dir", action="store", dest="dir", default="", help="Data directory")
    p.add_option("--title", action="store", dest="title", default="", help="Plot Title")
    p.add_option("--yrange", action="store", dest="yrange", default="", help="Specify Y Range")
    p.add_option("--input", action="store", dest="input", default="1", help="TPM Input Number")
    p.add_option("--freq", action="store", dest="freq", default=200, help="Frequency (default: 200)")
    p.add_option("--tdd", action="store_true", dest="tdd", default=False, help="Read .tdd files instead of .raw files")
    p.add_option("--clean", action="store_true", dest="clean", default=False, help="Clean trace with a moving average")
    p.add_option("--weather", action="store_true", dest="weather", default=False, help="Plot weather")
    p.add_option("--phase", action="store_true", dest="phs", default=False, help="Plot Relative Phase")
    p.add_option("--resolution", dest="resolution", default=1000, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")

    opts, args = p.parse_args(sys.argv[1:])

    if opts.phs and len(opts.input.split(",")) < 2:
        print "At least 2 inputs required to plot relative phase!"
        exit()

    dbaxw = 0.08
    kw = 0
    if opts.phs:
        dbaxw = 0
        kw = 0.06

    ftypes = ".raw"
    if opts.tdd:
        ftypes = ".tdd"
    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 17)
    rbw = int(closest(resolutions, opts.resolution))
    avg = 2 ** rbw
    nsamples = 2 ** 17 / avg
    RBW = (avg * (400000.0 / 65536.0))
    asse_x = np.arange(nsamples/2) * 400./(nsamples/2.)
    range_db_min = -25
    range_db_max = 5

    # if opts.channel == "":
    freq = closest(asse_x, float(opts.freq))
    # else:
    #     xmin = int(opts.channel)
    #     xmax = int(opts.channel)

    if not opts.weather:
        gs = GridSpec(1, 1, left=0.08, top=0.935, bottom=0.12, right=0.96)
    else:
        gs = GridSpec(1, 1, left=0.08, top=0.935, bottom=0.12, right=0.82 - dbaxw - kw)
    fig = plt.figure(figsize=(14, 9), facecolor='w')
    ax = fig.add_subplot(gs[0, 0])
    ymin = 0
    ymax = 0
    if not os.path.isdir(opts.dir):
        print "\nERROR: Cannot find path: ", opts.dir
        exit()
    chan_phase = {}
    chan_power = {}
    for rxn, rx in enumerate(opts.input.split(",")):
        if not os.path.isdir(opts.dir + "/RX-%02d" % int(rx)):
            print "\nERROR: Cannot find acquisition for TPM Input #%02d " % int(rx)
            exit()
        data_dir = opts.dir + "/RX-%02d/" % int(rx)
        for pcolor, pol in enumerate(['Pol-X', 'Pol-Y']):
            serie = "RX-%02d_%s" % (int(rx), pol)
            print "Processing %s" % pol
            files = sorted(glob.glob(data_dir + pol + "/*" + ftypes))
            t_stamps = []
            chan_power[serie] = []
            chan_phase[serie] = []
            norm_factor = 0
            for h, f in enumerate(files):
                sys.stdout.write(ERASE_LINE + "\rReading file %s..." % f[f.rfind("/")+1:-4])
                sys.stdout.flush()
                try:
                    spectrum, cplvect = calcolaspettro(readfile(f, tdd=opts.tdd), nsamples)
                    if not opts.phs:
                        if not len(chan_power["RX-%02d_%s" % (int(rx), pol)]):
                            norm_factor = spectrum[freq]
                        chan_power[serie] += [spectrum[freq] - norm_factor - rxn]
                    else:
                        chan_phase[serie] += [cplvect[freq]]
                    if opts.tdd:
                        t_stamps += [dt_to_timestamp(datetime.datetime.strptime(f[-21:-4], "%Y-%m-%d_%H%M%S"))]
                    else:
                        t_stamps += [dt_to_timestamp(datetime.datetime.strptime(f[-24:-4], "%Y-%m-%d_%H%M%S%f"))]
                except:
                    pass
            sys.stdout.write(ERASE_LINE + "\rFound %d valid records.\n" % len(t_stamps))
            sys.stdout.flush()

            if not opts.phs:
                ymin = np.minimum(ymin, min(chan_power[serie]))
                ymax = np.maximum(ymax, max(chan_power[serie]))
                if opts.clean:
                    ax.plot(t_stamps[19:], moving_average(chan_power[serie], 20), lw=1, color=COLORE[pcolor])#, marker=".", markersize=1)
                else:
                    ax.plot(t_stamps, chan_power[serie], lw=1, color=COLORE[pcolor])#, marker=".", markersize=1)

    if opts.phs:
        phase_x = np.angle(chan_phase['RX-02_Pol-X'] * np.conjugate(chan_phase['RX-01_Pol-X']), deg=True)
        phase_y = np.angle(chan_phase['RX-02_Pol-Y'] * np.conjugate(chan_phase['RX-01_Pol-Y']), deg=True)
        ax.plot(t_stamps, unwrap(phase_x), lw=0, marker=".", markersize=2, color='b')
        ax.plot(t_stamps, unwrap(phase_y), lw=0, marker=".", markersize=2, color='g')
    ax.grid()

    t_start = t_stamps[0]
    t_stop = t_stamps[-1]

    if t_stop - t_start > 60 * 60:
        delta_h = (t_stamps[-1] - t_stamps[0]) / 3600
        x = np.array(range(t_stamps[-1] - t_stamps[0] + 100)) + t_stamps[0]

        xticks = np.array(range(delta_h)) * 3600 + t_stamps[0]
        xticklabels = [f if f != 0 else datetime.datetime.strftime(
            datetime.datetime.utcfromtimestamp(t_stamps[0]) + datetime.timedelta(
                (datetime.datetime.utcfromtimestamp(t_stamps[0]).hour + n) / 24), "%Y-%m-%d") for n, f in
                       enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_stamps[0]).hour) % 24)]

        decimation = 3
        xticks = xticks[1::decimation]
        xticklabels = xticklabels[1::decimation]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)
    else:
        xticks = []
        xticklabels = []
        for t in t_stamps:
            if datetime.datetime.utcfromtimestamp(t).second == 0:
                if not t in xticks:
                    xticks += [t]
                    xticklabels += [datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(t), "%H:%M:%S")]

        decimation = 1
        xticks = xticks[::decimation]
        xticklabels = xticklabels[::decimation]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels, rotation=45, fontsize=8)

    ax.set_xlim(t_stamps[0], t_stamps[-1])
    if opts.yrange=="":
        if not opts.phs:
            ax.set_ylim(ymin-2, ymax+1)
    else:
        ax.set_ylim(float(opts.yrange.split(",")[0]), float(opts.yrange.split(",")[1]))
    ax.set_xlabel("UTC time", fontsize=12)
    ax.set_ylabel("dB", fontsize=12)
    if opts.title == "":
        if not opts.phs:
            ax.set_title("Magnitude")
        else:
            ax.set_title("Phase")
    else:
        ax.set_title(opts.title)

    # if not opts.phs:
    #     ax.set_yticks([-1, 0])
    #     ax.set_yticklabels(["DIRECT LINK", "AAVS1 LOOP"], fontsize=10)
    # else:
    #     ax.set_ylabel("Phase (deg)")

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

        if not opts.phs:
            ax_db = ax.twinx()
            ax_db.set_ylabel("dB")
            ax_db.set_yticks(np.arange(0, 200, 0.5)-100)
            ax_db.set_ylim(ymin-2, ymax+1)
            ax_db.tick_params(axis='y', labelcolor='k')
            ax_db.spines["right"].set_position(("axes", 1))
            ax_db.grid()

        if len(temp_data):
            ax_temp = ax.twinx()
            ax_temp.plot(temp_time, temp_data, color='r', lw=1.5)
            ax_temp.set_yticks(range(0, 201, 5))
            ax_temp.set_ylim(0, 200)
            ax_temp.set_ylabel('Temperature (Celsius degrees)', color='r')
            ax_temp.tick_params(axis='y', labelcolor='r')
            ax_temp.spines["right"].set_position(("axes", 1 + dbaxw))

        if len(rain_data):
            ax_rain = ax.twinx()
            ax_rain.plot(rain_time, rain_data, color='steelblue', lw=1.5)
            ax_rain.set_ylim(0, 40)
            ax_rain.set_ylabel('Rain (mm)', color='steelblue')
            ax_rain.tick_params(axis='y', labelcolor='steelblue')
            ax_rain.spines["right"].set_position(("axes", 1.16 + dbaxw))

        if len(wind_data):
            ax_wind = ax.twinx()
            ax_wind.plot(wind_time, wind_data, color='orange', lw=1.5)
            ax_wind.set_yticks(range(0, 201, 5))
            ax_wind.set_ylim(0, 200)
            ax_wind.set_ylabel('WindSpeed (mm)', color='orange')
            ax_wind.tick_params(axis='y', labelcolor='orange')
            ax_wind.spines["right"].set_position(("axes", 1.24 + dbaxw))

        if len(sun_data):
            ax_sun = ax.twinx()
            ax_sun.plot(sun_time, sun_data, color='k', lw=1.5)
            ax_sun.set_ylim(0, 5000)
            ax_sun.set_ylabel('Solar Radiation (W/m^2)', color='k')
            ax_sun.tick_params(axis='y', labelcolor='k')
            ax_sun.spines["right"].set_position(("axes", 1.08 + dbaxw))

    plt.show()

