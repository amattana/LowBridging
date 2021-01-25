from optparse import OptionParser
import sys
import os
import numpy as np
from matplotlib import pyplot as plt
import datetime
import calendar
import warnings
warnings.filterwarnings("ignore")
from matplotlib.gridspec import GridSpec

COLORE=["b", "orange", "r", "g"]
def dt_to_timestamp(d):
    return calendar.timegm(d.timetuple())


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def closest(serie, num):
    return serie.tolist().index(min(serie.tolist(), key=lambda z: abs(z - num)))


if __name__ == "__main__":
    # Command line options
    p = OptionParser()
    p.set_usage('aavs_plot_cont_channel [options]')
    p.set_description(__doc__)

    p.add_option('--file', dest='file', action='store', default="",
                 help="Data file")
    p.add_option('--tiles', dest='tiles', action='store', default="all",
                 type='str', help='comma separated tile numbers (def: all)')
    p.add_option('--pol', dest='pol', action='store', default="x",
                 type='str', help='Polarization')
    opts, args = p.parse_args(sys.argv[1:])

    if os.path.exists(opts.file):
        gs = GridSpec(1, 1, left=0.06, top=0.935, bottom=0.15, right=0.80)
        fig = plt.figure(figsize=(14, 9), facecolor='w')
        ax = fig.add_subplot(gs[0, 0])

        print "Processing file: %s" % opts.file
        with open(opts.file) as f:
            data = f.readlines()
        t_stamp = []
        ora = []
        antenne = []
        for a in range(32):
            antenne += [[]]
        for d in data:
            try:
                tempo = float(d.split("\t")[0])
                t_stamp += [tempo]
                dati = d.split()[3:]
                for n, v in enumerate(dati):
                    antenne[n] += [[float(v)]]
            except:
                pass
        for n in range(32):
            antenne[n] = (np.array(antenne[n])-antenne[n][0] - n/2).tolist()
        pol = 0
        if opts.pol.lower() == "y":
            pol = 1
        for i in range(6):
            ax.plot(t_stamp, antenne[i*2], lw=1.5, color='b')#, marker=".", markersize=2)#, marker=".", markersize=3)
            ax.plot(t_stamp, antenne[i*2+1], lw=1.5, color='g')#, marker=".", markersize=2)#, marker=".", markersize=3)
        plt.grid()

        h24 = 60 * 60 * 24

        t_start = int(t_stamp[0]) - h24
        t_stop = int(t_stamp[0]) + 2 * h24

        ax.set_xlim(t_start, t_stop)
        ax.set_ylim(-10, 1)
        ax.set_xlabel("UTC Time")
        ax.set_ylabel("dB")

        delta_h = (t_stop - t_start) / 3600
        x = np.array(range(t_stop - t_start)) + t_start

        xticks = np.array(range(delta_h)) * 3600 + t_start
        xticklabels = [f if f != 0 else datetime.datetime.strftime(
            datetime.datetime.utcfromtimestamp(t_start) + datetime.timedelta(
                (datetime.datetime.utcfromtimestamp(t_start).hour + n) / 24), "%Y-%m-%d") for n, f in
                       enumerate((np.array(range(delta_h)) + datetime.datetime.utcfromtimestamp(t_start).hour) % 24)]

        div = np.array([1, 2, 3, 4, 6, 8, 12, 24])
        decimation = 3
        xticks = xticks[2::decimation]
        xticklabels = xticklabels[2::decimation]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels, rotation=90, fontsize=8)
        ax.set_title(opts.file[opts.file.rfind("/")+1:-4] + "   Tile-01")# Pol-"+opts.pol.upper())

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
        if len(sun_data):
            ax_sun = ax.twinx()
            ax_sun.plot(sun_time, sun_data, color='k', lw=1.5)
            ax_sun.set_ylim(0, 4000)
            ax_sun.set_ylabel('Solar Radiation (W/m^2)', color='k')
            ax_sun.tick_params(axis='y', labelcolor='k')
            ax_sun.spines["right"].set_position(("axes", 1.08))

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
        print "Temperature records: ", len(temp_data)
        if len(temp_data):
            ax_temp = ax.twinx()
            ax_temp.plot(temp_time, temp_data, color='r', lw=1.5)
            ax_temp.set_ylim(0, 160)
            ax_temp.set_ylabel('Temperature (Celsius degrees)', color='r')
            ax_temp.tick_params(axis='y', labelcolor='r')
            ax_temp.spines["right"].set_position(("axes", 1))

        plt.show()
    else:
        print "\nInput file does not exists!\n"
