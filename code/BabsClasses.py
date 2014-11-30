########################################################################
#
#        Kevin Wecht                4 November 2014
#
#    Bay Area Bicycle Share (BABS) Open Data Challenge
#
########################################################################
#
#    This file contains user defined classes to assist the 
#    analysis of BABS data.
#
#    OUTLINE
#       PlotOptions - holds information from widgets to determine
#                     what to show in the plot window.
#       GridParams  - holds information about the grid layout of the GUI
#
########################################################################

# Import modules required by these functions
import pandas as pd
import pdb

########################################################################



# Set up grid on which to place widgets in the QtGui Window
class GridParams:
    """Class to hold grid parameters for the QtGui Window."""

    # Set default values for grid size
    def __init__(self):

        # Number of cells in each direction
        self.nrow = 48
        self.ncol = 72

        # Spacing between cells
        self.spacing = 2

        # Area occupied by matplotlib plot.
        # Leave 4 rows and 12 cols to the around the main plot
        self.plotnrow = self.nrow - 8
        self.plotncol = self.ncol - 12
        self.plotrow0 = 0   # Place 
        self.plotcol0 = 0
        self.plotrow1 = self.plotnrow + self.plotrow0 - 1  # -1 to be inclusive range
        self.plotcol1 = self.plotncol + self.plotcol0 - 1

        # Area occupied by plot options
        self.optnrow = self.nrow - self.plotnrow
        self.optncol = self.ncol - self.plotncol
        self.optrow0 = 0
        self.optcol0 = self.plotcol1 + 1
        self.optrow1 = self.optrow0 + self.optnrow - 1
        self.optcol1 = self.optcol0 + self.optncol - 1

        # Number of filter options to squeeze into each column
        self.nfiltercol = 3

        # Row offsets of each sub-section in the options section
        self.maintype_row0 = 0
        self.maingroup_row0 = 1
        self.timegroup_row0 = 3
        self.bingroup_row0 = 3
        self.divisiongroup_row0 = 7
        self.overgroup_row0 = 12
        self.filtergroup_row0 = 17

# Define class to hold parameters that determine what to plot in the main widget.
class PlotOptions:
    """Class to hold info determining what to plot in the main window."""

    # Initialize some options to plot number of rides per week
    def __init__(self):

        # Integer indicating the type of information to show
        #   {0 'timeseries'|1 'histogram'}
        self.typeid = 0

        # Integer indicating the value to plot
        #   {0 'nrides'|1 'duration'|2 'distance'}
        self.barid = 0

        # Integer indicating the way to bin the data
        #   {0 'Time (other)'|1 'Number of Rides'|2 'Day of Week'|3 'Hour of Day'|4 'Region'}
        self.binid = 0

        # String that indicates which variable along which to 
        #   divide the main variable plotted 
        # For example, we can divide each bar in the plot into two segments:
        #     annual customers and recent (casual) customers.
        #   {options here}
        self.division = ''
        self.division_types = []  # {['Subscriber','Customer'], ['Monday','Tuesday',...], ...}

        # Time over which to average data.
        # Used when plotting timeseries and 
        #   histogram (optional) for daily or weekly average values (ex. daily mean rides)
        #   Must be a whole number of days
        self.dT = '7D'   # Default weekly average. Monthly = 30, daily = 1

        # Plot dimensions. If empty, use default dimensions in the data.
        self.xlim = []
        self.ylim = []

        # Set additional values to plot over the bars.
        #    {weather('temp', 'precip', 'wind') | 'nrides' | 'duration'}
        self.overtype = []

        # Filter options
        #    {date range, time of day, day of week, region, weather, station ID}
        self.filters = {}

        # Populate plot options with the selections in the GUI window
        #    named MainWindow.
        # This overides the default options selected above
        #self.populate(MainWindow)


    # Method to fill options from currently selected widgets in the gui
    def populate(self,MainWindow):
        """Populate plot options using the selections in the GUI window.
        
           INPUT
              MainWindow  - Instance of a class that defines our main GUI window"""

        # 1. From drop down list indicating plot type
        self.typeid = MainWindow.mainType.currentIndex()

        # 2. From drop down list indicating which variable to plot in bars
        self.barid = MainWindow.mainGroup.currentIndex()

        # 3. From drop down list indicating how to bin the data
        self.binid = MainWindow.binGroup.currentIndex()

        # 3. From text entry telling by what time step to bin data
        number = int(str(MainWindow.timeText.text()))
        unit = str(MainWindow.timeGroup.currentText())[0]
        self.dT = str(number)+unit

        # 2. From radio buttons indicating by which variable we should
        #    divide the bars.
        self.division = str(MainWindow.divisionGroup.checkedButton().objectName())
        if self.division=='Customer Type':
            self.division_types=['Subscriber','Customer']
        elif self.division=='Hour of Day':
            self.division_types = [str(val) for val in range(24)]
        elif self.division=='Day of Week':
            self.division_types = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        elif self.division=='Region':
            self.division_types = ['San Francisco','San Jose','Mountain View','Redwood City','Palo Alto']

        # 3. From check buttons indicating what to overplot
        self.overtype = []
        for button in MainWindow.overGroup.buttons():
            if button.isChecked():
                self.overtype.append(str(button.text()))

        # 4. From filter check boxes indicating what to trim from data
        #    Store filter information in dictionary in which the keys are
        #       'Customer Type', 'Region', 'Day of Week', 'Hour of Day'
        self.filters = {}
        filtergroups = [MainWindow.filterGroup_customer,
                        MainWindow.filterGroup_region,
                        MainWindow.filterGroup_dayofweek,
                        MainWindow.filterGroup_hourofday]
        for group in filtergroups:
            groupname = str(group.objectName())
            unchecked = []
            for button in group.buttons():
                if not button.isChecked():
                    if groupname=="Day of Week":
                        unchecked.append(str(group.id(button)))
                    else:
                        unchecked.append(str(button.text()))
            if unchecked!=[]:
                self.filters[groupname] = unchecked

