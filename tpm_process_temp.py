#!/usr/bin/env python

'''

  Shows TPM Levels

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import os
import easygui
import numpy as np
from optparse import OptionParser
import matplotlib.gridspec as gridspec
from matplotlib import pyplot as plt
import datetime

colori = ['palegreen', 'green', 'lawngreen', 'yellowgreen', 'forestgreen', 'olive', 'darkolivegreen', 'springgreen',
          'aquamarine', 'mediumaquamarine', 'lightseagreen', 'mediumturquoise', 'paleturquoise', 'cyan', 'darkcyan',
          'red']

colors = ['b', 'r', 'g', 'k']

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--tile",
                      dest="tile", default=32,
                      help="The Tile number")

    parser.add_option("--all", action="store_true",
                      dest="all", default=False,
                      help="Plot all Tiles")

    parser.add_option("--subrack", action="store",
                      dest="subrack", default=0,
                      help="Plot TPMs of the given subrack")

    (options, args) = parser.parse_args()

    file = easygui.fileopenbox(msg='Please select the source files', default="auxiliary_data/*txt")
    with open(file, "r") as f:
        data = f.readlines()

    plt.ioff()
    gs = gridspec.GridSpec(7, 2, hspace=5, wspace=0.3, left=0.09, right=0.96, top=0.9, bottom=0.09)
    fig = plt.figure(figsize=(11, 7), facecolor='w')
    ax_top = fig.add_subplot(gs[0, 0:2])
    ax_top.set_axis_off()
    ax_top.plot(xrange(100), linestyle=None, color='w')
    ax_top.set_xlim(0,100)
    ax_fpga0 = fig.add_subplot(gs[1:4, 0])
    ax_fpga1 = fig.add_subplot(gs[1:4, 1])
    ax_board = fig.add_subplot(gs[4:7, 0])
    ax_current = fig.add_subplot(gs[4:7, 1])

    if not options.subrack == 0:
        tis = (np.array([1, 2, 3, 4]) + (4*((int(options.subrack) - 1) % 4))).tolist()
        tiles = []
        for i, t in enumerate(tis):
            tiles += ["%02d" % int(t)]
        print tiles

        times = []
        for i in range(len(tiles)):
            data_fpga0 = []
            data_fpga1 = []
            data_board = []
            data_current = []
            for k in data:
                if "Board:" in k:
                        c = 0
                        if k.split()[6] in tiles[i]:
                            data_current += [float(k.split()[10])]
                            data_board += [float(k.split()[12])]
                            data_fpga0 += [float(k.split()[14])]
                            data_fpga1 += [float(k.split()[16])]
                            if k.split()[6] == tiles[0]:
                                times += [datetime.datetime.strptime(k.split()[0] + " " + k.split()[1][:-4], "%Y-%m-%d %H:%M:%S")]
            ax_fpga0.plot(data_fpga0, color=colors[i], label="POS-%d"%(i+1))
            ax_fpga1.plot(data_fpga1, color=colors[i], label="POS-%d"%(i+1))
            ax_board.plot(data_board, color=colors[i], label="POS-%d"%(i+1))
            ax_current.plot(data_current, color=colors[i], label="POS-%d"%(i+1))
        ax_current.legend()


    elif not options.all:
        data_fpga0 = []
        data_fpga1 = []
        data_board = []
        data_current = []
        times = []
        failure_temp = []
        current = 8.5
        for k in data:
            if "Board:" in k:
                    if k.split()[6] == "%02d"%(int(options.tile)):
                        data_current += [float(k.split()[10])]
                        data_board += [float(k.split()[12])]
                        data_fpga0 += [float(k.split()[14])]
                        data_fpga1 += [float(k.split()[16])]
                        times += [datetime.datetime.strptime(k.split()[0] + " " + k.split()[1][:-4], "%Y-%m-%d %H:%M:%S")]
                        if ((float(k.split()[10]) < 8) and (current > 8)):
                            failure_temp += [datetime.datetime.strptime(k.split()[0] + " " + k.split()[1][:-4], "%Y-%m-%d %H:%M:%S")]
                        current = float(k.split()[10])
        ax_fpga0.plot(data_fpga0)
        ax_fpga1.plot(data_fpga1)
        ax_board.plot(data_board)
        ax_current.plot(data_current)

    else:
        for i in range(16):
            data_fpga0 = []
            data_fpga1 = []
            data_board = []
            data_current = []
            times = []
            failure_temp = []
            current = 8.5
            for c, k in enumerate(data):
                if "Board:" in k:
                        if k.split()[6] == "%02d"%(i+1):
                            data_current += [float(k.split()[10])]
                            data_board += [float(k.split()[12])]
                            data_fpga0 += [float(k.split()[14])]
                            data_fpga1 += [float(k.split()[16])]
                            times += [datetime.datetime.strptime(k.split()[0] + " " + k.split()[1][:-4], "%Y-%m-%d %H:%M:%S")]
                            if ((float(k.split()[10]) < 8) and (current > 8)):
                                failure_temp += [datetime.datetime.strptime(k.split()[0] + " " + k.split()[1][:-4], "%Y-%m-%d %H:%M:%S")]
                            current = float(k.split()[10])
            ax_fpga0.plot(data_fpga0, color=colori[i])
            ax_fpga1.plot(data_fpga1, color=colori[i])
            ax_board.plot(data_board, color=colori[i])
            ax_current.plot(data_current, color=colori[i])

    xtick = []
    xticklabel = []
    for i in range(6):
        xtick += [(len(times))/6 * i]
        xticklabel += [times[xtick[i]].time()]
    xtick += [len(times)-1]
    xticklabel += [times[len(times)-1].time()]

    ax_fpga0.set_xlim(0, len(data_fpga0))
    ax_fpga0.set_ylim(50, 85)
    ax_fpga0.grid()
    ax_fpga0.set_title("FPGA0 Temperature")
    ax_fpga0.set_ylabel("deg Celsius")
    ax_fpga0.set_xlabel("time", fontsize=10)
    ax_fpga0.set_xticks(xtick)
    ax_fpga0.set_xticklabels(xticklabel, fontsize=8, rotation=0)

    ax_fpga1.set_xlim(0, len(data_fpga0))
    ax_fpga1.set_ylim(50, 85)
    ax_fpga1.grid()
    ax_fpga1.set_title("FPGA1 Temperature")
    ax_fpga1.set_ylabel("deg Celsius")
    ax_fpga1.set_xlabel("time", fontsize=10)
    ax_fpga1.set_xticks(xtick)
    ax_fpga1.set_xticklabels(xticklabel, fontsize=8, rotation=0)

    ax_board.set_xlim(0, len(data_fpga0))
    ax_board.set_ylim(50, 70)
    ax_board.grid()
    ax_board.set_title("Board Temperature")
    ax_board.set_ylabel("deg Celsius")
    ax_board.set_xlabel("time", fontsize=10)
    ax_board.set_xticks(xtick)
    ax_board.set_xticklabels(xticklabel, fontsize=8, rotation=0)

    ax_current.set_xlim(0, len(data_fpga0))
    ax_current.set_ylim(6, 10)
    ax_current.grid()
    ax_current.set_title("Current Absorption read from PDU")
    ax_current.set_ylabel("Amp")
    ax_current.set_xlabel("time", fontsize=10)
    ax_current.set_xticks(xtick)
    ax_current.set_xticklabels(xticklabel, fontsize=8, rotation=0)

    t0 = datetime.datetime.strftime(times[0], "%Y-%m-%d  %H:%M:%S  UTC")
    ax_top.annotate("Start Time:  "+t0, (5, 0), fontsize=12, color='black')
    t1 = datetime.datetime.strftime(times[-1], "%Y-%m-%d  %H:%M:%S  UTC")
    ax_top.annotate("Stop Time:  "+t1, (60, 0), fontsize=12, color='black')
    #ax_top.annotate("TILE-%02d"%(int(options.tile)), (44, 90), fontsize=18, color='black')
    if options.subrack == 0:
        if options.all:
            ax_top.set_title("ALL Tiles", fontsize=18, color='black')
        else:
            ax_top.set_title("TILE-%02d"%(int(options.tile)), fontsize=18, color='black')
    else:
        ax_top.set_title("SubRack %d" % int(options.subrack), fontsize=18, color='black')

    if options.subrack == 0:
        for n, t in enumerate(failure_temp):
            print n+1, datetime.datetime.strftime(t, ": %Y-%m-%d  %H:%M:%S  UTC")

    plt.draw()
    plt.show()

