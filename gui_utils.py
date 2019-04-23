import sys, math
import numpy as np
# sys.path.append("../board")
# sys.path.append("..\\")
from PyQt4 import QtCore, QtGui
import xml.etree.ElementTree as ET


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

def xmlparser(config_file):
    tree = ET.parse(config_file)
    root = tree.getroot()
    tpm_list=[]
    for node in tree.iter('iTPM'):
        tpm_elem={}
        for tpm in node:
            tpm_elem[tpm.tag] = tpm.text
        tpm_list += [tpm_elem]
    return tpm_list


def clickable(widget):
    class Filter(QtCore.QObject):
        clicked = QtCore.pyqtSignal()
        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QtCore.QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        return True
            return False
    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked

# Matplotlib stuff
import matplotlib
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar

#from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
#from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

# Other stuff
try:
    # for Python2
    from Tkinter import *
except ImportError:
    # for Python3
    from tkinter import * 


def colors(name):
    if name == "white_on_red":
        return "background-color: rgb(255, 20, 20); color: rgb(255, 255, 255)"
    elif name == "black_on_yellow":
        return "background-color: rgb(255, 255, 0); color: rgb(0, 0, 0)"
    elif name == "black_on_green":
        return "background-color: rgb(0, 255, 0); color: rgb(0, 0, 0)"
    elif name == "black_on_blue":
        return "background-color: rgb(85, 170, 255); color: rgb(0, 0, 0)"

class MplCanvas(FigureCanvas):

    def __init__( self , parent = None, dpi = 100, size = (5.95,3.4)):
        self.dpi = dpi
        self.fig = Figure(size, dpi = self.dpi, facecolor='white')
        #?self.axes1  = self.fig.add_subplot( 111 )
        self.axes1  = self.fig.add_axes( [0.12, 0.12, 0.84, 0.8] )
        self.axes1.xaxis.set_label_text("MHz", fontsize=10)
        self.axes1.yaxis.set_label_text("dB", fontsize=10)
        #self.axes1.set_facecolor('white')
        self.axes1.tick_params(axis='both', which='both', labelsize=10)
        #self.axes1.tick_params(axis='both', which='major', labelsize=10)
        self.axes1.set_ylim([-100, 0])
        self.axes1.set_xlim([0, 400])


        FigureCanvas.__init__( self, self.fig )
        FigureCanvas.setSizePolicy( self, QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding )
        FigureCanvas.updateGeometry( self )

class MatplotlibPlot(QtGui.QWidget):
    """ Class encapsulating a matplotlib plot"""
    def __init__( self, parent = None ):
        QtGui.QWidget.__init__( self, parent )
    #def __init__(self, parent = None, dpi = 100, size = (6.1,4)):
        """ Class initialiser """

        #self.dpi = dpi
        #self.figure = Figure(size, dpi = self.dpi, facecolor='white')
        self.canvas = MplCanvas() #create canvas that will hold our plot
        self.navi_toolbar = NavigationToolbar(self.canvas, self) #createa navigation toolbar for our plot canvas
        
        #self.canvas = FigureCanvas(self.figure)
        #self.canvas.setParent(parent)
        #self.navi_toolbar = NavigationToolbar(self.canvas, self)

        self.updateGeometry()
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget( self.canvas )
        #self.vbl.addSpacing(20)
        self.vbl.addWidget(self.navi_toolbar)
        self.setLayout( self.vbl )
        self.show()
        self.plotClear()



    def resetSubplots(self):
        self.nSubplot=0

    def plotCurve(self, assex, data, xAxisRange = None, yAxisRange = None, xLabel = "", yLabel = "", title="", label="", plotLog=False, nSubplots=1, hold=False):
        """ Plot the data as a curve"""

        if len(data) != 0:
            # Plan what dimensions the grid will have if there are to be subplots
            # Attempt to be roughly square but give preference to vertical stacking
            nSubplots_v = np.ceil(np.sqrt(nSubplots))
            nSubplots_h = np.ceil(float(nSubplots)/nSubplots_v)

            auto_scale_y = True            
            #yAxisRange=np.array(yAxisRange)
            #if yAxisRange is not None:
            #    auto_scale_y = False
            #    if plotLog:
            #        data[data==0] = 1
            #        yAxisRange[yAxisRange==0] = 1
            #        data= 10*np.log(data)
            #        yAxisRange = 10*np.log(yAxisRange)
            #else:
            #    auto_scale_y = True
                
            #f, ax = plt.subplots()
            #self.axes1 = self.figure.add_subplot(111)
            #self.canvas.axes1.set_title(title, fontsize=10)
            self.canvas.axes1.plot(assex, data, scaley=auto_scale_y)

            self.canvas.axes1.xaxis.set_label_text(xLabel, fontsize=10)
            self.canvas.axes1.yaxis.set_label_text(yLabel, fontsize=10)
            #self.canvas.axes1.set_facecolor('white')
            self.canvas.axes1.tick_params(axis='both', which='minor', labelsize=10)
            self.canvas.axes1.tick_params(axis='both', which='major', labelsize=10)
            self.canvas.axes1.set_ylim(yAxisRange)

            #self.axes2 = self.figure.add_subplot(212)
            #self.axes2.set_title("Secondo grafico", fontsize=12)
            #self.axes2.plot(range(np.size(data)), data, scaley=auto_scale_y)

            #self.axes2.xaxis.set_label_text(xLabel, fontsize=6)
            #self.axes2.yaxis.set_label_text(yLabel, fontsize=6)
            #self.axes2.set_axis_bgcolor('white')
            #self.axes2.tick_params(axis='both', which='minor', labelsize=10)
            #self.axes2.tick_params(axis='both', which='major', labelsize=10)
            #self.canvas.figure.tight_layout()
            self.updatePlot()


    def updatePlot(self):
        self.canvas.draw()
        self.show()
        
    def plotClear(self):
        # Reset the plot landscape
        self.canvas.axes1.clear()
        self.updatePlot()
        #self.canvas.fig.show()
        #self.show()

class MiniCanvas(FigureCanvas):

    def __init__( self , nplot, parent = None, dpi = 100, size = (11,5.3)):
        self.nplot=nplot
        self.dpi = dpi
        self.fig = Figure(size, dpi = self.dpi, facecolor='white')
        self.fig.set_tight_layout(True)
        self.ax = []
        #print self.nplot,math.sqrt(self.nplot)
        for i in xrange(self.nplot):
            self.ax += [self.fig.add_subplot(np.ceil(math.sqrt(self.nplot)),np.ceil(math.sqrt(self.nplot)),i+1)]
            #self.ax[i].xaxis.set_label_text("MHz", fontsize=7)
            #self.ax[i].yaxis.set_label_text("dB", fontsize=9)
#            self.ax[i].set_facecolor('white')
            #self.ax[i].tick_params(axis='both', which='minor', labelsize=8)
            self.ax[i].tick_params(axis='both', which='both', labelsize=8)
            self.ax[i].set_ylim([-80, -20])
            self.ax[i].set_xlim([0, 400])

        FigureCanvas.__init__( self, self.fig )
        FigureCanvas.setSizePolicy( self, QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding )
        FigureCanvas.updateGeometry( self )

class MiniPlots(QtGui.QWidget):
    """ Class encapsulating a matplotlib plot"""
    def __init__( self, parent = None , nplot = 16, dpi = 100):
        QtGui.QWidget.__init__( self, parent)
        """ Class initialiser """
        self.nplot = nplot
        #print self.nplot
        self.canvas = MiniCanvas(self.nplot, dpi=dpi) #create canvas that will hold our plot
        self.updateGeometry()
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget( self.canvas )
        self.setLayout( self.vbl )
        self.show()

    def resetSubplots(self):
        self.nSubplot=0

    #def plotCurve(self, assex, data, ant, xAxisRange = None, yAxisRange = None, colore="b", xLabel = "", yLabel = "", title="", label="", plotLog=False, nSubplots=1, hold=False):
    def plotCurve(self, assex, data, ant, xAxisRange=None, yAxisRange=None, colore="b", xLabel="", yLabel="", title="", titlesize=8, label="", plotLog=False, nSubplots=1, hold=False):
        """ Plot the data as a curve"""
        #print "Plotto"
        if len(data) != 0:
            #auto_scale_y = True
            #self.canvas.ax[ant].clear()
            self.canvas.ax[ant].plot(assex, data, scaley=True, color=colore)
            if not xAxisRange == None:
                self.canvas.ax[ant].set_xlim(xAxisRange)
            if not yAxisRange == None:
                self.canvas.ax[ant].set_ylim(yAxisRange)
            if not title=="":
                self.canvas.ax[ant].set_title(title, fontsize=titlesize)
            self.canvas.ax[ant].grid(True)
            #print "plot ", len(assex), len(data), ant

    def updatePlot(self):
        self.canvas.draw()
        self.show()
        
    def plotClear(self):
        # Reset the plot landscape
        for i in xrange(self.nplot):
             self.canvas.ax[i].clear()
        self.updatePlot()

class BarCanvas(FigureCanvas):

    def __init__( self , parent = None, dpi = 100, size = (11,5.3)):
        self.dpi = dpi
        self.fig = Figure(size, dpi = self.dpi, facecolor='white')
        self.fig.set_tight_layout(True)
        self.ax = self.fig.add_subplot(1,1,1)
        #self.ax.set_facecolor('white')
        self.ax.tick_params(axis='both', which='both', labelsize=8)
        #self.ax.tick_params(axis='both', which='major', labelsize=8)
        self.ax.set_xticks(xrange(33))
        self.ax.set_yticks([5,10,15,20,25,30,35])
        self.ax.set_ylim([0, 40])
        self.ax.set_xlim([0, 17])

        FigureCanvas.__init__( self, self.fig )
        FigureCanvas.setSizePolicy( self, QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding )
        FigureCanvas.updateGeometry( self )

class BarPlot(QtGui.QWidget):
    """ Class encapsulating a matplotlib plot"""
    def __init__( self, parent = None):
        QtGui.QWidget.__init__( self, parent )
    #def __init__(self, parent = None, dpi = 100, size = (6.1,4)):
        """ Class initialiser """
        #print self.nplot
        self.canvas = BarCanvas() #create canvas that will hold our plot
        self.updateGeometry()
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget( self.canvas )
        self.setLayout( self.vbl )
        self.show()
        self.ind = np.arange(16)

    def resetSubplots(self):
        self.nSubplot=0

    def plotBar(self, data):
        """ Plot the data as Bars"""
        remap = [1, 0, 3, 2, 5, 4, 7, 6, 17, 16, 19, 18, 21, 20, 23, 22, 30, 31, 28, 29, 26, 27, 24, 25, 14, 15, 12, 13, 10, 11, 8, 9]
        if len(data) != 0:
            self.canvas.ax.clear()
            #self.canvas.ax.set_facecolor('white')
            self.canvas.ax.tick_params(axis='both', which='both', labelsize=10)
            #self.canvas.ax.tick_params(axis='both', which='major', labelsize=10)
            self.canvas.ax.set_xticks(xrange(17))
            self.canvas.ax.set_yticks([15,20])
            self.canvas.ax.set_ylim([0, 40])
            self.canvas.ax.set_xlim([0, 17])
            self.canvas.ax.set_xlabel("ANTENNA")
            self.canvas.ax.set_ylabel("ADU RMS")
            self.canvas.ax.grid()
            dati = []
            #print len(data)
            #print data
            for i in range(len(data)):
                dati += [data[remap[i]]]
            #print len(dati)
            #print dati
            rects1 = self.canvas.ax.bar(self.ind+0.6, dati[0::2], 0.4, color='b')
            rects2 = self.canvas.ax.bar(self.ind+1, dati[1::2], 0.4, color='g')
            self.updatePlot()

    def updatePlot(self):
        self.canvas.draw()
        self.show()
        
    def plotClear(self):
        # Reset the plot landscape
        self.canvas.ax.clear()
        self.updatePlot()


class MapCanvas(FigureCanvas):
    def __init__(self, parent=None, dpi=80, size=(8, 7.2)):
        self.dpi = dpi
        self.fig = Figure(size, dpi=self.dpi, facecolor='white')
        self.fig.set_tight_layout(True)
        self.ax = self.fig.add_subplot(1, 1, 1)
        #self.ax.set_facecolor('white')
        self.ax.axis([-25, 25, -25, 25])
        #self.ax.axvline(0, color='b', linestyle='dotted')
        #self.ax.axhline(0, color='b', linestyle='dotted')

        circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
        self.ax.add_artist(circle1)
        self.ax.plot([0, 0], [-20, 20], linestyle='dotted', color='b')
        self.ax.plot([-20, 20], [0, 0], linestyle='dotted', color='b')

        # self.ax.plot([-7.5, 7.5], [20, -20], linestyle='dotted', color='b')
        # self.ax.plot([-19, 19], [20, -20], linestyle='dotted', color='b')
        # self.ax.plot([-20, 20], [8, -8], linestyle='dotted', color='b')
        # self.ax.plot([-20, 20], [-7, 7], linestyle='dotted', color='b')
        # self.ax.plot([-7.5, 7.5], [-20, 20], linestyle='dotted', color='b')
        # self.ax.plot([-19, 19], [-20, 20], linestyle='dotted', color='b')
        #
        # self.ax.annotate("TPM-1", xy=(19, 3), fontsize=10)
        # self.ax.annotate("TPM-2", xy=(17, 11), fontsize=10)
        # self.ax.annotate("TPM-3", xy=(10, 18), fontsize=10)
        # self.ax.annotate("TPM-4", xy=(2, 20), fontsize=10)
        # self.ax.annotate("TPM-5", xy=(-5, 20), fontsize=10)
        # self.ax.annotate("TPM-6", xy=(-13, 18), fontsize=10)
        # self.ax.annotate("TPM-7", xy=(-20, 11), fontsize=10)
        # self.ax.annotate("TPM-8", xy=(-22, 3), fontsize=10)
        # self.ax.annotate("TPM-16", xy=(-22, -4), fontsize=10)
        # self.ax.annotate("TPM-15", xy=(-20, -12), fontsize=10)
        # self.ax.annotate("TPM-14", xy=(-13, -18), fontsize=10)
        # self.ax.annotate("TPM-13", xy=(-5, -21), fontsize=10)
        # self.ax.annotate("TPM-12", xy=(2, -21), fontsize=10)
        # self.ax.annotate("TPM-11", xy=(10, -18), fontsize=10)
        # self.ax.annotate("TPM-10", xy=(17, -12), fontsize=10)
        # self.ax.annotate("TPM-9", xy=(19, -4), fontsize=10)
        #
        # self.ax.annotate("NORTH", xy=(-2, 22), fontweight='bold', fontsize=9)
        # self.ax.annotate("SOUTH", xy=(-1.9, -24), fontweight='bold', fontsize=9)
        # self.ax.annotate("EAST", xy=(21.5, 0), fontweight='bold', fontsize=9)
        # self.ax.annotate("WEST", xy=(-24.5, 0), fontweight='bold', fontsize=9)

        self.ax.annotate("N", xy=(-0.5, 21), fontsize=16)
        self.ax.annotate("S", xy=(-0.5, -23), fontsize=16)
        self.ax.annotate("E", xy=(21, -0.5), fontsize=16)
        self.ax.annotate("W", xy=(-23.5, -0.5), fontsize=16)

        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class MapPlot(QtGui.QWidget):
    """ Class encapsulating a matplotlib plot"""

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        # def __init__(self, parent = None, dpi = 100, size = (6.1,4)):
        """ Class initialiser """
        # print self.nplot
        self.canvas = MapCanvas()  # create canvas that will hold our plot
        self.updateGeometry()
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
        self.show()

    def resetSubplots(self):
        self.nSubplot = 0

    def plotMap(self, ant, marker='8', markersize=8, markerwidth=1, color='b'):
        """ Plot the data as Bars"""
        if len(ant) != 0:
            
            x = [float(str(a['East']).replace(",", ".")) for a in ant]
            y = [float(str(a['North']).replace(",", ".")) for a in ant]
            
            self.canvas.ax.plot(x, y, marker=marker, markersize=markersize, markeredgewidth=markerwidth, linestyle='None', color=color)
         
            self.updatePlot()

    def updatePlot(self):
        self.canvas.draw()
        self.show()

    def oPlot(self, x, y, marker='8', markersize=8, color='b'):
        self.canvas.ax.plot(x, y, marker=marker, markersize=markersize, linestyle='None', color=color)
        self.updatePlot()

    def printBase(self, ant):
        if len(ant) != 0:
            x = [float(str(a['East']).replace(",", ".")) for a in ant]
            y = [float(str(a['North']).replace(",", ".")) for a in ant]
        name = [a['Base'] for a in ant]
        for i in range(len(x)):
            self.canvas.ax.annotate("%d"%name[i], xy=(x[i],y[i]), fontsize=10, fontweight='bold')
        self.updatePlot()

    def plotClear(self):
        # Reset the plot landscape
        self.canvas.ax.clear()
        #self.canvas.ax.set_facecolor('white')
        self.canvas.ax.tick_params(axis='both', which='both', labelsize=10)
        self.canvas.ax.axis([-25, 25, -25, 25])
        #self.canvas.ax.axvline(0, color='b', linestyle='dotted')
        #self.canvas.ax.axhline(0, color='b', linestyle='dotted')

        circle1 = plt.Circle((0, 0), 20, color='wheat', linewidth=2.5)  # , fill=False)
        self.canvas.ax.add_artist(circle1)
        self.canvas.ax.plot([0, 0], [-20, 20], linestyle='dotted', color='b')
        self.canvas.ax.plot([-20, 20], [0, 0], linestyle='dotted', color='b')
        # self.canvas.ax.plot([-7.5, 7.5], [20, -20], linestyle='dotted', color='b')
        # self.canvas.ax.plot([-19, 19], [20, -20], linestyle='dotted', color='b')
        # self.canvas.ax.plot([-20, 20], [8, -8], linestyle='dotted', color='b')
        # self.canvas.ax.plot([-20, 20], [-7, 7], linestyle='dotted', color='b')
        # self.canvas.ax.plot([-7.5, 7.5], [-20, 20], linestyle='dotted', color='b')
        # self.canvas.ax.plot([-19, 19], [-20, 20], linestyle='dotted', color='b')
        # self.canvas.ax.annotate("TPM-1", xy=(19, 3), fontsize=10)
        # self.canvas.ax.annotate("TPM-2", xy=(17, 11), fontsize=10)
        # self.canvas.ax.annotate("TPM-3", xy=(10, 18), fontsize=10)
        # self.canvas.ax.annotate("TPM-4", xy=(2, 20), fontsize=10)
        # self.canvas.ax.annotate("TPM-5", xy=(-5, 20), fontsize=10)
        # self.canvas.ax.annotate("TPM-6", xy=(-13, 18), fontsize=10)
        # self.canvas.ax.annotate("TPM-7", xy=(-20, 11), fontsize=10)
        # self.canvas.ax.annotate("TPM-8", xy=(-22, 3), fontsize=10)
        # self.canvas.ax.annotate("TPM-16", xy=(-22, -4), fontsize=10)
        # self.canvas.ax.annotate("TPM-15", xy=(-20, -12), fontsize=10)
        # self.canvas.ax.annotate("TPM-14", xy=(-13, -18), fontsize=10)
        # self.canvas.ax.annotate("TPM-13", xy=(-5, -21), fontsize=10)
        # self.canvas.ax.annotate("TPM-12", xy=(2, -21), fontsize=10)
        # self.canvas.ax.annotate("TPM-11", xy=(10, -18), fontsize=10)
        # self.canvas.ax.annotate("TPM-10", xy=(17, -12), fontsize=10)
        # self.canvas.ax.annotate("TPM-9", xy=(19, -4), fontsize=10)

        # self.canvas.ax.annotate("N", xy=(-0.5, 21), fontweight='bold', fontsize=16)
        # self.canvas.ax.annotate("S", xy=(-0.5, -23), fontweight='bold', fontsize=16)
        # self.canvas.ax.annotate("E", xy=(21, -0.5), fontweight='bold', fontsize=16)
        # self.canvas.ax.annotate("W", xy=(-23.5, -0.5), fontweight='bold', fontsize=16)

        self.canvas.ax.annotate("N", xy=(-0.5, 21), fontsize=16)
        self.canvas.ax.annotate("S", xy=(-0.5, -23), fontsize=16)
        self.canvas.ax.annotate("E", xy=(21, -0.5), fontsize=16)
        self.canvas.ax.annotate("W", xy=(-23.5, -0.5), fontsize=16)

        self.updatePlot()


class AAVS_SNAP_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(970, 700)
        self.frame = QtGui.QFrame(Dialog)
        self.frame.setGeometry(QtCore.QRect(10, 10, 950, 680))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.qlabel_antnum = QtGui.QLabel(Dialog)
        self.qlabel_antnum.setGeometry(QtCore.QRect(30, 490, 191, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.qlabel_antnum.setFont(font)
        self.qlabel_antnum.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.qlabel_tile = QtGui.QLabel(Dialog)
        self.qlabel_tile.setGeometry(QtCore.QRect(30, 520, 191, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.qlabel_tile.setFont(font)
        self.qlabel_tile.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.qlabel_sb = QtGui.QLabel(Dialog)
        self.qlabel_sb.setGeometry(QtCore.QRect(300, 490, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.qlabel_sb.setFont(font)
        self.qlabel_sb.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.qlabel_rib = QtGui.QLabel(Dialog)
        self.qlabel_rib.setGeometry(QtCore.QRect(300, 520, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.qlabel_rib.setFont(font)
        self.qlabel_rib.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.qlabel_fib = QtGui.QLabel(Dialog)
        self.qlabel_fib.setGeometry(QtCore.QRect(530, 490, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.qlabel_fib.setFont(font)
        self.qlabel_fib.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.qlabel_col = QtGui.QLabel(Dialog)
        self.qlabel_col.setGeometry(QtCore.QRect(530, 520, 150, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.qlabel_col.setFont(font)
        self.qlabel_col.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.qlabel_tpm = QtGui.QLabel(Dialog)
        self.qlabel_tpm.setGeometry(QtCore.QRect(740, 490, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.qlabel_tpm.setFont(font)
        self.qlabel_tpm.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)

        self.qlabel_rx = QtGui.QLabel(Dialog)
        self.qlabel_rx.setGeometry(QtCore.QRect(740, 520, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.qlabel_rx.setFont(font)
        self.qlabel_rx.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)

        self.qlabel_des = QtGui.QLabel(Dialog)
        self.qlabel_des.setGeometry(QtCore.QRect(30, 570, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.qlabel_des.setFont(font)
        self.qlabel_des.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)

        self.qlabel_antnum.setText("Antenna Number:")
        self.qlabel_sb.setText("Smart Box:")
        self.qlabel_tile.setText("Tile:")
        self.qlabel_rib.setText("Ribbon:")
        self.qlabel_fib.setText("Fibre:")
        self.qlabel_col.setText("Colour:")
        self.qlabel_tpm.setText("TPM:")
        self.qlabel_rx.setText("RX:")
        self.qlabel_des.setText("Description")

