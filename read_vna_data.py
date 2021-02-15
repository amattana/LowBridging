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
    p.set_usage('read_vna_data.py [options]')
    p.set_description(__doc__)
    p.add_option("--dir", action="store", dest="dir", default="", help="Data directory")
    p.add_option("--freq", action="store", dest="freq", default=160, help="Frequency (default: 200)")
    p.add_option("--device", action="store", dest="device", default=1, help="Device Number (typically 1 or 2)")

    opts, args = p.parse_args(sys.argv[1:])
    if not os.path.isdir(opts.dir):
        print "\nERROR: Cannot find path: ", opts.dir
        exit()
    data_path = opts.dir
    if data_path[-1] == "/":
        data_path = data_path[:-1]
    lista = sorted(glob.glob(opts.dir + "/*%03d.csv" % int(opts.device)))
    records = []
    tempi = []
    for nl, l in enumerate(lista):
        sys.stdout.write(ERASE_LINE + "\r[%d/%d] Reading file %s..." % (nl+1, len(lista), l[l.rfind("/")+1:]))
        sys.stdout.flush()

        with open(l) as f:
            data = f.readlines()
        freq_record = [d for d in data if "+1.600100000" in d]
        if len(freq_record) > 0:
            records += [freq_record[0]]
            tempi += [dt_to_timestamp(datetime.datetime.strptime(l[-23:-8], "%Y%m%d_%H%M%S"))]

    print "Found %d records" % len(records)
    with open(opts.dir[:opts.dir.rfind("/") + 1] + "FREQ-160MHz_%03d.tsv"%int(opts.device), "w") as f:
        for n, r in enumerate(records):
            fields = r.split(",")
            f.write("%d\t%s\t%f\t%f\t%f\t%f\n" % (tempi[n], ts_to_datestring(tempi[n], formato="%Y-%m-%d\t%H:%M:%S"),
                                                  float(fields[1]), float(fields[2]), float(fields[3]), float(fields[4])))
            f.flush()
