
import pandas as pd
import numpy as np
import json
from github import Github
from io import BytesIO


def fitExponential(x,y):
    logy = np.log(y)
    logy[logy == -np.inf] = 0
    try:
        A, B = np.polyfit(x, logy, 1)
    except:
            B=0
    return B

def calcStateHeat(df):
    """
    Calculate the exponential growth constant for case growth.
    """
    heat = []
    cases = []
    states = df.columns
    for state in states:
        y = df[state].values
        x = np.arange(len(y))+1
        heat.append(fitExponential(x,y))
        cases.append(df[state][-1])
    return pd.DataFrame(index=states, data={'Heat':heat, 'Cases':cases}).sort_values('Heat', ascending=False)

def addTotalCases(df):
    """Add a total cases row to dataframe
    """
    total = pd.DataFrame(df.sum(axis=0)).T
    total.index = ['Total']
    df = df.append(total)
    return df

def calcR0(gamma, B):
    return 1 + B/gamma # i need to figure this out better

def unserialize(results):
    results = json.loads(results)
    results['data'] = json.loads(results['data'])
    results['data'] = pd.Series(results['data'])
    return results

def getCountyData():
    g = Github('groe0029@umn.edu','jyntej-3zYtku-juwsok')

    repo = g.get_repo("CSSEGISandData/COVID-19")

    dataframes = []
    for file in repo.get_contents('csse_covid_19_data/csse_covid_19_daily_reports'):
        if file.name.split('.')[-1]=='csv':
            df = pd.read_csv(BytesIO(file.decoded_content))
            dataframes.append(df)

    for i,df in enumerate(dataframes):
        if 'Country_Region' in df.columns:
            dataframes[i]['Country/Region'] = df['Country_Region']
        if 'Province_State' in df.columns:
            dataframes[i]['Province/State'] = df['Province_State']
        if 'Last Update' in df.columns:
            dataframes[i]['Last_Update'] = df['Last Update']

    data = pd.concat(dataframes).fillna(0)
    data = data.drop(['Country_Region','Province_State', 'Last Update','Combined_Key',
                    'FIPS','Active'],axis=1)
    data['Last_Update'] = pd.to_datetime(data['Last_Update']).dt.normalize()

    countydata = data[data['Country/Region']=='US']
    countydata = countydata[[True if ',' not in str(x) else False for x in countydata['Province/State'].values]]
    #usdata = usdata.groupby(['Province/State','Last_Update']).sum()

    return countydata

def getandsaveCountyData():
    countydata = getCountyData()
    countydata.to_csv('data/countydata.csv')

