import os
import datetime
from pyaavs import station

PIC_PATH = "/storage/monitoring/pictures"
VIDEO_PATH = "/storage/monitoring/videos"

if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv

    parser = OptionParser(usage="usage: %aavs_gen_videos [options]")
    parser.add_option("--config", action="store", dest="config",
                      default="/opt/aavs/config/aavs2.yml",
                      help="Station configuration files to use, comma-separated (default: AAVS1)")
    parser.add_option("--directory", action="store", dest="directory",
                      default="/storage/monitoring/integrated_data/",
                      help="Directory where plots will be generated (default: /storage/monitoring/integrated_data)")
    parser.add_option("--tile", action="store", dest="tile", type=str,
                      default="1", help="Tile Number")
    parser.add_option("--date", action="store", dest="date",
                      default="", help="Stop time for filter (YYYY-mm-DD)")
    (opts, args) = parser.parse_args(argv[1:])

    t_date = None
    t_start = None
    t_stop = None

    if opts.date:
        try:
            t_date = datetime.datetime.strptime(opts.date, "%Y-%m-%d")
        except:
            print "Bad date format detected (must be YYYY-MM-DD)"

    s_date = datetime.datetime.strftime(t_date, "%Y-%m-%d")

    if "all" in opts.tile.lower():
        tiles = [i+1 for i in range(16)]
        tile_names = [str(i+1) for i in range(16)]
    else:
        tiles = [int(i) for i in opts.tile.split(",")]
        tile_names = [str(i) for i in opts.tile.split(",")]

    # Load configuration file
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']

    if station_name == "AAVS1.5":
        if "all" in opts.tile.lower():
            tiles = [1, 2, 3]
            tile_names = ["7", "11", "16"]

    print "\nStation Name: ", station_name
    print "Checking directory: ", opts.directory+station_name.lower() + "\n"
    print "Tiles to be processed: ", tile_names, "\n"

    if not os.path.exists(PIC_PATH):
        print "Generating pictures directory"
        os.mkdir(PIC_PATH)

    if not os.path.exists(VIDEO_PATH):
        print "Generating videos directory"
        os.mkdir(VIDEO_PATH)

    if not os.path.exists(VIDEO_PATH + "/" + station_name):
        print "Generating stations video directory"
        os.mkdir(VIDEO_PATH + "/" + station_name)

    if not os.path.exists(VIDEO_PATH + "/" + station_name + "/" + s_date):
        print "Generating stations video directory"
        os.mkdir(VIDEO_PATH + "/" + station_name + "/" + s_date)

    for en_tile, tile in enumerate(tiles):
        print "\nExecuting:\n\n"
        print "ffmpeg -y -f image2 -i " + PIC_PATH + "/" + station_name + "/" + s_date.replace("-", "") + \
              "/TILE-%02d/TILE-%02d_" % (int(tile_names[en_tile]), int(tile_names[en_tile])) + s_date + \
              "_%*.png -vcodec libx264 " + VIDEO_PATH + "/" + station_name + "/" + s_date + "/" + \
              s_date + "_" + station_name + "_TILE-%02d" % int(tile_names[en_tile]) + ".avi\n\n"
        os.system("ffmpeg -y -f image2 -i " + PIC_PATH + "/" + station_name + "/" + s_date.replace("-", "") +
                  "/TILE-%02d/TILE-%02d_" % (int(tile_names[en_tile]), int(tile_names[en_tile])) + s_date +
                  "_%*.png -vcodec libx264 " + VIDEO_PATH + "/" + station_name + "/" + s_date + "/" +
                  s_date + "_" + station_name + "_TILE-%02d" % int(tile_names[en_tile]) + ".avi")
