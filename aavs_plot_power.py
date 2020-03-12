from matplotlib import pyplot as plt
import glob
import os
import datetime
import numpy as np

if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv
    parser = OptionParser(usage="usage: %aavs_plot_power [options]")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/power/",
                      help="Directory containing Tiles data (default: /storage/monitoring/power/)")
    parser.add_option("--station", action="store", dest="station",
                      default="AAVS2", help="Station name (default: AAVS2)")
    parser.add_option("--date", action="store", dest="date",
                      default="", help="Date in YYYY-MM-DD (required)")
    parser.add_option("--tile", action="store", dest="tile", type=str,
                      default="1", help="Tile Number")
    parser.add_option("--antenna", action="store", dest="antenna", type=int,
                      default=0, help="Antenna Name")
    parser.add_option("--equalize", action="store_true", dest="eq",
                      default=False, help="Equalize antennas power")
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

    try:
        proc_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
    except:
        print "Wrong date format or missing required argument (" + opts.date + ")"
        exit(1)

    if opts.eq:
        print "Equalization activated!"
    plt.ioff()
    fig = plt.figure(figsize=(14, 9), facecolor='w')
    ax = fig.add_subplot(1, 1, 1)
    for t in tiles:
        lista = glob.glob(path + t + "_*")
        print "Found", len(lista), "Antenna Directories"
        for pol in ["X", "Y"]:
            full_data = []
            full_time = []
            for k, l in enumerate(lista):
                fname = l + "/data/POWER_" + opts.date + "_" + l.split("/")[-1] + "_POL-" + pol + "_BAND-160-170MHz.txt"
                with open(fname) as f:
                    data = f.readlines()
                dati = []
                tempi = []
                for d in data:
                    dati += [float(d.split()[1])]
                    tempi += [int(d.split()[0])]
                if opts.eq:
                    if not k:
                        eq_value = dati[0]
                        #print "Equalization value set to ", eq_value
                    else:
                        eq_diff = eq_value - dati[0]
                        #print eq_diff, eq_value, dati[0]
                        dati = (np.array(dati) + eq_diff).tolist()
                full_data += [dati]
                full_time += [tempi]
            ax.cla()
            xmin = full_time[0][0]
            xmax = full_time[-1][-1]
            ymin = np.ceil(np.mean(full_data[0]) - 5)
            ymax = np.ceil(np.mean(full_data[0]) + 5)
            for n, l in enumerate(lista):
                ax.plot(full_time[n], full_data[n], label=l.split("/")[-1])
                xmin = min(full_time[n][0], xmin)
                xmax = max(full_time[n][-1], xmax)
                ymin = min(np.ceil(np.mean(full_data[n])) - 5, ymin)
                ymax = max(np.ceil(np.mean(full_data[n])) + 6, ymax)
            #print xmin, xmax, ymin, ymax
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ax.set_xlabel("Timestamps", fontsize=14)
            ax.set_ylabel("dB", fontsize=14)
            ax.grid()
            ax.legend(fontsize=8)
            ax.set_title(opts.date + "  " + t + "  POL-" + pol, fontsize=14)
            if not os.path.exists(path + "processed-pic"):
                os.mkdir(path + "processed-pic")
            print "Saving " + path + "processed-pic/POWER_" + opts.date + "_" + t + "_POL-" + pol + "_BAND-160-170MHz.png",
            fig.tight_layout()
            fig.savefig(path + "processed-pic/POWER_" + opts.date + "_" + t + "_POL-" + pol + "_BAND-160-170MHz.png")
            print " ...done!"
