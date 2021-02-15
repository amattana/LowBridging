"""
GANTT Chart with Matplotlib
"""
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.dates
import glob
from matplotlib.dates import WEEKLY, MONTHLY, DateFormatter, rrulewrapper, RRuleLocator
import numpy as np
import os
import datetime
import calendar
from matplotlib.gridspec import GridSpec

def _create_date(datetxt):
    """Creates the date"""
    day, month, year = datetxt.split('-')
    date = dt.datetime(int(year), int(month), int(day))
    mdate = matplotlib.dates.date2num(date)
    return mdate


def ts_to_datestring(tstamp, formato="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(tstamp), formato)


def read_records(fpath):
    taskes = []
    if os.path.exists(fpath):
        file_list = sorted(glob.glob(fpath + "*.txt"))
        for ant_file in file_list:
            record = {}
            record['name'] = ant_file[len(fpath):]
            with open(ant_file) as f:
                data = f.readlines()
            activity = []
            for d in data:
                if len(d.split()) > 3:
                    d_start = d.split(",")[0].split()[0] + " " + d.split(",")[0].split()[1]
                    d_stop = d.split(",")[1].split()[0] + " " + d.split(",")[1].split()[1]
                    activity += [(calendar.timegm(datetime.datetime.strptime(d_start, "%Y-%m-%d %H:%M:%S").timetuple()),
                                  calendar.timegm(datetime.datetime.strptime(d_stop, "%Y-%m-%d %H:%M:%S").timetuple()) -
                                  calendar.timegm(datetime.datetime.strptime(d_start, "%Y-%m-%d %H:%M:%S").timetuple())),
                                 d.split(",")[2].split()[0]]
            record['events'] = activity
            taskes += [record]
    return taskes


def CreateGanttChart(fpath):
    """
        Create gantt charts with matplotlib
        Give file path
    """
    if os.path.exists(fpath):
        taskes = read_records(fpath)
        ylabels = []
        customDates = []
        #
        taskes = read_records(fpath)
        xmin = taskes[0]['events'][0][0]
        xmax = taskes[-1]['events'][0][0] + taskes[-1]['events'][0][1]
        #print xmin, xmax
        ilen = len(taskes)
        #print ilen
        pos = np.arange(0.5, ilen * 1 + 0.5)
        #print pos
        task_dates = {}
        #for i, task in enumerate(ylabels):
        #    task_dates[task] = customDates[i]
        for t in taskes:
            ylabels += [t['name'][2:-4]]
        gs = GridSpec(2, 1, hspace=1.5, wspace=0.1, left=0.25, right=0.9, bottom=0.25, top=0.9)
        fig = plt.figure(figsize=(12, 3))
        ax = fig.add_subplot(gs[0:2, 0])
        #print taskes,
        for n, t in enumerate(taskes):
            #print t['events'], [t['events'][0]], t['events'][1]
            ax.broken_barh([t['events'][0]], (n+0.1, 0.9), edgecolor='w', color=t['events'][1], alpha=0.9, label=t['name'])
            if n == 4:
                break
        locsy, labelsy = plt.yticks(pos, ylabels)
        plt.setp(labelsy, fontsize=10)
        #    ax.axis('tight')
        ax.set_ylim(ymin=-0.1, ymax=ilen * 1 + 0.5)
        ax.grid(color='g', linestyle=':')
        #ax.xaxis_date()
        #rule = rrulewrapper(WEEKLY, interval=1)
        #loc = RRuleLocator(rule)
        # formatter = DateFormatter("%d-%b '%y")
        #formatter = DateFormatter("%d-%b")

        #ax.xaxis.set_major_locator(loc)
        #ax.xaxis.set_major_formatter(formatter)
        #labelsx = ax.get_xticklabels()
        #plt.setp(labelsx, rotation=30, fontsize=8)

        font = font_manager.FontProperties(size='small')
        #ax.legend(loc=1, prop=font)

        ax.set_xlim(xmin, xmax)
        xticks = [xt['events'][0][0] for xt in taskes]
        xticks += [taskes[-1]['events'][0][0] + taskes[-1]['events'][0][1]]
        xtickslabel = [ts_to_datestring(xt, "%Y-%m") for xt in xticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xtickslabel, fontsize=10)
        ax.invert_yaxis()
        fig.autofmt_xdate()
        #plt.tight_layout()
        plt.savefig('gantt_5.png')
        plt.show()

    else:
        print "\nGive path does not exist!\n"

if __name__ == '__main__':
    fpath = "/storage/monitoring/gannt/"
    CreateGanttChart(fpath)
