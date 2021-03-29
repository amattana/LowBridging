from pydaq.persisters import ChannelFormatFileManager, FileDAQModes, RawFormatFileManager
import sys
import matplotlib
if not 'matplotlib.backends' in sys.modules:
    matplotlib.use('agg') # not to use X11from pydaq.persisters import ChannelFormatFileManager, FileDAQModes
import matplotlib.pyplot as plt
import numpy as np
from pyaavs import station
import time
import glob
import datetime
from aavs_utils import dt_to_timestamp, fname_to_tstamp
import os

complex_8t = np.dtype([('real', np.int8), ('imag', np.int8)])

# Antenna mapping
antenna_mapping = [0, 1, 2, 3, 12, 13, 14, 15, 4, 5, 6, 7, 8, 9, 11, 12]
nof_samples = 20000000


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S.%s"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def _connect_station(aavs_station):
    """ Return a connected station """
    # Connect to station and see if properly formed
    while True:
        try:
            aavs_station.check_station_status()
            if not aavs_station.properly_formed_station:
                raise Exception
            break
        except:
            sleep(60) 
            try:
                aavs_station.connect()
            except:
                continue



if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %aavs_check_available_data [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs2.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS1)")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data/",
                      help="Directory where plots will be generated (default: /storage/monitoring/integrated_data)")
    parser.add_option("--tile", action="store", dest="tile", type=int,
                      default=1, help="Tile Number")
    parser.add_option("--skip", action="store", dest="skip", type=int,
                      default=-1, help="Skip N blocks")
    parser.add_option("--start", action="store", dest="start",
                      default="", help="Start time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--stop", action="store", dest="stop",
                      default="", help="Stop time for filter (YYYY-mm-DD_HH:MM:SS)")
    parser.add_option("--date", action="store", dest="date",
                      default="", help="Stop time for filter (YYYY-mm-DD)")
    parser.add_option("--type", action="store", dest="type",
                      default="channel", help="File Manager Format (channel, raw)")
    parser.add_option("--mode", action="store", dest="mode",
                      default="integ", help="FileDAQ Mode (integ, cont, burst, null)")
    parser.add_option("--save", action="store_true", dest="save",
                      default=False, help="Save txt data")
    parser.add_option("--outfile", action="store", dest="outfile",
                      default="", help="Destination file")
    parser.add_option("--savecplx", action="store_true", dest="savecplx",
                      default=False, help="Save Complex Values in txt files")
    parser.add_option("--outpath", action="store", dest="outpath",
                      default="/storage/monitoring/cplx_data/", help="Destination folder")
    parser.add_option("--inputlist", action="store", dest="inputlist",
                      default="0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15", help="List of TPM input to save")

    (opts, args) = parser.parse_args(argv[1:])

    t_date = None
    t_start = None
    t_stop = None
    t_cnt = 0

    modo = FileDAQModes.Integrated
    if opts.mode == "cont":
        modo = FileDAQModes.Continuous
    elif opts.mode == "burst":
        modo = FileDAQModes.Burst
    elif opts.mode == "null":
        modo = FileDAQModes.Null

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

    #print t_date, t_start, t_stop

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']
    print "\nStation Name: ", station_name
    print "Checking directory: ", opts.directory + "\n"

    if opts.type == "channel":
        file_manager = ChannelFormatFileManager(root_path=opts.directory, daq_mode=modo)
    elif opts.type == "raw":
        file_manager = RawFormatFileManager(root_path=opts.directory, daq_mode=modo)
    else:
        print "\n Please specify a data format (channel, raw)"
        exit()
    print "\tFILE\t\t TIMESTAMP\t\tSTART\t\t\tSTOP\t\tSIZE (MB)\tBLOCKS"
    print "---------------------+-----------------+------------------+--------------------------+--------------+-----------"
    if opts.mode == "null":
        lista = sorted(glob.glob(opts.directory + "/" + opts.type + "_%d_*hdf5" % (int(opts.tile)-1)))
    else:
        lista = sorted(glob.glob(opts.directory + "/" + opts.type + "_" + opts.mode + "_%d_*hdf5" % (int(opts.tile)-1)))
    nof_tiles = 16
    for l in lista:
        dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(int(opts.tile)-1))
        #file_manager.read_data(n_samples=1)
        #file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(int(opts.tile)-1))
        if file_manager.file_partitions(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(int(opts.tile)-1)) == 0:
            total_samples = file_manager.n_samples * file_manager.n_blocks
        else:
            total_samples = file_manager.n_samples * file_manager.n_blocks * \
                            (file_manager.file_partitions(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=(int(opts.tile)-1)))
        nof_blocks = total_samples
        nof_antennas = file_manager.n_antennas * nof_tiles

        # Read data in antenna, pol, sample order
        #print l[-21:-7], fname_to_tstamp(l[-21:-7]), ts_to_datestring(fname_to_tstamp(l[-21:-7]))
        data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), n_samples=total_samples, tile_id=(int(opts.tile)-1))
        # Fix antenna mapping, convert to complex and place in data placeholder
        data = data[0, antenna_mapping, :, :].transpose((1, 0, 2))
        data = (data['real'] + 1j * data['imag']).astype(np.complex64)

        #d = data[0, 0][:]
        #print "\n", 10 * np.log10(np.sum(np.sqrt(np.power(d.real, 2))))
        if opts.save:
            if not opts.outfile == "":
                fname = opts.outfile
                with open(fname, "a") as f:
                    #for k in range(len(data[0, 0])/100):
                    print ts_to_datestring(timestamps[0], formato="%Y-%m-%d %H:%M:%S.%s")
                    f.write("%f\t%s\t" % (timestamps[0], ts_to_datestring(timestamps[0])))
                    for ant in range(16):
                        for pol in range(2):
                            f.write("%6.3f\t" % (10 * np.log10(np.sum(np.abs(data[pol, ant, :].real)))))
                    f.write("\n")
                    f.flush()
            else:
                print "WARNING: Missing required argument 'outfile'..."

        if opts.savecplx:
            for tpm_input in opts.inputlist.split(","):
                ant = int(tpm_input)
                for npol, pol in enumerate(["Pol-X", "Pol-Y"]):
                    fname = opts.outpath + "TILE-%02d_INPUT-%02d_%s.txt" % (opts.tile, ant + 1, pol)
                    with open(fname, "a") as f:
                        #for k in range(len(timestamps)):
                            #print ts_to_datestring(timestamps[0], formato="%Y-%m-%d %H:%M:%S.%s")
                        f.write("%f\t%s\t" % (timestamps[0][0], ts_to_datestring(timestamps[0][0], formato="%Y-%m-%d %H:%M:%S")))
                        f.write("%f\t%f\n" % (np.sum(np.array(data[npol, ant, :]).real), np.sum(np.array(data[npol, ant, :]).imag)))
                        f.flush()

        if len(timestamps):
            if not t_start and not t_stop:
                print " ", l[-21:-5], "\t", int(timestamps[0][0]), "\t", ts_to_datestring(timestamps[0][0]), "\t", \
                    ts_to_datestring(timestamps[-1][0]), "\t%6s"%(str(os.path.getsize(l)/1000000)), "\t\t", "%6s"%(str(len(timestamps)))
            else:
                if timestamps[0] > t_stop:
                    break
                cnt = 0
                if not t_start >= timestamps[-1]:
                    if not t_stop <= timestamps[0]:
                        for i, t in enumerate(timestamps):
                            if t_start <= t[0] <= t_stop:
                                cnt = cnt + 1
                                t_cnt = t_cnt + 1
                if cnt:
                    print " ", l[-21:-5], "\t", int(timestamps[0][0]), "\t", ts_to_datestring(timestamps[0][0]), "\t", \
                        ts_to_datestring(timestamps[-1][0]), "\t%6s\t"%(str(os.path.getsize(l)/1000000)), "\t", "%6s"%(str(cnt))
        else:
            print l[-21:-5], "\t", fname_to_tstamp(l[-21:-7]), "\t", \
                ts_to_datestring(fname_to_tstamp(l[-21:-7])), "\t", ": no metadata available"
    if t_cnt:
        print "\nFound %d measurements\n" % t_cnt
    print



