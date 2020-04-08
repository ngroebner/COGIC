# populationModels.py

"""
Things necessary to deal with population stuff.
E.g, conversion between census and CDC age categories,
"""

import pandas as pd
import numpy as np

def loadUSPopulation():
    return pd.read_csv('data/us_population-2019.csv').set_index('State')

def loadUSCountyPopStructure():
    return pd.read_pickle('data/us_county_population_byage-2018.pkl')

def getCountyCensusPop(county):
    """Read the census data for total population by county,
    and return a series containing population by age ranges
    in 5 year increments
    """
    censuspop = pd.read_csv('data/mn_population_struture2018_total.csv')
    countypop = censuspop[censuspop['County']==county].drop(['County'], axis=1).T
    countypop.columns = ['Population']
    countypop = countypop['Population']
    countypop.index = [int(x) for x in countypop.index]
    return countypop

def census2cdc(series):
    """Converts census population data, which is given in terms of 5 year age ranges,
    to age ranges from the CDC paper on COVID-19 mortality
    """
    cdc = pd.Series([
        series[[0,5,10,15]].sum(),
        series[[20,25,30,35,40]].sum(),
        series[[45,50]].sum(),
        series[[55,60]].sum(),
        series[[65,70]].sum(),
        series[[75,80]].sum(),
        series[85]]
    )
    cdc.index = [0,20,45,55,65,75,85]
    return cdc

def census2verity(series):
    """Converts census population data, which is given in terms of 5 year age ranges,
    to age ranges from the Verity paper on COVID-19 mortality and hospitalization.
    https://www.medrxiv.org/content/10.1101/2020.03.09.20033357v1.full.pdf
    """
    verity = pd.Series([
        series[[0,5]].sum(),
        series[[10,15]].sum(),
        series[[20,25]].sum(),
        series[[30,35]].sum(),
        series[[40,45]].sum(),
        series[[50,55]].sum(),
        series[[60,65]].sum(),
        series[[70,75]].sum(),
        series[[80,85]].sum()
        ])
    verity.index = [0,10,20,30,40,50,60,70,80]
    return verity

def buildUSCountyAgeStructure():
    """Build population by age file for counties 
    by state
    Population profiles are access by
    df[state][county]
    """
    df = pd.read_csv('data/county_census_population_byage.csv',
             encoding='latin-1').drop(['Id','Id2'], axis=1)
    cols2018 = ['State','County'] + [
        x for x in df.columns if ('2018sex0' in x) and ('sex' in x)]
    df = df[cols2018]
    df.columns = [x.replace('est72018sex0_age','') for x in df.columns]
    df['County'] = df.County.apply(lambda x: x.replace(' County','').strip())
    df = df[['State', 'County', '0to4', '5to9', '10to14', '15to19', '20to24', '25to29',
       '30to34', '35to39', '40to44', '45to49', '50to54', '55to59', '60to64',
       '65to69', '70to74', '75to79', '80to84', '85plus']]
    df.columns = ['State', 'County'] + [x for x in np.arange(0, 90, 5)]
    df = df.set_index(['State','County']).T
    return df