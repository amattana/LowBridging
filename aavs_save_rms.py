from pyaavs import station
from time import sleep
import logging
import calendar
import datetime
import time
import os


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

    parser = OptionParser(usage="usage: %aavs_save_rms [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs2.yml",
                      help="Station configuration files to use, comma-separated (default: /opt/aavs/config/aavs2.yml)")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/rms",
                      help="Destination directory for data (default: /storage/monitoring/rms, station_name is automatically added)")
    parser.add_option("--interface", action="store", dest="interface",
                      default="eth3", help="Network interface (default: eth3)")
    parser.add_option("--period", action="store", dest="period", type=int,
                      default=5, help="Cadence in seconds (default: 5)")
    (opts, args) = parser.parse_args(argv[1:])

    # Set logging
    logging.Formatter.converter = time.gmtime
    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    line_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    # ch = logging.FileHandler(filename="/opt/aavs/log/integrated_data", mode='w')
    ch = logging.StreamHandler(stdout)
    ch.setFormatter(line_format)
    log.addHandler(ch)

    # Check if a configuration file was defined
    if opts.config is None:
        log.error("A station configuration file is required, exiting")
        exit()

    # Load configuration file
    station.load_configuration_file(opts.config)

    station_name = station.configuration['station']['name']

    # Store number of tiles
    nof_tiles = len(station.configuration['tiles'])

    while True:

        try:

            # Create station instance
            aavs_station = station.Station(station.configuration)
            aavs_station.connect()
            _connect_station(aavs_station)

            if not os.path.exists(opts.directory):
                os.mkdir(opts.directory)
            path = opts.directory
            if not path[-1] == "/":
                path += "/"
            path += station_name.upper()
            if not os.path.exists(path):
                os.mkdir(path)
            path += "/"

            tile_names = [("Tile-%02d"%(x+1)) for x in range(16)]
            #remap = [0, 1, 2, 3, 8, 9, 10, 11, 15, 14, 13, 12, 7, 6, 5, 4]
            rms_remap = [0, 1, 2, 3, 4, 5, 6, 7, 16, 17, 18, 19, 20, 21, 22, 23, 30, 31, 28, 29, 26, 27, 24, 25, 14, 15, 12, 13, 10, 11, 8, 9]

            orario = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%d_%H%M%S_")
            lista_file = [(path + orario + t + ".txt") for t in tile_names]
            files = []
            for l in lista_file:
                files += [open(l, "w")]
            logging.info("Logging RMS for station " + station_name)
            hours = 0
            while True:
                try:
                    for n, t in enumerate(range(nof_tiles)):
                        t_stamp = int(calendar.timegm(datetime.datetime.utcnow().timetuple()))
                        t_date = datetime.datetime.utcfromtimestamp(t_stamp)
                        date = datetime.datetime.strftime(t_date, "%Y-%m-%d %H:%M:%S")
                        if not t_date.hour == hours:
                            msg = "Continuing acquiring (t_stamp: %d, date: %s)"%(t_stamp, date)
                            logging.info(msg)
                            hours = t_date.hour
                        record = "%d\t%s\t" % (t_stamp, date)
                        rms = aavs_station.tiles[t].get_adc_rms()
                        if len(rms) == 32:
                            RMS = [rms[rms_remap[x]] for x in range(len(rms))]
                            for r in RMS:
                                record += "%6.3f\t" % r
                            record = record[:-1] + "\n"
                            files[n].write(record)
                            files[n].flush()
                    time.sleep(opts.period)
                except KeyboardInterrupt:
                    for f in files:
                        f.close()
        except:
            msg = "Exception manager..."
            logging.warning(msg)


