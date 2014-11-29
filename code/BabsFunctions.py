########################################################################
#
#        Kevin Wecht                4 November 2014
#
#    Bay Area Bicycle Share (BABS) Open Data Challenge
#
########################################################################
#
#    This file contains auxiliary functions to assist the 
#    analysis of BABS data.
#
#    OUTLINE
#       addregion  - add a column indicating the region of each ride
#                       to the ride data.
#       filterdata - filter rides from the dataset based on options
#                       set in the GUI.
#       getdata    - imports data from .pkl file or csv to pandas dataframe
#       typefraction- calculates the fraction of events that fall into
#                       a set of bins. For dividing histogram bars
#                       by categorical variables.
#
########################################################################

# Import modules required by these functions
import pandas as pd
import numpy as np
import pdb

########################################################################


def addregion(data,name):
    """
    Add column indicating the region to the pandas dataframe
    """

    # If processing trip information, do the following
    if name=="trip":

        # Get Station ID information from file
        try:
            filein = '../data/201402-babs-open-data/station.pkl'
            stationdata = pd.read_pickle(filein)
        
        # If that doesn't work, read the data from csv
        except:
        
            # Get filename to read
            filein = '../data/201402-babs-open-data/201402_station_data.csv'
            
            # Read file using pandas read_csv
            stationdata = pd.read_csv( filein, na_values="?",
                                       parse_dates={'date':['installation']} )
        
        # Add column of region information to a pandas dataframe
        data['region'] = ['None']*len(data)
        stations = stationdata['station_id'].unique()
        for station in stations:
            try:
                data['region'][data['Start Terminal']==station] = stationdata['landmark'][stationdata['station_id']==station].iloc[0]
            except:
                print "No stations in the dataset ", station

    # If processing weather information
    if name=="weather":
        data = data.rename( columns={'zip': 'region'} )
        zipdict = {94107:'San Francisco',94063:'Redwood City',
                   94301:'Palo Alto',94041:'Mountain View',95113:'San Jose'}
        for key,value in zipdict.iteritems():
            data['region'][data['region']==key] = value


    # Return data to calling function
    return data
    


def filterdata(data,NewOptions):
    """
    Filters data from Pandas dataframe (data) based on 
    filtering options read from widgets in NewOptions.
    """

    # Trim Data based on options in the NewOptions.filters list
    for filtername,filtervals in NewOptions.filters.iteritems():

        # For a categorical filter:
        #    1. add a column of zeros to the dataframe
        #    2. place 1 in every row that matches the criteria to filter out
        #    3. trim dataframe; keep columns with a 0 in them
        #    4. Remove column of ones from the dataframe
        #
        # For a min/max value filter:
        #    1. trim dataframe based on values.
        #         ex. data = data[(data.index.hour>=min) & (data.index.hour<=max)]

        # Customer Type: categorical filter
        if filtername=='Customer Type':
            data['ones'] = np.zeros(len(data))
            for ctype in filtervals:
                data['ones'][data['Subscription Type']==ctype] = 1
            data = data[data['ones']==0]
            data.drop('ones',axis=1,inplace=True)

        # Region: categorical filter
        if filtername=='Region':
            data['ones'] = np.zeros(len(data))
            for region in filtervals:
                data['ones'][data['region']==region] = 1
            data = data[data['ones']==0]
            data.drop('ones',axis=1,inplace=True)

        # Day of Week: categorical filter
        if filtername=='Day of Week':
            data['ones'] = np.zeros(len(data))
            for value in filtervals:
                data['ones'][data.index.dayofweek==int(value)] = 1
            data = data[data['ones']==0]
            data.drop('ones',axis=1,inplace=True)

        # Hour of Day: categorical filter
        if filtername=='Hour of Day':
            data['ones'] = np.zeros(len(data))
            for value in filtervals:
                data['ones'][data.index.hour==int(value)] = 1
            data = data[data['ones']==0]
            data.drop('ones',axis=1,inplace=True)

    # Return data to calling function
    return data


def getdata(name,NewOptions):
    """
    Imports data from csv to pandas dataframe.
    Selects columns of interest, sets indices, 
    and generates pandas datetime objects where
    appropriate.

    INPUT - 
       name       - {"rebalancing"|"trip"|"weather"|"station"}
       NewOptions - PlotOptions class object from BabsClasses
                    that contains information on what data to trim.
    """


    # Make sure that "name" is an exceptable value.
    if name not in ["rebalancing","trip","station","weather"]:
        print "Name passed to readcsv is not of an acceptable value."
        print "Name = " + name
        print "Name should be in {'rebalancing'|'trip'|'weather'|'station'}"
        print ""
        print "Returning to calling program with None"
        return None


    # Try to restore pickle. Otherwise, readcsv
    try:
        filein = '../data/201402-babs-open-data/' + name + '.pkl'
        data = pd.read_pickle(filein)

    # If that doesn't work, read the data from csv
    except:

        # Get filename to read
        filein = '../data/201402-babs-open-data/201402_' + name + '_data.csv'
        
        # Read file using pandas read_csv
        if name=="rebalancing":
            data = pd.read_csv( filein, na_values="?",
                                parse_dates={'datetime':['time']} )
        elif name=="trip":
            data = pd.read_csv( filein, na_values="?",
                                parse_dates=['Start Date','End Date'])
            data = data.set_index('Start Date')
        elif name=="station":
            data = pd.read_csv( filein, na_values="?",
                                parse_dates={'date':['installation']} )
        elif name=="weather":
            data = pd.read_csv( filein, na_values="?",
                                parse_dates={'date':['Date']} )
            data = data.set_index('date')

        # Save dataframe as pickle
        fileout = '../data/201402-babs-open-data/' + name + '.pkl'
        data.to_pickle(fileout)

    # Add region indicator to the weather and trip data
    if (name=="trip") | (name=="weather"):
        data = addregion(data,name)

    # Filter data based on input options
    data = filterdata( data, NewOptions )

    # Return dataframe to calling program
    return data


def typefraction(column,divisions):
    """
    Calculates the fraction of events that fall in each
    bin. Successful events are counted in the column 'zeros'.
    Total events are denoted by a 1 in the column 'ones'.
    Divisions contain the edges of each bin.

    This function is used to assist in sub-dividing
    histogram bars by different categorical variables."""

    # Calculate the fraction of events in the "column" dataframe
    #    as defined by sum('zeros') / sum('ones')
    thistypefrac = []
    for dd in range(len(divisions)-1):
        if dd==0:
            thisinfo = column[(column['ones']>=divisions[dd]) & 
                              (column['ones']<=divisions[dd+1])]
        else:
            thisinfo = column[(column['ones']>divisions[dd])  & 
                              (column['ones']<=divisions[dd+1])]
        if len(thisinfo)==0: thistypefrac.append(0)
        else:
            thistypefrac.append( thisinfo['zeros'].sum()/thisinfo['ones'].sum() )

    # Return fraction of occurances to calling program
    return thistypefrac


def get_column( basedata, ii, PlotOptions ):
    """
Retrieves a column of Trip IDs that match a particular condition supplied by
types[ii] and the division name."""

    
    # Select data based on condition of the division type being met
    types = PlotOptions.division_types
    if PlotOptions.division=='Customer Type':
        selection = basedata['Subscription Type']==types[ii]
    elif PlotOptions.division=='Day of Week':
        selection = basedata.index.dayofweek==ii
    elif PlotOptions.division=='Hour of Day':
        selection = basedata.index.hour==ii
    elif PlotOptions.division=='Region':
        selection = basedata['region']==types[ii]

    column = basedata[selection]['Trip ID']

    # If grouping data by region, make sure we have region information
    # by putting region in the column index
    if PlotOptions.binid==4:
        column.index = basedata[selection]['region']


    # Return column of data to calling program
    return column
