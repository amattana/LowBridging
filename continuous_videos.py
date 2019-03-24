#!/usr/bin/env python

'''

  Transfer data from AAVS1-server to CERBERUS
'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import os, time
import datetime

datapath = "/data/data_2/2018-11-LOW-BRIDGING/"
debug = "DEBUG/"
imgpath = "/IMG/PLOT-A/"
videolabel = "LB_PHASE-0_A_"


'''
<html>
<head>
<title>SKA-Low Bridging Real Time Spectra</title>
<meta http-equiv="refresh" content="15">
</head>
<body>

<div name="spectra"><center><img src="spectra.png"></center></div>

<p><center><b><font size=3 face="Arial" color="black">Spectra picture updates every 30 secs</font></b></center></p>

</body>
</html>

'''


def do_html():
    with open("debug.html", "w") as f:
        f.write("<html>\n<head>\n<title>SKA-Low Bridging Debug Videos</title>")
        f.write("\n<meta http-equiv=\"refresh\" content=\"30\">\n</head>")
        f.write("\n<body>\n<div name=\"intro\">\n")
        f.write("\n<b><font size=5 face=\"Arial\" color=\"black\">Debug Videos</font><br /><font size=3 face=\"Arial\" color=\"black\">updated every about 15 minutes<br />")
        f.write("\nLast update: "+str(datetime.datetime.utcnow())+" UTC</font></b>\n</div>")
        lista = sorted(os.listdir(datapath + debug), reverse=True)
        f.write("\n<br>\n<p>\n")
        for l in lista:
            f.write("\n<font size=2 face=\"Courier\"> " + str(datetime.datetime.utcfromtimestamp(os.stat(datapath+debug+l).st_atime))[:-7])
            f.write("\n<a href=\"DEBUG/" + l + "\">" + l + "</a> ")
            f.write("</font><br />\n")
        f.write("\n</p>\n")
        f.write("\n</body>\n</html>\n")
    os.system("scp -r debug.html amattana@192.167.189.30:/home/amattana/public_html/SKA/")


if __name__ == "__main__":
    data = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%d")
    last = datetime.datetime.strftime(datetime.datetime.utcnow(), "%H")  # -datetime.timedelta(0,60*60*8) # if AWT GMT+8
    while True:
        orario = datetime.datetime.utcnow()
        ora = datetime.datetime.strftime(datetime.datetime.utcnow(), "%H")
        print "\n\nNext op:\n\n  - ffmpeg -y -f image2 -i " + datapath + data + imgpath + videolabel + data + "%*.png -vcodec libx264 " + datapath + debug + videolabel + data + ".avi\n\n"
        os.system(
            "ffmpeg -y -f image2 -i " + datapath + data + imgpath + videolabel + data + "%*.png -vcodec libx264 " + datapath + debug + videolabel + data + ".avi")
        print "\nData trasfer..."+datapath + debug + videolabel + data + ".avi\n"
        os.system(
            "scp -r " + datapath + debug + videolabel + data + ".avi amattana@192.167.189.30:/home/amattana/public_html/SKA/DEBUG/")
        if not ora == last:
            if int(ora) == 0:
                print "\n\nNext op:\n\n  - ffmpeg -y -f image2 -i " + datapath + data + imgpath + videolabel + data + "_23%*.png -vcodec libx264 " + datapath + debug + videolabel + data + "_23.avi\n\n"
                os.system(
                    "ffmpeg -y -f image2 -i " + datapath + data + imgpath + videolabel + data + "_23%*.png -vcodec libx264 " + datapath + debug + videolabel + data + "_23.avi")
                print "\nData trasfer..."+datapath + debug + videolabel + data + "_23.avi\n"
                os.system(
                    "scp -r " + datapath + debug + videolabel + data + "_23.avi amattana@192.167.189.30:/home/amattana/public_html/SKA/DEBUG/")
                data = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%d")
            else:
                print "\n\nNext op:\n\n  - ffmpeg -y -f image2 -i " + datapath + data + imgpath + videolabel + data + "_" + last + "%*.png -vcodec libx264 " + datapath + debug + videolabel + data + "_" + last + ".avi\n\n"
                os.system(
                    "ffmpeg -y -f image2 -i " + datapath + data + imgpath + videolabel + data + "_" + last + "%*.png -vcodec libx264 " + datapath + debug + videolabel + data + "_" + last + ".avi")
                print "\nData trasfer..."+datapath + debug + videolabel + data + "_" + last + ".avi\n"
                os.system(
                    "scp -r " + datapath + debug + videolabel + data + "_" + last + ".avi amattana@192.167.189.30:/home/amattana/public_html/SKA/DEBUG/")
            last = ora

        print "\n\nNext op:\n\n  - ffmpeg -y -f image2 -i " + datapath + data + imgpath + videolabel + data + "_" + ora + "%*.png -vcodec libx264 " + datapath + debug + videolabel + data + "_" + ora + ".avi\n\n"
        os.system(
            "ffmpeg -y -f image2 -i " + datapath + data + imgpath + videolabel + data + "_" + ora + "%*.png -vcodec libx264 " + datapath + debug + videolabel + data + "_" + ora + ".avi")
        print "\nData trasfer..."+datapath + debug + videolabel + data + "_" + ora + ".avi\n"
        os.system(
            "scp -r " + datapath + debug + videolabel + data + "_" + ora + ".avi amattana@192.167.189.30:/home/amattana/public_html/SKA/DEBUG/")
        do_html()
        while orario + datetime.timedelta(0, 60*15) > datetime.datetime.utcnow():
            print "Waiting for "+str(orario + datetime.timedelta(0, 60*15))[:-7] + ", actual time is " + str(datetime.datetime.utcnow())[:-7]
            time.sleep(60)
