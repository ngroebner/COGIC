# Functions for loading case and demographic data
import pandas as pd
from collections import defaultdict 


def createCountyList(df):
    """Adapted from Geeks from Geeks
    https://www.geeksforgeeks.org/python-convert-list-of-tuples-to-dictionary-value-lists/
    """
    statecountytuples = list(set(df.columns.droplevel(-1)))
    res = defaultdict(list)
    for i, j in statecountytuples:
        res[i].append(j)
    return res

#first date for which there is continuous data

# this could be created with the county data below
def loadStateData(t0='2020-03-10'):
    """Loads the current us state-level data on confirmed cases,
    deaths, and recovered from JHU github.

    Returns a dataframe with multiindex columns.
    df[State][Confirmed/Infected/Deaths/Recovered]
    """
    statedata = pd.read_csv('data/usStateData.csv')
    statedata['Infected'] = (
        statedata['Confirmed']
        - (statedata['Recovered'] + statedata['Deaths'])
    )
    statedata = statedata.pivot(
        index='Last_Update',
        columns='Province/State',
        values=['Confirmed', 'Infected', 'Deaths', 'Recovered']
    ).interpolate().fillna(0)
    statedata = statedata.swaplevel(-2,-1, axis=1)
    return statedata.loc[t0:]

def loadCountyData(t0='2020-03-10'):
    """Loads the current us state-level data on confirmed cases,
    deaths, and recovered from New York Times github.

    Returns a dataframe with multiindex columns.
    df[State][Confirmed/Infected/Deaths/Recovered]
    """
    df = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv')
    df.columns = ['date','County','State','fips','Confirmed','Deaths']
    return df.pivot_table(
        index='date',
        columns=['State','County'],
        values=['Confirmed','Deaths']
    ).fillna(0).swaplevel(0,-1,axis=1).swaplevel(0,-2,axis=1).loc[t0:]
