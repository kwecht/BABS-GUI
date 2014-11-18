########################################################################
#
#        Kevin Wecht                4 November 2014
#
#    Bay Area Bicycle Share (BABS) Open Data Challenge
#
########################################################################
#
#    This file begins a Qt window to support interactive
#       visualization of the BABS data.
#
#    OUTLINE
#       functionname - description
#
########################################################################

# Import modules required by these functions
import sys
from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import random
import BabsFunctions
import BabsClasses
import pandas as pd
#import pdb
import itertools

########################################################################


# Define class to hold our main interactive window
class MainWindow(QtGui.QWidget):
    """Python Class to hold our main interactive GUI window.
Inherits methods from QtGui.QWidget.

METHODS
   __init__    -  initializes the window class
   initUI      -  initializes and draws the GUI grid
   initPlot    -  places Matplotlib canvas on the grid
   initOptions -  places widgets on the grid to manipulate the plot"""


    def __init__(self):
        """Initialize the window class and its parent class."""
        super(MainWindow, self).__init__()

        # This function initializes the GUI.
        self.initUI()

    def initUI(self):
        """Initialize the GUI."""

        # Create grid layout on which the GUI will be based
        self.initGrid()

        # ---- Initialize different types of widgets on the grid
        self.initOptions()  # Options for selecting what to plot
        self.initPlot()     # After initializing the options
        #self.initOther()    # Other things...
        #self.quitbutton = QtGui.QPushButton('Button',self)
        #self.grid.addWidget(self.quitbutton,self.gridParams.nrow-1,self.gridParams.ncol-1)

        # Set layout after all widgets have been placed on the grid
        self.setLayout(self.grid) 
        
        # Set size of window and window title
        self.setGeometry(100, 100, 1450, 900)
        self.setWindowTitle('Review')    

        # Set the focus of the GUI on the matplotlib window for click events
        self.canvas.setFocusPolicy( QtCore.Qt.ClickFocus )
        self.canvas.setFocus()

        # Show window!
        self.show()

    def initGrid(self):
        """Set up the grid layout on which the GUI will be based."""

        # Create Grid
        self.grid = QtGui.QGridLayout()

        # Assign Parameters 
        self.gridParams = BabsClasses.GridParams()

        # Set even scaling of columns when resizing the window
        for ii in range(self.gridParams.ncol):
            self.grid.setColumnStretch(ii,1)


        # Set default grid spacing
        self.grid.setSpacing(self.gridParams.spacing)

        # Set column width for the final five columns
        #for ii in range(self.optcol0,self.optcol1+1):
        #    self.

    def initPlot(self):
        """Initialize plot in window."""

        # Create figure and canvas to display plot
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar= NavigationToolbar(self.canvas,self.canvas)

        # Place canvas on the grid
        self.grid.addWidget(self.canvas,self.gridParams.plotrow0,
                                        self.gridParams.plotcol0,
                                        self.gridParams.plotnrow,
                                        self.gridParams.plotncol)

        # Create axis on which to plot everything
        self.ax = self.figure.add_subplot(111)
        self.ax.hold(False)

        # Create the initial plot from the buttons already selected
        #   during initOptions()
        self.updateplot(None)


    def initOptions(self):
        """Initialize widgets to control matplotlib plot."""

        # PlotOptions object to hold the options for this plot
        self.PlotOptions = BabsClasses.PlotOptions()

        # Initialize BarPlot options
        self.initMainType()   # X-axis: timeseries, histogram, ...
        self.initMainGroup()  # number of rides, duration, ...
        self.initBinGroup()   # how to bin the data
        self.initTimeBin()    # If binning by time, what time step to use

        # Initialize Bar plot divisions
        self.initDivisions()  # weather, region, customer type, ...

        # Initialize Line Overplot options
        self.initOverplots()  # weather, number of rides, duration, ...

        # Initialize Data Filtering options
        self.initFilters()    # date range, day of week, hour of day, region, weather, ...

        # Initialize Refresh and Quit Buttons
        self.initButtons()


    def EnableAll(self):
        """
        Enable all widgets in the GUI.
        Called before disabling select widgets based on current selections.
        """

        # Enable Main Type and Main Group widgets
        self.mainType.setEnabled(True)
        self.mainGroup.setEnabled(True)

        # Enable Time options and plot refresh button
        self.timeGroup.setEnabled(True)
        self.timeText.setEnabled(True)

        # Enable division radio buttons
        for button in self.divisionGroup.buttons():
            button.setEnabled(True)

        # Enable all check boxes in the overplot options

        # Enable all check boxes in filtering options
        


    def DisableOptions(self,NewOptions):
        """
        Disable some widgets based on currently selected widgets.
        For example, when showing number of rides vs. day of week,
        disable time averaging and disable the option of dividing 
        bars by day of the week.
        """

        # Begin by enabling all widgets
        self.EnableAll()

        # If plotting a timeseries, disable the bin options other than
        #    Time (other)
        if NewOptions.typeid==0:
            NewOptions.binid = 0   # Force binid to be Time (other)
            self.binGroup.setCurrentIndex(0)

        # If plotting a histogram, disable Time (other) by 
        #    forcing that selection to change to Number of Rides
        if NewOptions.typeid==1:
            if NewOptions.binid==0:
                NewOptions.binid=1
                self.binGroup.setCurrentIndex(1)

        # If binning data by day of week, hour of day, or region
        #    don't set time manually
        if NewOptions.binid>=2:
            self.timeGroup.setEnabled(False)
            self.timeText.setEnabled(False)

        # If plotting by Hour of Day, day of week, or region, don't divide
        #    the bar by hour of day, day of week, or region
        names = ['Day of Week','Hour of Day','Region']
        inds  = [2,3,4]
        for name,ind in zip(names,inds):
            if NewOptions.binid==ind:
                for button in self.divisionGroup.buttons():
                    if str(button.objectName())==name: button.setEnabled(False)

        # Disable the "Other" radio button in the divisions section
        for button in self.divisionGroup.buttons():
            if str(button.objectName())=='Other': button.setEnabled(False)


    def setLabels(self,NewOptions):
        """
        Sets plot title, axis labels, and tick marks for the current plot.
        """

        # Set plot title = title0 + ' of ' + title1
        title0 = ['Timeseries', 'Histogram']
        title1 = ['Number of Rides', 'Ride Duration [minutes]', 'Ride Distance [km]']
        title2 = ['Time (other)', 'Number of Rides', 'Day of Week average', 
                  'Hour of Day average', 'Region']
        title = (title0[NewOptions.typeid] + ' of ' + 
                 title1[NewOptions.barid] + ' binned by ' + 
                 title2[NewOptions.binid])

        # Set y-axis label
        if NewOptions.typeid==1: 
            ylabel = 'Number of Occurances'
        else:
            ylabel = title1[NewOptions.barid]

        # Set x-axis label
        if NewOptions.typeid==0: xlabel='Date'
        if NewOptions.typeid==1: xlabel=title2[NewOptions.binid]

        # Set x-tick labels
        xticks = []

        # Set y-tick labels


        # Place all labels on the plot
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        #plt.yticks()
        #plt.xticks()

    def initMainType(self):
        """Initialize widgets to control the type of bar plot"""

        # Group to hold the drop down list options buttons
        self.mainType = QtGui.QComboBox()

        # Label above the Bar Plot options
        top_label  = QtGui.QLabel('Interacting with BABS data')
        top_label.setAlignment(QtCore.Qt.AlignCenter)
        thisfont = top_label.font()
        thisfont.setPointSize(24)
        top_label.setFont(thisfont)

        show_label  = QtGui.QLabel('Show: ')
        show_label.setAlignment(QtCore.Qt.AlignCenter)

        # Radio Buttons
        button_names = ['Timeseries', 'Histogram']#, ]
        buttonlist = []

        # Add each name to the drop down list
        self.mainType.addItems(button_names)

        # Upon item selection, call the method updateplot
        self.connect(self.mainType, QtCore.SIGNAL('activated(QString)'), self.updateplot)

        # Place widgets on grid
        rowoffset = self.gridParams.maintype_row0
        self.grid.addWidget( top_label, self.gridParams.optrow0+0+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(0),
                             1,
                             self.gridParams.optncol )
        self.grid.addWidget( show_label,    self.gridParams.optrow0+2+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(0)+1,
                             1, 2 )
        self.grid.addWidget( self.mainType,    self.gridParams.optrow0+2+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(1),
                             1, self.gridParams.nfiltercol )


    def initMainGroup(self):
        
        # Group to hold the drop down list options buttons
        self.mainGroup = QtGui.QComboBox()

        # Label above the Bar Plot options
        of_label  = QtGui.QLabel(' of ')
        of_label.setAlignment(QtCore.Qt.AlignCenter)

        # Drop down list options 
        button_names = ['Number Rides', 'Duration', 'Distance']
        buttonlist = []

        # Add each name to the drop down list
        self.mainGroup.addItems(button_names)

        # Upon item selection, call the method updateplot
        self.connect(self.mainGroup, QtCore.SIGNAL('activated(QString)'), self.updateplot)

        # Place widgets on grid
        rowoffset = self.gridParams.maingroup_row0
        coloffset = 2
        self.grid.addWidget( of_label, self.gridParams.optrow0+1+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(0+coloffset),
                             1, self.gridParams.nfiltercol-1  )
        self.grid.addWidget( self.mainGroup,    self.gridParams.optrow0+1+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(1+coloffset)-1,
                             1, self.gridParams.nfiltercol  )


    def initBinGroup(self):
        """Create drop down list of ways to bin data for histogram."""

        # Group to hold the bin drop down list
        self.binGroup = QtGui.QComboBox()

        # Message to the left of the text box
        bin_label = QtGui.QLabel('Bin by: ')
        bin_label.setAlignment(QtCore.Qt.AlignCenter)

        # Drop down list options
        button_names = ['Time (other)', 'Number of Rides', 'Day of Week', 'Hour of Day', 'Region']
        buttonlist = []

        # Add each name to the drop down list
        self.binGroup.addItems(button_names)

        # Upon selection, call the method updateplot
        self.connect(self.binGroup, QtCore.SIGNAL('activated(QString)'), self.updateplot)

        # Place widgets on grid
        rowoffset = self.gridParams.bingroup_row0
        self.grid.addWidget( bin_label, self.gridParams.optrow0+1+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(0)+1,
                             1, self.gridParams.nfiltercol-1  )
        self.grid.addWidget( self.binGroup,    self.gridParams.optrow0+1+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(1),
                             1, self.gridParams.nfiltercol  )


    def initTimeBin(self):
        """Create text entry and combo box telling us how to bin observations in time."""

        # Label to hold grid information
        set_label = QtGui.QLabel('Timestep: ')
        set_label.setAlignment(QtCore.Qt.AlignCenter)

        # Group to hold the time unit drop down list
        self.timeGroup = QtGui.QComboBox()

        # Label to the left of text entry and drop down lists
        self.timeText  = QtGui.QLineEdit('7')

        # Drop down list options 
        button_names = ['Hours', 'Days']
        buttonlist = []

        # Add each name to the drop down list
        self.timeGroup.addItems(button_names)
        self.timeGroup.setCurrentIndex(button_names.index('Days'))

        # Upon item selection, call the method updateplot
        self.connect(self.timeGroup, QtCore.SIGNAL('activated(QString)'), self.updateplot)


        # Place widgets on grid
        rowoffset = self.gridParams.timegroup_row0
        self.grid.addWidget( set_label, self.gridParams.optrow0+1+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(2)+1,
                             1, 1 )
        self.grid.addWidget( self.timeText, self.gridParams.optrow0+1+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(2)+2,
                             1, self.gridParams.nfiltercol-2 )
        self.grid.addWidget( self.timeGroup, self.gridParams.optrow0+1+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(3),
                             1, self.gridParams.nfiltercol-1 )


    def initDivisions(self):
        """Initialize widgets to divide each bar in the bar plot"""

        # Lots of radio buttons that determine if we should divide the 
        # bars in the bar plot by different categories 
        #   (time of day, weather, day of week, type of customer, etc.

        # Group to hold the radio buttons
        self.divisionGroup = QtGui.QButtonGroup()

        # Label above the Division Options
        label_timeseries  = QtGui.QLabel('Bar Division Options')
        label_timeseries.setAlignment(QtCore.Qt.AlignCenter)
        thisfont = label_timeseries.font()
        thisfont.setPointSize(16)
        label_timeseries.setFont(thisfont)

        # Radio Buttons
        button_names = ['None', 'Customer Type', 'Day of Week', 
                        'Hour of Day', 'Region', 'Other']
        buttonlist = []

        # Add buttons to the group, no default checked
        counter = 0
        for button in button_names:
            thisbutton = QtGui.QRadioButton(button)
            thisbutton.setObjectName(button)
            buttonlist.append(thisbutton)
            buttonlist[counter].clicked.connect(self.updateplot)
            self.divisionGroup.addButton(thisbutton)
            self.divisionGroup.setId(thisbutton, counter)
            counter += 1

        # Make the group exclusive
        self.divisionGroup.setExclusive(True)

        # Set Default
        buttonlist[0].setChecked(True)

        # Place widgets on grid
        rowoffset = self.gridParams.divisiongroup_row0
        self.grid.addWidget( label_timeseries, self.gridParams.optrow0+0+rowoffset,
                                               self.gridParams.optcol0,
                                               1,
                                               self.gridParams.optncol, )
        ijs = [value for value in itertools.product([0,1,2],repeat=2) if value[0]<2]
        for index in range(len(buttonlist)):
            self.grid.addWidget( buttonlist[index],
                                 self.gridParams.optrow0+ijs[index][0]+1+rowoffset,
                                 self.gridParams.optcol0+self.gridParams.nfiltercol*(ijs[index][1]+1),
                                 1, self.gridParams.nfiltercol )


    def initOverplots(self):
        """Initialize widgets to control the items to plot on top of the bar plot"""

        label_timeseries  = QtGui.QLabel('Overplot Options  (out of service)')
        label_timeseries.setAlignment(QtCore.Qt.AlignCenter)
        thisfont = label_timeseries.font()
        thisfont.setPointSize(16)
        label_timeseries.setFont(thisfont)

        checkbox_nrides   = QtGui.QCheckBox('Number Rides',self)
        checkbox_duration = QtGui.QCheckBox('Duration [min]',self)
        checkbox_rain     = QtGui.QCheckBox('Precipitation',self)
        checkbox_wind     = QtGui.QCheckBox('Wind',self)

        # Set default values for which boxes are checked 
        #   Default is not checked
        #checkbox_nrides.toggle()   # Initialize plot with # of rides displayed

        # Associate actions with each checkbox
        #    When the state of the checkbox changes, execute these functions
        #checkbox_nrides.stateChanged.connect(self.function_name)  
        #checkbox_duration.stateChanged.connect(self.function_name)

        # Place widgets on grid
        rowoffset = self.gridParams.overgroup_row0
        self.grid.addWidget( label_timeseries, self.gridParams.optrow0+rowoffset,
                                               self.gridParams.optcol0,
                                               1,
                                               self.gridParams.optncol, )
        self.grid.addWidget( checkbox_nrides,  self.gridParams.optrow0+1+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(1),
                             1, self.gridParams.nfiltercol )
        self.grid.addWidget( checkbox_duration,self.gridParams.optrow0+1+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(2),
                             1, self.gridParams.nfiltercol )
        self.grid.addWidget( checkbox_rain,    self.gridParams.optrow0+2+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(1),
                             1, self.gridParams.nfiltercol )
        self.grid.addWidget( checkbox_wind,    self.gridParams.optrow0+2+rowoffset,
                             self.gridParams.optcol0+self.gridParams.nfiltercol*(2),
                             1, self.gridParams.nfiltercol )

    def initFilters(self):
        """Initialize widgets to filter the items in the time series"""

        # Label for filters
        label_timeseries  = QtGui.QLabel('Filtering Options')
        label_timeseries.setAlignment(QtCore.Qt.AlignCenter)
        thisfont = label_timeseries.font()
        thisfont.setPointSize(16)
        label_timeseries.setFont(thisfont)

        # Place label widget on grid
        rowoffset = self.gridParams.filtergroup_row0
        self.grid.addWidget( label_timeseries, self.gridParams.optrow0+rowoffset,
                                               self.gridParams.optcol0,
                                               1, self.gridParams.optncol )

        # ---- Group to hold Customer Type check boxes and place on grid
        label_customers  = QtGui.QLabel('Customer Type')
        label_customers.setAlignment(QtCore.Qt.AlignCenter)
        colwidth = 3
        thisrowoffset = 1
        thiscoloffset = 1
        self.grid.addWidget(label_customers, self.gridParams.optrow0+rowoffset+thisrowoffset,
                            self.gridParams.optcol0+thiscoloffset, 1, colwidth)
        self.filterGroup_customer = QtGui.QButtonGroup()
        self.filterGroup_customer.setExclusive(False)
        self.filterGroup_customer.setObjectName('Customer Type')
        types = ['Subscriber', 'Customer']
        buttonlist = []
        counter = 0
        ijs = [[0,0],[1,0]]
        for name,ij in zip(types,ijs):
            thisbutton = QtGui.QCheckBox(name,self)
            thisbutton.setObjectName(name)
            buttonlist.append(thisbutton)
            #buttonlist[counter].clicked.connect(self.updateplot)
            buttonlist[counter].setChecked(True)
            self.filterGroup_customer.addButton(thisbutton)
            self.filterGroup_customer.setId(thisbutton, counter)
            self.grid.addWidget(buttonlist[counter], 
                                self.gridParams.optrow0+rowoffset+thisrowoffset+1+ij[0],
                                self.gridParams.optcol0+ij[1]+thiscoloffset,
                                1, colwidth)
            counter += 1

        # --- Group to hold Region check boxes
        label_region  = QtGui.QLabel('Region')
        label_region.setAlignment(QtCore.Qt.AlignCenter)
        colwidth = 3
        thisrowoffset = 5
        thiscoloffset = 1
        self.grid.addWidget(label_region, self.gridParams.optrow0+rowoffset+thisrowoffset,
                            self.gridParams.optcol0+thiscoloffset, 1, colwidth)
        self.filterGroup_region = QtGui.QButtonGroup()
        self.filterGroup_region.setExclusive(False)
        self.filterGroup_region.setObjectName('Region')
        types = ['San Francisco', 'San Jose', 'Mountain View', 'Redwood City', 'Palo Alto']
        buttonlist = []
        counter = 0
        ijs = [[val,0] for val in range(len(types))]
        for name,ij in zip(types,ijs):
            thisbutton = QtGui.QCheckBox(name,self)
            thisbutton.setObjectName(name)
            buttonlist.append(thisbutton)
            #buttonlist[counter].clicked.connect(self.updateplot)
            buttonlist[counter].setChecked(True)
            self.filterGroup_region.addButton(thisbutton)
            self.filterGroup_region.setId(thisbutton, counter)
            self.grid.addWidget(buttonlist[counter], 
                                self.gridParams.optrow0+rowoffset+thisrowoffset+1+ij[0],
                                self.gridParams.optcol0+ij[1]+thiscoloffset,
                                1, colwidth)
            counter += 1

        # ---- Group to hold Day of Week check boxes 
        label_dayofweek = QtGui.QLabel('Day of Week')
        label_dayofweek.setAlignment(QtCore.Qt.AlignCenter)
        colwidth = 3
        thiscoloffset = 5
        thisrowoffset = 1
        self.grid.addWidget(label_dayofweek, self.gridParams.optrow0+rowoffset+thisrowoffset,
                            self.gridParams.optcol0+thiscoloffset, 1, colwidth)
        self.filterGroup_dayofweek = QtGui.QButtonGroup()
        self.filterGroup_dayofweek.setExclusive(False)
        self.filterGroup_dayofweek.setObjectName('Day of Week')
        types = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        buttonlist = []
        counter = 0
        ijs = [[val,0] for val in range(len(types))]
        for name,ij in zip(types,ijs):
            thisbutton = QtGui.QCheckBox(name,self)
            thisbutton.setObjectName(name)
            buttonlist.append(thisbutton)
            #buttonlist[counter].clicked.connect(self.updateplot)
            buttonlist[counter].setChecked(True)
            self.filterGroup_dayofweek.addButton(thisbutton)
            self.filterGroup_dayofweek.setId(thisbutton, counter)
            self.grid.addWidget(buttonlist[counter], 
                                self.gridParams.optrow0+rowoffset+thisrowoffset+1+ij[0],
                                self.gridParams.optcol0+ij[1]+thiscoloffset,
                                1, colwidth)
            counter += 1

        # ---- Group to hold Hour of Day check boxes 
        label_hourofday = QtGui.QLabel('Hour of Day')
        label_hourofday.setAlignment(QtCore.Qt.AlignCenter)
        colwidth = 1
        thiscoloffset = 9
        thisrowoffset = 1
        self.grid.addWidget(label_hourofday, self.gridParams.optrow0+rowoffset+thisrowoffset,
                            self.gridParams.optcol0+thiscoloffset, 1, colwidth*3)
        self.filterGroup_hourofday = QtGui.QButtonGroup()
        self.filterGroup_hourofday.setExclusive(False)
        self.filterGroup_hourofday.setObjectName('Hour of Day')
        types = [str(val) for val in range(24)]
        buttonlist = []
        counter = 0
        ijs = [val for val in itertools.product(range(8),repeat=2) if val[1]<=2]
        for name,ij in zip(types,ijs):
            thisbutton = QtGui.QCheckBox(name,self)
            thisbutton.setObjectName(name)
            buttonlist.append(thisbutton)
            #buttonlist[counter].clicked.connect(self.updateplot)
            buttonlist[counter].setChecked(True)
            self.filterGroup_hourofday.addButton(thisbutton)
            self.filterGroup_hourofday.setId(thisbutton, counter)
            self.grid.addWidget(buttonlist[counter], 
                                self.gridParams.optrow0+rowoffset+thisrowoffset+1+ij[0],
                                self.gridParams.optcol0+ij[1]+thiscoloffset,
                                1, colwidth)
            counter += 1


        # ---- Group to hold date range calendar objects



    def initButtons(self):
        """Initialize Refresh and Quit buttons at the bottom of the window"""

        # Button to refresh plot after entering text
        self.buttonRefresh = QtGui.QPushButton('Refresh Plot',self)
        self.buttonRefresh.clicked.connect(self.updateplot)

        # Button to reset plot to default values
        self.buttonReset = QtGui.QPushButton('Reset All',self)
        self.buttonReset.clicked.connect(self.resetplot)

        # Button to close window
        self.buttonQuit = QtGui.QPushButton('Quit Window',self)
        self.buttonQuit.clicked.connect(QtCore.QCoreApplication.instance().quit)

        # Place buttons on the grid
        self.grid.addWidget(self.buttonRefresh, 
                            self.gridParams.nrow-1,self.gridParams.ncol-3*self.gridParams.nfiltercol,
                            1, self.gridParams.nfiltercol-1)
        self.grid.addWidget(self.buttonReset, 
                            self.gridParams.nrow-1,self.gridParams.ncol-2*self.gridParams.nfiltercol,
                            1, self.gridParams.nfiltercol-1)
        self.grid.addWidget(self.buttonQuit, 
                            self.gridParams.nrow-1,self.gridParams.ncol-1*self.gridParams.nfiltercol,
                            1, self.gridParams.nfiltercol-1)


    def resetplot(self,state):
        """
        Reset PlotOptions to default values and make the original plot.
        """

        # Get Initial plot options and redraw plot
        self.initOptions()  # Options for selecting what to plot
        self.initPlot()     # After initializing the options


    def updateplot(self,state):
        """Set up plot options based on which buttons are checked.
           Then, call the plottng function (plotbar) with the new options"""

        # Initialize instance of plot options class.
        # These options will replace the existing options.
        newoptions = BabsClasses.PlotOptions()

        # Get new options from the current widget selections
        newoptions.populate(self)

        # Disable some widgets based on currently selected widgets
        self.DisableOptions(newoptions)

        # Call plotting routine, passing the newly constructed instance
        #   of the PlotOptions class.
        self.plotbar(newoptions)


    def plotbar(self,NewOptions):
        """Plots the bar plot.

           INPUT
              self.options  - Options class object that determines what to plot.
                              See class PlotOptions? for more information."""

        # Self.PlotOptions  holds option information of old plot
        # newoptions        holds the option information of the new plot
        # OUTLINE
        #   1. Gather data based on plot options
        #   2. Make the plot
        #   3. Replace self.PlotOptions with NewOptions

        # Get data to plot on the bar plot.

        # Main Type: Timeseries 
        if NewOptions.typeid==0:
            
            # Main Group: Number of Rides
            if NewOptions.barid==0:
                basedata = BabsFunctions.getdata('trip',NewOptions)

                # Create Pandas data frame to hold all information
                tempdf = pd.DataFrame( np.ones(len(basedata['Duration'])), index=basedata.index )
                tempdf = tempdf.resample( NewOptions.dT, how=np.sum ).fillna(0)
                tempdf.columns = ['Number of Rides']

                # Calculate values for each sub-division of the data set
                if NewOptions.division=='Customer Type':
                    types = ['Subscriber','Customer']
                    for ii in range(len(types)):
                        column = pd.DataFrame( np.zeros(len(basedata['Duration'])), index=basedata.index )
                        column.loc[basedata['Subscription Type']==types[ii]] = 1
                        column = column.resample( NewOptions.dT, how=np.sum ).fillna(0)
                        tempdf[types[ii]] = column[0]

                elif NewOptions.division=='Day of Week':
                    types = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                    for ii in range(len(types)):
                        column = pd.DataFrame( np.zeros(len(basedata['Duration'])), index=basedata.index )
                        column.loc[basedata.index.dayofweek==ii] = 1  # Monday
                        column = column.resample( NewOptions.dT, how=np.sum ).fillna(0)
                        tempdf[types[ii]] = column[0]

                elif NewOptions.division=='Hour of Day':
                    types = [str(val) for val in range(24)]
                    for ii in range(len(types)):
                        column = pd.DataFrame( np.zeros(len(basedata['Duration'])), index=basedata.index )
                        column.loc[basedata.index.hour==ii] = 1  # Monday
                        column = column.resample( NewOptions.dT, how=np.sum ).fillna(0)
                        tempdf[types[ii]] = column[0]

                elif NewOptions.division=='Region':
                    types = ['San Francisco','San Jose','Mountain View','Palo Alto','Redwood City']
                    for region in types:
                        column = pd.DataFrame( np.zeros(len(basedata['Duration'])), index=basedata.index )
                        column.loc[basedata['region']==region] = 1  
                        column = column.resample( NewOptions.dT, how=np.sum ).fillna(0)
                        tempdf[region] = column[0]


                # Drop original item in the pandas dataframe
                if NewOptions.division!='None':
                    tempdf.drop('Number of Rides',axis=1,inplace=True)


            # Main Group: Duration of rides
            if NewOptions.barid==1:
                basedata = BabsFunctions.getdata('trip',NewOptions)
                tempdf = basedata[['Duration']]
                tempdf = tempdf.resample( NewOptions.dT, how=np.median ).fillna(0)
                tempdf.columns = ['Duration of Ride']

                # Calculate values for each sub-division of the data set
                if NewOptions.division=='Customer Type':
                    barcolors = []
                    # Add Number of Subscribers to the data frame
                    types = ['Subscriber','Customer']
                    for ii in range(len(types)):
                        column = basedata[['Duration']]
                        column.loc[basedata['Subscription Type']==types[ii]] = 1
                        column = column.resample( NewOptions.dT, how=np.median ).fillna(0)
                        tempdf[types[ii]] = column[0]

                    # Drop total Number from the Data Frame
                    tempdf.drop('Duration of Rides',axis=1,inplace=True)

                #elif NewOptions.division=='Another Division':

                        # do similar things


        # Main Type: Histogram
        elif NewOptions.typeid==1:

            # Number of Rides
            if NewOptions.barid==0:

                # Number of Rides
                if NewOptions.binid==1:

                    # Get column of number of rides in each time period
                    basedata = BabsFunctions.getdata('trip',NewOptions)
                    tempdf = pd.DataFrame( np.ones(len(basedata['Duration'])), index=basedata.index )
                    tempdf = tempdf.resample( NewOptions.dT, how=np.sum ).fillna(0)

                    # Put histogram of rides into a pandas dataframe
                    tempdf.columns = ['Number of Rides']
                    count, divisions = np.histogram(tempdf['Number of Rides'], bins=20)
                    tempdf = pd.DataFrame(count, index=divisions[:-1]+(divisions[1]-divisions[0])/2.)
                    tempdf.index.name = 'Number of Rides'
                    tempdf.columns = ['Number of Occurances']

                    # Add sub-division bars, if indicated
                    if NewOptions.division=='Customer Type':
                        types = ['Subscriber','Customer']
                        for ii in range(len(types)):

                            # Make column of ones for each event and column of ones for each
                            #    event that matches the condition.
                            column = pd.DataFrame( np.ones(len(basedata['Duration'])), index=basedata.index )
                            column.columns = ['ones']
                            column['zeros'] = np.zeros(len(column))
                            column['zeros'].loc[basedata['Subscription Type']==types[ii]] = 1
                            column = column.resample( NewOptions.dT, how=np.sum ).fillna(0)
                        
                            # Calculate fraction of events of this type in the data
                            thistypefrac = BabsFunctions.typefraction(column,divisions)
    
                            # Add the value for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac*tempdf['Number of Occurances']
    
                    # Sub-division by day of the week
                    elif NewOptions.division=='Day of Week':
                        types = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                        for ii in range(len(types)):
                            column = pd.DataFrame( np.ones(len(basedata['Duration'])), index=basedata.index )
                            column.columns = ['ones']
                            column['zeros'] = np.zeros(len(column))
                            column['zeros'].loc[basedata.index.dayofweek==ii] = 1
                            column = column.resample( NewOptions.dT, how=np.sum ).fillna(0)
                        
                            # Calculate fraction of events of this type in the data
                            thistypefrac = BabsFunctions.typefraction(column,divisions)
    
                            # Add the value for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac*tempdf['Number of Occurances']
    
                    # Sub-division by hour of the day
                    elif NewOptions.division=='Hour of Day':
                        types = [str(val) for val in range(24)]
                        for ii in range(len(types)):
    
                            column = pd.DataFrame( np.ones(len(basedata['Duration'])), index=basedata.index )
                            column.columns = ['ones']
                            column['zeros'] = np.zeros(len(column))
                            column['zeros'].loc[basedata.index.hour==ii] = 1
                            column = column.resample( NewOptions.dT, how=np.sum ).fillna(0)
    
                            # Calculate fraction of events of this type in the data
                            thistypefrac = BabsFunctions.typefraction(column,divisions)
    
                            # Add the value for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac*tempdf['Number of Occurances']
    
                    # Sub-division by region
                    elif NewOptions.division=='Region':
                        types = ['San Francisco','San Jose','Mountain View','Palo Alto','Redwood City']
                        for ii in range(len(types)):
    
                            column = pd.DataFrame( np.ones(len(basedata['Duration'])), index=basedata.index )
                            column.columns = ['ones']
                            column['zeros'] = np.zeros(len(column))
                            column['zeros'].loc[basedata['region']==types[ii]] = 1
                            column = column.resample( NewOptions.dT, how=np.sum ).fillna(0)
    
                            # Calculate fraction of events of this type in the data
                            thistypefrac = BabsFunctions.typefraction(column,divisions)
    
                            # Add the value for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac*tempdf['Number of Occurances']
    
                    # Drop original item in the pandas dataframe
                    if NewOptions.division!='None':
                        tempdf.drop('Number of Occurances',axis=1,inplace=True)

                # Day of the week
                elif NewOptions.binid==2:

                    # Get column of number of rides in each time bin
                    basedata = BabsFunctions.getdata('trip', NewOptions)
                    tempdf = pd.DataFrame( np.ones(len(basedata['Duration'])), index=basedata.index )

                    # Group by hour of day
                    tempdf = tempdf.groupby(tempdf.index.dayofweek).sum()
                    tempdf.index.name = 'Number of Rides'
                    tempdf.columns = ['Number of Occurances']
    
                    # Add sub-division bars, if indicated
                    if NewOptions.division=='Customer Type':
                        types = ['Subscriber','Customer']
                        for ii in range(len(types)):
    
                            # Make a new column where 1 marks if the condition of this type is met
                            newtemp = pd.DataFrame( np.zeros(len(basedata['Duration'])), index=basedata.index )
                            newtemp.columns = ['zeros']
                            newtemp['zeros'].loc[basedata['Subscription Type']==types[ii]] = 1
    
                            # Calculate the number of occurances of this type
                            thistypefrac = newtemp.groupby(newtemp.index.dayofweek).sum()
    
                            # Add the values for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac

                    elif NewOptions.division=='Hour of Day':
                        types = [str(val) for val in range(24)]
                        for ii in range(len(types)):
    
                            # Make a new column where 1 marks if the condition of this type is met
                            newtemp = pd.DataFrame( np.zeros(len(basedata['Duration'])), index=basedata.index )
                            newtemp.columns = ['zeros']
                            newtemp['zeros'].loc[basedata.index.hour==ii] = 1
    
                            # Calculate the number of occurances of this type
                            thistypefrac = newtemp.groupby(newtemp.index.dayofweek).sum()
    
                            # Add the values for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac
    
                    elif NewOptions.division=='Region':
                        types = ['San Francisco','San Jose','Mountain View','Palo Alto','Redwood City']
                        for ii in range(len(types)):
    
                            # Make a new column where 1 marks if the condition of this type is met
                            newtemp = pd.DataFrame( np.zeros(len(basedata['Duration'])), index=basedata.index )
                            newtemp.columns = ['zeros']
                            newtemp['zeros'].loc[basedata['region']==types[ii]] = 1
    
                            # Calculate the number of occurances of this type
                            thistypefrac = newtemp.groupby(newtemp.index.dayofweek).sum()
    
                            # Add the values for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac
    
                    # Drop original item in the pandas dataframe
                    if NewOptions.division!='None':
                        tempdf.drop('Number of Occurances',axis=1,inplace=True)

                # Hour of the Day
                elif NewOptions.binid==3:

                    # Get column of number of rides in each time period
                    basedata = BabsFunctions.getdata('trip', NewOptions)
                    tempdf = pd.DataFrame( np.ones(len(basedata['Duration'])), index=basedata.index )

                    # Group by hour of day
                    tempdf = tempdf.groupby(tempdf.index.hour).sum()
                    tempdf.index.name = 'Number of Rides'
                    tempdf.columns = ['Number of Occurances']

                    # Add sub-division bars, if indicated
                    if NewOptions.division=='Customer Type':
                        types = ['Subscriber','Customer']
                        for ii in range(len(types)):
    
                            # Make a new column where 1 marks if the condition of this type is met
                            newtemp = pd.DataFrame( np.zeros(len(basedata['Duration'])), index=basedata.index )
                            newtemp.columns = ['zeros']
                            newtemp['zeros'].loc[basedata['Subscription Type']==types[ii]] = 1
    
                            # Calculate the number of occurances of this type
                            thistypefrac = newtemp.groupby(newtemp.index.hour).sum()
    
                            # Add the values for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac
    
                    elif NewOptions.division=='Day of Week':
                        types = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                        for ii in range(len(types)):
    
                            # Make a new column where 1 marks if the condition of this type is met
                            newtemp = pd.DataFrame( np.zeros(len(basedata['Duration'])), index=basedata.index )
                            newtemp.columns = ['zeros']
                            newtemp['zeros'].loc[basedata.index.dayofweek==ii] = 1
    
                            # Calculate the number of occurances of this type
                            thistypefrac = newtemp.groupby(newtemp.index.hour).sum()
    
                            # Add the values for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac
    
                    elif NewOptions.division=='Region':
                        types = ['San Francisco','San Jose','Mountain View','Palo Alto','Redwood City']
                        for ii in range(len(types)):
    
                            # Make a new column where 1 marks if the condition of this type is met
                            newtemp = pd.DataFrame( np.zeros(len(basedata['Duration'])), index=basedata.index )
                            newtemp.columns = ['zeros']
                            newtemp['zeros'].loc[basedata['region']==types[ii]] = 1
    
                            # Calculate the number of occurances of this type
                            thistypefrac = newtemp.groupby(newtemp.index.hour).sum()
    
                            # Add the values for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac
    
                    # Drop original item in the pandas dataframe
                    if NewOptions.division!='None':
                        tempdf.drop('Number of Occurances',axis=1,inplace=True)

                # Region
                elif NewOptions.binid==4:

                    # Get column of number of rides in each time period
                    basedata = BabsFunctions.getdata('trip', NewOptions)
                    tempdf = pd.DataFrame( np.ones(len(basedata['Duration'])), index=basedata.region )

                    # Group by hour of day
                    tempdf = tempdf.groupby(tempdf.index).sum()
                    tempdf.index.name = 'Region'
                    tempdf.columns = ['Number of Occurances']

                    # Add sub-division bars, if indicated
                    if NewOptions.division=='Customer Type':
                        types = ['Subscriber','Customer']
                        for ii in range(len(types)):

                            # Make a new column where 1 marks if the condition of this type is met
                            newtemp = pd.DataFrame( {'zeros':np.zeros(len(basedata['Duration'])),
                                                     'region':basedata['region']}, index=basedata.index )
                            newtemp['zeros'].loc[basedata['Subscription Type']==types[ii]] = 1

                            # Calculate the number of occurances of this type
                            thistypefrac = newtemp.groupby(newtemp.region).sum()

                            # Add the values for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac

                    elif NewOptions.division=='Day of Week':
                        types = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                        for ii in range(len(types)):
    
                            # Make a new column where 1 marks if the condition of this type is met
                            newtemp = pd.DataFrame( {'zeros':np.zeros(len(basedata['Duration'])),
                                                     'region':basedata['region']}, index=basedata.index )
                            newtemp['zeros'].loc[basedata.index.dayofweek==ii] = 1
    
                            # Calculate the number of occurances of this type
                            thistypefrac = newtemp.groupby(newtemp.region).sum()
    
                            # Add the values for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac
    
                    elif NewOptions.division=='Hour of Day':
                        types = [str(val) for val in range(24)]
                        for ii in range(len(types)):
    
                            # Make a new column where 1 marks if the condition of this type is met
                            newtemp = pd.DataFrame( {'zeros':np.zeros(len(basedata['Duration'])),
                                                     'region':basedata['region']}, index=basedata.index )
                            newtemp['zeros'].loc[basedata.index.hour==ii] = 1
    
                            # Calculate the number of occurances of this type
                            thistypefrac = newtemp.groupby(newtemp.region).sum()
    
                            # Add the values for this type to the dataframe
                            tempdf[types[ii]] = thistypefrac
    
                    # Drop original item in the pandas dataframe
                    if NewOptions.division!='None':
                        tempdf.drop('Number of Occurances',axis=1,inplace=True)
    
                    # Reset index to be numbers for calculating width of plot
                    xticklabels = tempdf.index
                    tempdf.index = range(len(tempdf.index))


            # Duration of Rides
            #elif NewOptions.barid==1:
            #    basedata = BabsFunctions.getdata('trip',NewOptions)
            #    tempdf = basedata[['Duration']]
            #    tempdf.columns = ['Duration of Ride']



        # Create the barplot
        # Calculate width of bars
        # Regularly spaced time series
        if NewOptions.typeid==0: 
            width = 1.0*(tempdf.index[1]-tempdf.index[0]).days

        # Histogram
        else: 
            diffs = [tempdf.index[ind+1] - tempdf.index[ind] for 
                     ind in range(len(tempdf.index)-1)]
            width = 1.0*(min(diffs))
            #width = 1.0*(tempdf.index[1]-tempdf.index[0])

        # Calculate barplot colors
        if NewOptions.division=='None':
            barcolors = ['b']
        elif NewOptions.division=='Customer Type':
            types = ['Subscriber','Customer']
            barcolors = cm.rainbow( np.linspace(0,1,len(types)) )
        elif NewOptions.division=='Day of Week':
            types = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            barcolors = cm.rainbow( np.linspace(0,1,len(types)) )
        elif NewOptions.division=='Hour of Day':
            types = [str(val) for val in range(24)]
            barcolors = cm.hsv( np.linspace(0,1,len(types)) )
        elif NewOptions.division=='Region':
            types = ['San Francisco','San Jose','Mountain View','Redwood City','Palo Alto']
            barcolors = cm.jet( np.linspace(0,1,len(types)) )


        # Create the bars on the bar plot
        bars = []   # list of handles for each bar in barplot
        for ii in range(len(tempdf.columns)):
            # Save previous plot's y-value for base of next plot
            if ii==0: 
                previous = np.zeros(len(tempdf.iloc[:,ii]))

            # Add the bar to the axis. If plotting many (divisions), make sure
            #   to set ax.hold(True) after the first call
            thisbar = self.ax.bar( tempdf.index, tempdf.iloc[:,ii], width,
                                   bottom=previous, color=barcolors[ii] )
            bars.append(thisbar)
            self.ax.hold(True)
            previous = previous + tempdf.iloc[:,ii]


        # Update all other lines to overplot
        if NewOptions.overtype!=[]:

            # Make new axis to plot
            self.ax2.twinx()

            # Add each new plot to the axis
            for name in NewOptions.overtype:

                # Get data.  data = BabsFunctions.getdata('weather')
                data = BabsFunctions.getdata('weather', NewOptions)

                # if name==NewOptions.overtype[0]:
                #     add this info to the axis
                # else:
                #     scale this info the axis and add it

            # Get data.   data = BabsFunctions.getdata('')
            # Make the line.   thisline = plot(x,y)
            # Add lines to this figure


        # Reset ax.hold(False) after placing everything on the plot
        self.ax.hold(False)

        # Make a legend for the figure
        self.plotlegend = self.ax.legend( (bar[0] for bar in bars), (col for col in tempdf.columns) )
        self.plotlegend.draggable()

        # Add titles and labels
        #    Plot title and axis labels
        self.setLabels(NewOptions)

        # Refresh the canvas
        self.canvas.draw()

        # Resent plot options with the new options
        self.PlotOptions = NewOptions



def main():

    app = QtGui.QApplication(sys.argv)
    ex  = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
