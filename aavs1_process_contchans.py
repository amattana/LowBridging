from pydaq.persisters import ChannelFormatFileManager, FileDAQModes, RawFormatFileManager
import sys
from pyaavs import station
import time
import glob
import datetime
from aavs_utils import ts_to_datestring, tstamp_to_fname, dt_to_timestamp, fname_to_tstamp
import os
import numpy as np


conf = "/opt/aavs/config/aavs1_full_station.yml"
station.load_configuration_file(conf)
station_name = station.configuration['station']['name']
modo = FileDAQModes.Continuous
file_manager = ChannelFormatFileManager(root_path="/data/data_2/2019_03_25_204_24hr/", daq_mode=modo)
tiles = range(16)
for t in tiles:
    lista = sorted(glob.glob("/data/data_2/2019_03_25_204_24hr/channel_cont_%d_*hdf5" % t))
    for ant in range(16):
        print "Processing TILE-%02d ANT-%03d" % (t + 1, ant + 1)
        datix = []
        datiy = []
        tempi = []
        for l in lista:
            dic = file_manager.get_metadata(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=0)
            samplex = []
            sampley = []
            data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(l[-21:-7]), tile_id=0, n_samples=20000000)
            d = data[0, ant, 0, :]
            datix += [np.abs(np.complex(np.sum(np.transpose(d)[0]), np.sum(np.transpose(d)[1])))]
            d = data[0, ant, 1, :]
            datiy += [np.abs(np.complex(np.sum(np.transpose(d)[0]), np.sum(np.transpose(d)[1])))]
            tempi += [timestamps[0]]
            print " - Timestamp: %s - Pol-X: %d, Pol-Y: %d" % (ts_to_datestring(tempi[-1]), datix[-1], datiy[-1])
        print "Saving file:", "/storage/monitoring/aavs1_data/AAVS1_TILE-%02d_ANT-%03d_Pol-X.txt" % (t + 1,  ant + 1)
        with open("/storage/monitoring/aavs1_data/AAVS1_TILE-%02d_ANT-%03d_Pol-X.txt" % (t + 1,  ant + 1), "w") as f:
            for n, d in enumerate(datix):
                f.write("%d\t%d\n" % (tempi[n], d))
                f.flush()
        print "Saving file:", "/storage/monitoring/aavs1_data/AAVS1_TILE-%02d_ANT-%03d_Pol-Y.txt" % (t + 1,  ant + 1)
        with open("/storage/monitoring/aavs1_data/AAVS1_TILE-%02d_ANT-%03d_Pol-Y.txt" % (t + 1,  ant + 1), "w") as f:
            for n, d in enumerate(datiy):
                f.write("%d\t%d\n" % (tempi[n], d))
                f.flush()
