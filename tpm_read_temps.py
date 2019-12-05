import datetime, time
from pyaavs import station
from optparse import OptionParser
from sys import argv, stdout
import logging
import sys
sys.path.insert(0, "/opt/aavs/bin/")
from pdu import PDU

PDU_FILE = "tpm_pdu.txt"


def getPDUinfo(fname):
    with open(fname) as f:
        data = f.readlines()
    pdus = []
    for a in data:
        pdus += [a.split()]
    return pdus



def read_current(ip, port):
    p = PDU(ip)
    c = p.port_info(port, 'current')
    del p
    return c


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
            time.sleep(60)
            try:
                aavs_station.connect()
            except:
                continue


if __name__ == "__main__":
    parser = OptionParser(usage="usage: %monitor_bandpasses [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs2.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS2)")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/auxiliary_data",
                      help="Directory where data will be saved (default: /storage/monitoring/auxiliary_data)")
    parser.add_option("--interface", action="store", dest="interface",
                      default="eth3", help="Network interface (default: eth3)")

    parser.add_option("--interval", action="store", dest="interval", type=int,
                      default=10, help="Time interval between acquisitions")

    (opts, args) = parser.parse_args(argv[1:])

    # Check if a configuration file was defined
    if opts.config is None:
        print "\nA station configuration file is required, exiting\n"
        exit()

    # Load configuration file
    station.load_configuration_file(opts.config)

    station_name = station.configuration['station']['name']

    start_time = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y%m%d_%H%M%S_")

    # Set logging
    logging.Formatter.converter = time.gmtime
    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    line_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    log_file = opts.directory + "/" + start_time + station_name + ".txt"
    ch = logging.FileHandler(filename=log_file, mode='w')
    ch2 = logging.StreamHandler(stdout)
    ch.setFormatter(line_format)
    ch2.setFormatter(line_format)
    log.addHandler(ch)
    log.addHandler(ch2)

    # Store number of tiles
    nof_tiles = len(station.configuration['tiles'])

    while True:
        try:
            # Create station instance
            aavs_station = station.Station(station.configuration)
            aavs_station.connect()
            _connect_station(aavs_station)

            pdu_list = getPDUinfo(PDU_FILE)
            pdu_handler = []
            for i in range(nof_tiles):
                tile_pdu, tile_port = [(k[1], int(k[2])) for k in pdu_list if k[0]==aavs_station.tiles[i].get_ip()][0]
                pdu_handler += [(PDU(tile_pdu), tile_port)]

            while True:
                try:
                    logging.info("\n\nReading current and temperatures...")
                    for i in range(nof_tiles):
                        logging.info("Tile %02d\tIP: %s\tCurrent: %3.1f\tBoard: %3.1f\tFPGA-0: %3.1f\tFPGA-1: %3.1f" % (
                            i + 1, aavs_station.tiles[i].get_ip(), pdu_handler[i][0].port_info(pdu_handler[i][1],'current'),
                            aavs_station.tiles[i].get_temperature(), aavs_station.tiles[i].get_fpga0_temperature(),
                            aavs_station.tiles[i].get_fpga1_temperature()))
                    time.sleep(opts.interval)
                except KeyboardInterrupt:
                    logging.info("Terminated by the user.")
                    break
        except:
            logging.error("Station communication failed, trying to re-instantiate the station...")
