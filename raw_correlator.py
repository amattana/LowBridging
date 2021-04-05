import matplotlib.pyplot as plt
import numpy as np
import glob
import datetime
import calendar
import struct
from matplotlib.gridspec import GridSpec
from tqdm import tqdm

COLORI=['b', 'g']


def dt_to_timestamp(d):
    return calendar.timegm(d.timetuple())


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


def corr(a, b):
    re = (a.real * b.real)+(a.imag * b.imag)
    im = (a.imag * b.real)-(a.real * b.imag)
    return np.complex(re, im)


def moving_average(xx, w):
    return np.convolve(xx, np.ones(w), 'valid') / w


def unwrap(dati):
    off = 0
    unwrapped = []
    for n, p in enumerate(dati):
        if not n:
            unwrapped += [p]
        else:
            if np.abs(p + off - unwrapped[-1]) > 179.9:
                if p > 0:
                    off = off - 360
                else:
                    off = off + 360
            unwrapped += [p + off]
    return np.array(unwrapped)


def new_unwrap(dati):
    off = 0
    unwrapped = []
    for n, p in enumerate(dati):
        if not n:
            unwrapped += [p]
        else:
            a = np.abs(p + off - unwrapped[-1])
            b = np.abs(p + off - unwrapped[-1]) + 360
            c = np.abs(p + off - unwrapped[-1]) - 360
            if min([a, b, c]) == b:
                off = off - 360
            elif min([a, b, c]) == c:
                off = off + 360
            unwrapped += [p + off]
    return unwrapped


def readfile(filename, tdd=False):
    with open(filename, "rb") as f:
        if tdd:
            l = f.read(8)
        vettore = f.read()
    vett = struct.unpack(str(len(vettore)) + 'b', vettore)
    return vett


def readtxtfile(filename):
    with open(filename, "r") as ftxt:
        data = ftxt.readlines()
    vett = []
    tempi = []
    for d in data:
        tempi += [int(float(d.split()[0]))]
        vett += [complex(int(d.split()[3]), int(d.split()[4]))]
    return tempi, vett


def calcSpectra(vett):
    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett * window)
    N = len(spettro)
    acf = 2  # amplitude correction factor
    cplx = ((acf * spettro) / N)
    spettro[:] = abs((acf * spettro) / N)
    # print len(vett), len(spettro), len(np.real(spettro))
    return np.real(spettro), cplx


def calcolaspettro(dati, nsamples=32768, chan=1):
    n = nsamples  # split and average number, from 128k to 16 of 8k # aavs1 federico
    sp = [dati[x:x + n] for x in xrange(0, len(dati), n)]
    mediato = np.zeros(len(calcSpectra(sp[0])[0]))
    cplx = 0
    #cpl = np.zeros(len(mediato))
    for k in sp:
        singolo, cplx_val = calcSpectra(k)
        mediato[:] += singolo
        cplx = cplx + cplx_val[chan]
    cplx = cplx / len(sp)
    # singoli[:] /= 16 # originale
    mediato[:] /= (2 ** 17 / nsamples)  # federico
    with np.errstate(divide='ignore', invalid='ignore'):
        mediato[:] = 20 * np.log10(mediato / 127.0)
    return mediato, cplx


def corrint(a, b, avg, freq_bin):
    nsamples = 2 ** 14 / avg
    window = np.hanning(nsamples)
    xAB = []
    for i in range(avg):
        bina = np.fft.rfft(a[(i * nsamples):(i * nsamples) + nsamples] * window)[freq_bin]
        binb = np.fft.rfft(b[(i * nsamples):(i * nsamples) + nsamples] * window)[freq_bin]
        xAB += [corr(bina, binb)]
    return np.sum(xAB)


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %raw_correlator.py [options]")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data/",
                      help="Directory where plots will be generated (default: /storage/monitoring/integrated_data)")
    parser.add_option("--tile", action="store", dest="tile", type=int,
                      default=1, help="Tile Number")
    parser.add_option("--pol", action="store", dest="pol",
                      default="x", help="Polarization")
    parser.add_option("--resolution", action="store", dest="resolution",
                      default=1000, help="Frequency resolution in KHz (it will be truncated to the closest possible)")
    parser.add_option("--freq", action="store", dest="freq", default=160, help="Frequency (default: 160)")
    parser.add_option("--weather", action="store_true", dest="weather",
                      default=False, help="Save txt data")
    parser.add_option("--start", action="store", dest="start",
                      default="", help="Start time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--stop", action="store", dest="stop",
                      default="", help="Stop time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--date", action="store", dest="date",
                      default="", help="Stop time for filter (YYYY-mm-DD)")
    parser.add_option("--tdd", action="store_true", dest="tdd",
                      default=False, help="Read .tdd files instead of .raw files")
    parser.add_option("--save", action="store_true", dest="save",
                      default=False, help="Save txt data")
    parser.add_option("--outfile", action="store", dest="outfile",
                      default="", help="Destination file")
    parser.add_option("--title", action="store", dest="title",
                      default="", help="Plot Title")
    parser.add_option("--ab", action="store", dest="ab",
                      default="14-15", help="index of the 2 antenna for correlation (def: 14-15)")
    parser.add_option("--groups", action="store", dest="groups",
                      default="", help="Plot more correlation in the same graph (example: 5-7,6-7)")
    parser.add_option("--movavg", action="store", dest="movavg", type=int,
                      default=10, help="Moving Average Window Length (default 10 samples)")
    parser.add_option("--phase", action="store_true", dest="phase",
                      default=False, help="Output the Phase instead of Magnitude")
    parser.add_option("--readtxtfile", action="store_true", dest="readtxtfile",
                      default=False, help="Input file are txt file with complex voltages of one channel")
    parser.add_option("--yrange", action="store", dest="yrange",
                      default="", help="Y plot range")

    (opts, args) = parser.parse_args(argv[1:])

    t_date = None
    t_start = None
    t_stop = None
    t_cnt = 0
    mov_avg = opts.movavg

    ftypes = ".raw"
    if opts.tdd:
        ftypes = ".tdd"
    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 15)
    rbw = int(closest(resolutions, int(opts.resolution)))
    avg = 2 ** rbw
    nsamples = 2 ** 15 / avg
    RBW = (avg * (400000.0 / 65536.0))
    asse_x = np.arange(nsamples/2) * 400./(nsamples/2.)
    range_db_min = -25
    range_db_max = 5
    freq = closest(asse_x, float(opts.freq))


    if opts.date:
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
            t_start = dt_to_timestamp(t_date)
            t_stop = dt_to_timestamp(t_date) + (60 * 60 * 24)
        except:
            print "Bad date format detected (must be YYYY-MM-DD)"
    else:
        if opts.start:
            try:
                t_start = dt_to_timestamp(datetime.datetime.strptime(opts.start, "%Y-%m-%d_%H:%M:%S"))
                print "Start Time:  " + ts_to_datestring(t_start)
            except:
                print "Bad t_start time format detected (must be YYYY-MM-DD_HH:MM:SS)"
        if opts.stop:
            try:
                t_stop = dt_to_timestamp(datetime.datetime.strptime(opts.stop, "%Y-%m-%d_%H:%M:%S"))
                print "Stop  Time:  " + ts_to_datestring(t_stop)
            except:
                print "Bad t_stop time format detected (must be YYYY-MM-DD_HH:MM:SS)"

    print "Processing directory: ", opts.directory,

    gs = GridSpec(1, 1, left=0.08, top=0.935, bottom=0.13, right=0.76)
    fig = plt.figure(figsize=(14, 9), facecolor='w')
    ax = fig.add_subplot(gs[0])

    plt.ioff()

    ftype = "raw"
    if opts.readtxtfile:
        ftype = "txt"
    if not opts.groups == "":
        groups = opts.groups.split(",")
    else:
        groups = [opts.ab]

    print
    if opts.readtxtfile:
        print "Using channelised data, single channel files"
    else:
        print "File types: ", ftypes
        print "Resolution Bandwidth: ", resolutions[rbw]
        print "Samples per FFT: ", nsamples
        print "FFT bins: ", nsamples/2
        print "Frequency: ", opts.freq
        print "Channel number: ", freq

    max_ylim = 0
    min_ylim = 0
    datapro = {}
    for gn, group in enumerate(groups):
        for npol, pol in enumerate(["Pol-X", "Pol-Y"]):
            a = int(group.split("-")[0])
            b = int(group.split("-")[1])
            files_a = sorted(glob.glob(opts.directory + "/TILE-%02d_INPUT-%02d_%s*.%s" % (int(opts.tile), a, pol, ftype)))
            files_b = sorted(glob.glob(opts.directory + "/TILE-%02d_INPUT-%02d_%s*.%s" % (int(opts.tile), b, pol, ftype)))
            data_a = []
            pow_a = []
            data_b = []
            pow_b = []
            tstamps = []
            if opts.readtxtfile:
                tstamps, data_a = readtxtfile(files_a[0])
                tstamps, data_b = readtxtfile(files_b[0])
                pow_a = 20*np.log10(np.abs(np.array(data_a)).real)
                pow_a = moving_average(np.array(pow_a), mov_avg + 1)
                pow_a = pow_a - pow_a[0] + (npol*2)
                pow_b = 20*np.log10(np.abs(np.array(data_b)).real)
                pow_b = moving_average(np.array(pow_b), mov_avg + 1)
                pow_b = pow_b - pow_b[0] + 1 + (npol*2)
            else:
                for fn in tqdm(range(len(files_a)), desc="Processing " + pol):
                    spectrum, cplval = calcolaspettro(readfile(files_a[fn], tdd=opts.tdd), nsamples, freq)
                    data_a += [cplval]
                    pow_a += [spectrum[freq]]
                    spectrum, cplval = calcolaspettro(readfile(files_b[fn], tdd=opts.tdd), nsamples, freq)
                    data_b += [cplval]
                    pow_b += [spectrum[freq]]
                    tstamps += [int(dt_to_timestamp(datetime.datetime.strptime(files_a[fn][-21:-4], "%Y-%m-%d_%H%M%S")))]
            if opts.phase:
                phase = np.angle(data_a * np.conjugate(data_b), deg=True)
                fasi = phase[mov_avg:]#moving_average(unwrap(phase), mov_avg + 1)
                fasi = fasi - fasi[0]
                ax.plot(tstamps[mov_avg:], fasi + (50*gn) , lw=1.5, marker=".", markersize=0, color=COLORI[npol])
                datapro[group.split("-")[0] + "_" + pol] = np.array(fasi)
                max_ylim = np.maximum(max(fasi) + ((np.abs(max(fasi)) + np.abs(min(fasi))) / 100. * 5), max_ylim)
                min_ylim = np.minimum(min(fasi) - ((np.abs(max(fasi)) + np.abs(min(fasi))) / 100. * 35), min_ylim)
                if opts.save:
                    if opts.outfile == "":
                        with open("/storage/monitoring/FASE-"+str(a)+"_"+"FREQ-%03d"%int(opts.freq)+"_"+pol+".txt", "w") as f:
                            for n, t in enumerate(tstamps):
                                f.write("%d\t%f\n" % (int(t), phase[n]))
                                f.flush()
            else:
                ax.plot(tstamps[mov_avg:], moving_average(pow_a, mov_avg + 1), lw=1.5, marker=".", markersize=0, color=COLORI[npol])
                ax.plot(tstamps[mov_avg:], moving_average(pow_b, mov_avg + 1), lw=1.5, marker=".", markersize=0, color=COLORI[npol])

    print "Processed " + str(len(tstamps)) + " correlations..."
    if opts.title == "":
        ax.set_title("Correlation between " + str(a) + " and " + str(b))
    else:
        ax.set_title(opts.title)
    ax.set_xlim(tstamps[mov_avg], tstamps[-1])
    ax.set_xlabel("UTC time", fontsize=12)
    if opts.phase:
        ax.set_ylabel("Phase degrees", fontsize=12)
        if not opts.yrange == "":
            max_ylim = float(opts.yrange.split(",")[0])
            min_ylim = float(opts.yrange.split(",")[1])
        ax.set_ylim(min_ylim, max_ylim)
    else:
        ax.set_ylabel("Power (dB)", fontsize=12)
        ax.set_ylim(-4, 4)
    ax.grid()

    #corrAB += [corrint(da, db, int(opts.avg), int(opts.channel))]

    t_day = int(tstamps[0])
    t_start = t_day
    t_end = int(tstamps[-1])
    t_stop = t_end
    delta_h = (t_end - t_day) / 3600
    x = np.array(range(t_end - t_day)) + t_day

    xticks = np.array(range(delta_h)) * 3600 + t_day
    xticklabels = [f if f != 0 else datetime.datetime.strftime(
        datetime.datetime.utcfromtimestamp(t_day) + datetime.timedelta(
            (datetime.datetime.utcfromtimestamp(t_day).hour + n) / 24), "%Y-%m-%d") for n, f in
                   enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_day).hour) % 24)]

    decimation = 3
    try:
        offset = decimation - int(xticklabels[0]) % decimation
    except:
        pass
    xticks = xticks[offset::decimation]
    xticklabels = xticklabels[offset::decimation]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)

    #ax.set_xlim(t_start, t_stop)

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

        if len(wind_data):
            ax_wind = ax.twinx()
            ax_wind.plot(wind_time, wind_data, color='orange', lw=1.5)
            ax_wind.set_yticks(range(0, 201, 5))
            ax_wind.set_ylim(0, 200)
            ax_wind.set_ylabel('WindSpeed (mm)', color='orange')
            ax_wind.tick_params(axis='y', labelcolor='orange')
            ax_wind.spines["right"].set_position(("axes", 1.24))

        if len(temp_data):
            ax_temp = ax.twinx()
            ax_temp.plot(temp_time, temp_data, color='r', lw=1.5)
            ax_temp.set_yticks(range(0, 201, 5))
            ax_temp.set_ylim(0, 200)
            ax_temp.set_ylabel('Temperature (Celsius degrees)', color='r')
            ax_temp.tick_params(axis='y', labelcolor='r')
            ax_temp.spines["right"].set_position(("axes", 1))

        if len(rain_data):
            ax_rain = ax.twinx()
            ax_rain.plot(rain_time, rain_data, color='steelblue', lw=2)
            ax_rain.set_ylim(0, 20)
            ax_rain.set_ylabel('Rain (mm)', color='steelblue')
            ax_rain.tick_params(axis='y', labelcolor='steelblue')
            ax_rain.spines["right"].set_position(("axes", 1.16))

        if len(sun_data):
            ax_sun = ax.twinx()
            ax_sun.plot(sun_time, sun_data, color='k', lw=1.5)
            ax_sun.set_ylim(0, 5000)
            ax_sun.set_ylabel('Solar Radiation (W/m^2)', color='k')
            ax_sun.tick_params(axis='y', labelcolor='k')
            ax_sun.spines["right"].set_position(("axes", 1.08))

    plt.show()

# This code is helpful to identify which Freq can be analysed
# import os
# for n in range(40, 400, 20):
#         os.system("python  raw_correlator.py  --directory=/storage/monitoring/syncbox_raw/saved_data/ "
#                   "--ab=7-5 --weather --title='Correlation Between Loop #1 and Loop #2 - Phase' --phase "
#                   "--freq=" + str(n) + " --movavg=20 --save")
# import glob
# import numpy as np
# pol = "Pol-Y"
# lista = sorted(glob.glob("/storage/monitoring/FASE*"+pol+"*txt"))
# fasi = []
# for l in lista:
#     with open(l) as f:
#         data = f.readlines()
#     dati = []
#     for d in data:
#         dati += [float(d.split()[1])]
#     dati = np.array(dati[1:]) - dati[1]
#     fasi += [np.abs(max(dati)) + np.abs(min(dati))]
#     print l, "%3.1f"%fasi[-1]
# fig = plt.figure(figsize=(14, 9), facecolor='w')
# gs = GridSpec(1, 1, left=0.08, top=0.935, bottom=0.12, right=0.98)
# ax = fig.add_subplot(gs[0])
# ax.bar(np.arange(len(fasi))*20+40, fasi, width=5, align='center')
# ax.set_xticks(np.arange(len(fasi))*20+40)
# ax.set_xlabel("MHz", fontsize=14)
# ax.set_ylabel("degrees", fontsize=14)
# ax.set_title("Max-Min of "+pol+" Phase")
# ax.set_xlim(0, 400)
# plt.show()
