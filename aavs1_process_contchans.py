from pydaq.persisters import ChannelFormatFileManager, FileDAQModes, RawFormatFileManager
import sys
from pyaavs import station
import time
import glob
import datetime
from aavs_utils import ts_to_datestring, tstamp_to_fname, dt_to_timestamp, fname_to_tstamp
import os
import numpy as np
from tqdm import tqdm
from slacker import Slacker

#
slack = Slacker("")
conf = "/opt/aavs/config/aavs1_full_station.yml"
station.load_configuration_file(conf)
station_name = station.configuration['station']['name']
modo = FileDAQModes.Continuous
file_manager = ChannelFormatFileManager(root_path="/data/data_1/2019_05_15_204_station_beam/", daq_mode=modo)
tiles = range(16)
for t in tiles:
    try:
        message = "Processing AAVS1 Tile-%02d" % (t + 1)
        slack.chat.post_message("lab-test", message, as_user=True)
    except:
        pass
    print "Processing Tile-%02d" % (t + 1)
    lista = sorted(glob.glob("/data/data_1/2019_05_15_204_station_beam/channel_cont_%d_*hdf5" % t))
    for l in tqdm(range(len(lista))):
        dic = file_manager.get_metadata(timestamp=fname_to_tstamp(lista[l][-21:-7]), tile_id=t)
        data, timestamps = file_manager.read_data(timestamp=fname_to_tstamp(lista[l][-21:-7]), tile_id=t, n_samples=20000000)
        #print "Timestamp: %s " % (ts_to_datestring(timestamps[0]))
        for ant in range(16):
            #sys.stdout.write("\rProcessing TILE-%02d ANT-%03d" % (t + 1, ant + 1))
            #sys.stdout.flush()
            d = data[0, ant, 0, :]
            x = 10 * np.log10(np.abs((np.complex(np.sum(np.transpose(d.tolist())[0]), np.sum(np.transpose(d.tolist())[1]))/len(d))))
            d = data[0, ant, 1, :]
            y = 10 * np.log10(np.abs((np.complex(np.sum(np.transpose(d.tolist())[0]), np.sum(np.transpose(d.tolist())[1]))/len(d))))
            with open("/storage/monitoring/aavs1_data/AAVS1_2019_05_15_TILE-%02d_ANT-%03d_Pol-X.txt" % (t + 1,  ant + 1), "a") as f:
                f.write("%d\t%f\n" % (timestamps[0], x))
                f.flush()
            with open("/storage/monitoring/aavs1_data/AAVS1_2019_05_15_TILE-%02d_ANT-%03d_Pol-Y.txt" % (t + 1,  ant + 1), "a") as f:
                f.write("%d\t%f\n" % (timestamps[0], y))
                f.flush()
