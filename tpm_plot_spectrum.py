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
    p.set_usage('tpm_plot_spectrum.py [options]')
    p.set_description(__doc__)
    p.add_option("--dir", action="store", dest="dir", default="", help="Data directory")
    p.add_option("--input", action="store", dest="input", default="1", help="TPM Input Number")
    p.add_option("--tdd", action="store_true", dest="tdd", default=False, help="Read .tdd files instead of .raw files")
    p.add_option("--resolution", dest="resolution", default=1000, type="int",
                      help="Frequency resolution in KHz (it will be truncated to the closest possible)")

    opts, args = p.parse_args(sys.argv[1:])

    ftypes = ".raw"
    if opts.tdd:
        ftypes = ".tdd"
    resolutions = 2 ** np.array(range(16)) * (800000.0 / 2 ** 17)
    rbw = int(closest(resolutions, opts.resolution))
    avg = 2 ** rbw
    nsamples = 2 ** 17 / avg
    RBW = (avg * (400000.0 / 65536.0))
    range_db_min = -25
    range_db_max = 5

    gs = GridSpec(1, 1, left=0.08, top=0.935, bottom=0.12, right=0.96)
    fig = plt.figure(figsize=(14, 9), facecolor='w')
    ax = fig.add_subplot(gs[0, 0])
    ymin = 0
    ymax = 50
    if not os.path.isdir(opts.dir):
        print "\nERROR: Cannot find path: ", opts.dir
        exit()
    spectra = {}
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
            spectra[serie] = []
            for h, f in enumerate(files):
                sys.stdout.write(ERASE_LINE + "\rReading file %s..." % f[f.rfind("/")+1:-4])
                sys.stdout.flush()
                try:
                    spectrum, cplvect = calcolaspettro(readfile(f, tdd=opts.tdd), nsamples)
                    if not len(spectra[serie]):
                        spectra[serie] = np.zeros(len(spectrum))
                    spectra[serie][:] += dB2Linear(spectrum)
                    if opts.tdd:
                        t_stamps += [dt_to_timestamp(datetime.datetime.strptime(f[-21:-4], "%Y-%m-%d_%H%M%S"))]
                    else:
                        t_stamps += [dt_to_timestamp(datetime.datetime.strptime(f[-24:-4], "%Y-%m-%d_%H%M%S%f"))]
                except:
                    pass
            sys.stdout.write(ERASE_LINE + "\rFound %d valid records.\n" % len(t_stamps))
            sys.stdout.flush()
            asse_x = np.linspace(0, 400, len(spectrum))
            ax.plot(asse_x, linear2dB(spectra[serie]/h), lw=1, label="INPUT-%02d"%int(rx)+" "+pol)#, marker=".", markersize=1)
    #ax.plot(t_stamps, np.array(chan_phase["Pol-X"])-chan_phase["Pol-Y"], lw=0, color=COLORE[pcolor], marker=".", markersize=2)
    ax.grid()
    ax.legend()
    ax.set_xlim(asse_x[0], asse_x[-1])
    ax.set_xticks(range(0, 420, 20))
    ax.set_xticklabels(range(0, 420, 20))#, rotation=90, fontsize=8)

    ax.set_ylim(-100, 0)
    ax.set_xlabel("MHz")
    ax.set_ylabel("dB")
    ax.set_title("TPM Spectra")

    plt.show()

