"""
GANTT Chart with Matplotlib
"""
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.dates
from matplotlib.dates import WEEKLY, MONTHLY, DateFormatter, rrulewrapper, RRuleLocator
import numpy as np
import os
import datetime
import calendar

def _create_date(datetxt):
    """Creates the date"""
    day, month, year = datetxt.split('-')
    date = dt.datetime(int(year), int(month), int(day))
    mdate = matplotlib.dates.date2num(date)
    return mdate


def read_records(fpath):
    taskes = []
    if os.path.exists(fpath):
        for ant_file in os.listdir(fpath):
            record = {}
            record['name'] = ant_file
            with open(fpath + "/" + ant_file) as f:
                data = f.readlines()
            activity = []
            for d in data:
                if len(d.split()) > 3:
                    d_start = d.split(",")[0].split()[0] + " " + d.split(",")[0].split()[1]
                    d_stop = d.split(",")[1].split()[0] + " " + d.split(",")[1].split()[1]
                    activity += [(calendar.timegm(datetime.datetime.strptime(d_start, "%Y-%m-%d %H:%M:%S").timetuple()),
                                calendar.timegm(datetime.datetime.strptime(d_stop, "%Y-%m-%d %H:%M:%S").timetuple()) -
                                calendar.timegm(datetime.datetime.strptime(d_start, "%Y-%m-%d %H:%M:%S").timetuple()))]
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

        ilen = len(taskes)
        pos = np.arange(0.5, ilen * 0.5 + 0.5, 0.5)
        task_dates = {}
        #for i, task in enumerate(ylabels):
        #    task_dates[task] = customDates[i]
        for t in taskes:
            ylabels += [t['name']]
        fig = plt.figure(figsize=(20, 8))
        ax = fig.add_subplot(111)
        for n, t in enumerate(taskes):
            #start_date, end_date = task_dates[ylabels[i]]
            ax.broken_barh(t['events'], (n, 0.8), edgecolor='lightgreen', color='orange', alpha=0.8)
        locsy, labelsy = plt.yticks(pos, ylabels)
        plt.setp(labelsy, fontsize=14)
        #    ax.axis('tight')
        ax.set_ylim(ymin=-0.1, ymax=ilen * 0.5 + 0.5)
        ax.grid(color='g', linestyle=':')
        ax.xaxis_date()
        rule = rrulewrapper(WEEKLY, interval=1)
        loc = RRuleLocator(rule)
        # formatter = DateFormatter("%d-%b '%y")
        formatter = DateFormatter("%d-%b")

        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(formatter)
        labelsx = ax.get_xticklabels()
        plt.setp(labelsx, rotation=30, fontsize=10)

        font = font_manager.FontProperties(size='small')
        ax.legend(loc=1, prop=font)

        ax.invert_yaxis()
        fig.autofmt_xdate()
        plt.savefig('gantt.svg')
        plt.show()

    else:
        print "\nGive path does not exist!\n"

if __name__ == '__main__':
    fpath = "/storage/monitoring/gannt/"
    CreateGanttChart(fpath)
