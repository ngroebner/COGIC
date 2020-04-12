# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from datetime import date, timedelta, datetime
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from  util import *
from SIRModels import discreteSIR, continuousSIR, estimate_beta, doubling_time
from loadCaseData import (
    loadStateData,
    loadCountyData,
    createCountyList
)

from populationModels import census2cdc, loadUSPopulation
from hospCensusModels import HospitalCensus

createcensus = HospitalCensus()

theme = dbc.themes.FLATLY
mathjax = 'https://cdnjs.cloudflare.com/ajax/libcds/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
#app.scripts.append_script({ 'external_url' : mathjax })

external_stylesheets = [theme, mathjax]

graph_height = '400'

if theme==dbc.themes.DARKLY:
    plot_bgcolor = 'rgb(45, 45, 45)'
    paper_bgcolor = 'rgb(45, 45, 45)'
    font_color = 'rgb(180, 180, 180)'
    line_color = 'rgb(80, 150, 220)'
else:
    paper_bgcolor = plot_bgcolor = 'rgb(255, 255, 255)'
    line_color = 'rgb(80, 150, 220)'
    font_color = 'black'


# Load data
#######################################################################

statedata = loadStateData()
# list of states
states = statedata.columns.get_level_values(0)
t_tot = len(statedata.index)


uscountydata = loadCountyData()
# list of counties
# uscountylist[State] - > list of counties

uscountylist = createCountyList(uscountydata)

us_population = loadUSPopulation()

controls = [
    dbc.Row([
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('State'),
                    dcc.Dropdown(
                        options = [{
                            'label':state, 'value':state
                            } for state in states],
                        value = 'Minnesota',
                        id = 'state-dropdown'
                    )
                ]
            ), md=12
        )
    ]),
    dbc.Row([
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('County'),
                    dcc.Dropdown(
                            value = 'Brown',
                            id = 'county-dropdown'
                    )
                ]
            ), md=12
        )
    ]),
    dbc.Row(
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Days to project'),
                    dbc.Input(
                        id = 'tsteps',
                        type = 'number',
                        value = 200
                    )
                ]
            ), md=12
        )
    ),
    dbc.Row([
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Percentage Asymptomatic/Untested'),
                    dcc.Slider(
                        min = 0.0,
                        max = 1,
                        step = 0.05,
                        marks = {i:str(int(100*i))+'%' for i in np.arange(0.0, 1.1, 0.2)},
                        value = 0.5,
                        id = 'silent-slider'
                    )
                ]
            ), md=12
        )
    ]),
    dbc.Row(
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Hospital LOS - days'),
                    dbc.Input(
                        id = 'hosp_LOS',
                        type = 'number',
                        value = 7
                    )
                ]
            ), md=12
        )
    ),
    dbc.Row(
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('ICU LOS - days'),
                    dbc.Input(
                        id = 'ICU_LOS',
                        type = 'number',
                        value = 9
                    )
                ]
            ), md=12
        )
    ),
    dbc.Row(dbc.Col(html.Hr('Hospitalization rate'), md=12)),
    dbc.Row(
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Hospitalization and fatality rate data'),
                    dcc.RadioItems(
                        options=[
                            {'label':'Verity, et al. MedrXiv preprint', 'value':'Verity'},
                            {'label': 'CDC MMWR 3/26/20            .', 'value':'CDC'},
                            {'label': 'Custom (below)', 'value':'Custom'},
                        ],
                        value='Verity',
                        style={'display': 'block'},
                        id = 'hospmodel'
                    )
                ]
            ),md=12
        )
    ),
    dbc.Row(
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Hospitalization rate'),
                    dcc.Slider(
                        min = 0.01,
                        max = 0.1,
                        step = 0.005,
                        marks = {i:str(int(100*i))+'%' for i in np.arange(0, 0.11, 0.01)},
                        value = 0.025,
                        id = 'hospitalizationrate-slider'
                    ),
                ]
            ), md=12
        )
    ),
    dbc.Row(
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('ICU rate'),
                    dcc.Slider(
                        min = 0.00,
                        max = 0.05,
                        step = 0.001,
                        marks = {i:str(int(100*i))+'%' for i in np.arange(0, 0.06, 0.01)},
                        value = 0.01,
                        id = 'icurate-slider'
                    )
                ]
            ), md=12
        )
    ),
    dbc.Row(
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Death Rate'),
                    dcc.Slider(
                        id = 'deathrate-slider',
                        min = 0.001,
                        max = 0.03,
                        step = 0.001,
                        marks = {
                            0.001: '0.1%',
                            0.005: '0.5%',
                            0.01: '1.0%',
                            0.015: '1.5%',
                            0.02: '2.0%',
                            0.025: '2.5%',
                            0.03: '3.0%',
                        },
                        value = 0.005
                    )
                ]
            )
        )
    ),
]

basetext = html.Div([
    html.P([
        'Code for this page is available at ',
        html.A('Github.', href='https://github.com/ngroebner/COGIC'),
    ]),
    dcc.Markdown("""Case data are taken from the [Johns Hopkins 
        University Center for Systems Science and Engineering.]
         (https://github.com/CSSEGISandData/COVID-19)"""),
    html.P('Demographic data is from 2018 US Census estimates.'),
    dcc.Markdown('&copy; Nate Groebner, 2020'),
    html.P('Code GPL-3.0')
    ]
)


modeltext = html.Div([
    dcc.Markdown("""

        Please note all calculations are illustrative only, and should not be used for planning purposes.

        Estimated cases are calculated according to a
        **Susceptible-Infected-Removed (SIR)** continuous, deterministic epidemic model.

        The model generally follows the methodology of the 
        [CHIME model from UPenn](https://code-for-philly.gitbook.io/chime/). 
        This model was developed for estimating hospital resource utilization on a refgional 
        level. It estimates the epi curve using the SIR equations with a fixed gamma (1/14), 
        and calculates beta via the estimated doubling time of the infection in the area.
        In Chime, this doubling time is an adjustable parameter. 

        The current model makes the following modifications to CHIME:

        * The models are US state and county specific
        * The beta parameter for the SIR model is calculated from the 7-day averaged
        observed doubling time.
        * 2018 US population estimates at the state and county levels are used for epidemic curve modeling
        * Hospital census data are calculated based on one of several methods:
            * Adjustable parameters as in CHIME
            * Observed hospitalization rates from (1) and (2) below. If one of these is applied, 
            county and state-level population age distributions are used along with the age-specific 
            hospitalization and death rates from the studies.

        References:

        (1) [Verity, et al, preprint, Estimates of the severity of COVID-19 disease]
        (https://www.medrxiv.org/content/10.1101/2020.03.09.20033357v1)

        (2) [CDC MMWR, 3-26-2020, Severe Outcomes Among Patients with Coronavirus 
        Disease 2019 (COVID-19) — United States, February 12–March 16, 2020]
        (https://www.cdc.gov/mmwr/volumes/69/wr/mm6912e2.htm)

        """),
    ]
)

"""
        dcc.Markdown('''

            (Insert SIR equations)

            Gamma is assumed to be 1/14. Beta is calculated from the doubling time as in the CHIME model (1),
            but fit to real-world state-level data. Instantaneous doubling time is calculated from actual per-day 
            case data, and this quantity is averaged over one week.

            (Insert equation for beta here.)

            This assumption is valid for early in the epidemic, where the number of susceptible patients >>
            than number of infected patients (show math here.)
            '''
        )
"""

censusgraph = [dbc.Row(
            [
                dbc.Col(controls, md=3),
                dbc.Col(
                    [
                        dbc.Row(dbc.Col(dcc.Graph(id='countysir-graph'))),
                        dbc.Row(dbc.Col(dcc.Graph(id='countymodel-graph'))),
                        dbc.Row(dbc.Col(dcc.Graph(id='countyadmissions-graph'))),
                        dbc.Row(dbc.Col(html.Div(id='countymodel-text'))),
                        dbc.Row(dbc.Col(dcc.Graph(id='countydeath-graph'))),
                        dbc.Row(dbc.Col(dcc.Graph(id='statesir-graph'))),
                        dbc.Row(dbc.Col(dcc.Graph(id='statemodel-graph'))),
                        dbc.Row(dbc.Col(dcc.Graph(id='stateadmissions-graph'))),
                        dbc.Row(dbc.Col(html.Div(id='statemodel-text'))),
                        dbc.Row(dbc.Col(dcc.Graph(id='statedeath-graph'))),
                        dbc.Col(modeltext),
                        dbc.Col(basetext)
                    ], md=9
                ),
            ]
        ),
    ]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True
app.title = "COGIC"
application = app.server


app.layout = dbc.Container(
    [
        html.H2('COVID-19 Geographic Impact Calculator (COGIC)'),
        html.Hr(),
        html.Div(censusgraph)
    ],
    fluid=True
)

@app.callback(
    Output('county-dropdown', 'options'),
    [Input('state-dropdown', 'value')]
)
def countrydropdownoptions(state):
    return [
        {'label':county, 'value':county}
        for county in sorted(uscountylist[state])
    ]

def sirgraph(state, county,
            silent,tsteps):
    data, popstructure, N = createcensus.createPopulation(state, county, uscountydata, None)

    statedata = data['state']
    county_data = data['county'] #this may actually also be whole state data
    known_infected = county_data['Confirmed'].values[-7:]
    estimated_infected = known_infected/(1-silent)
    infected_for_beta = statedata['Confirmed'].values[-7:]
    #infected_for_beta = county_data['Confirmed'].values[-7:]

    #df, popstructure = df['county'] * susceptible, popstructure['county'] * susceptible

    I0 = estimated_infected[-1] #current cases as initial condition
    t = np.arange(tsteps)
    dates = [(date.today() + timedelta(int(i))).strftime('%m/%d') for i in t]
    pastdates = pd.to_datetime(county_data.index[-7:]).strftime('%m/%d')

    gamma = 1./14
    beta = estimate_beta(infected_for_beta, gamma)
    Td = doubling_time(infected_for_beta).mean()

    sol = continuousSIR(beta, gamma, N, I0, t)
    projected_infected = sol['I']

    knowntrace = [
        {
            'x': pastdates,
            'y': known_infected,
                'mode':'line',
                'opacity':0.7,
                'line':{
                    'width': 4,
                    'color': 'black',
                    'opacity':0.9
                    },
                'id':'Known Infected',
                'name':'Known Infected',
                'showlegend': True,
        }
    ]
    SIR = [
        {
            'x': dates,
            'y': y,
                'mode':'line',
                'opacity':0.7,
                'line':{
                    'width': 4,
                    #'color': 'blue' if i==1 else 'green',
                    'opacity':0.9
                    },
                'id':{0:'S', 1:'I', 2:'R'}[i],
                'name':{0:'S', 1:'I', 2:'R'}[i],
                'showlegend': True,
        } for i,y in enumerate([sol[c] for c in ['S','I','R']])
    ]

    I = [
        {
            'x': dates,
            'y': sol['I'],
                'mode':'line',
                'opacity':0.7,
                'line':{
                    'width': 4,
                    'color': 'blue',
                    'opacity':0.9
                    },
                'id':'Confirmed',
                'name':'Estimated Infected',
                'showlegend': True,
        }
    ]

    Inew = [
        {
            'x': dates,
            'y': sol['Inew'],
                'mode':'line',
                'opacity':0.7,
                'line':{
                    'width': 4,
                    'color': 'green',
                    'opacity':0.9
                    },
                'id':'Confirmed',
                'name':'New Infections',
                'showlegend': True,
        }
    ]

    figure = {
        'data': knowntrace + Inew,
        'layout': {
            'xaxis': {'title':'Date'},
            'yaxis': {
                #'title': 'Patients',
                'type':'linear'
                },
            'hovermode':'closest',
            'title':{
                'text': (
                    state if county=='All' else (county + ' County')
                    ) + ' SIR model' + ', Current Td: {:0.1f}'.format(Td) + ' days'
                },
            'margin':{'l':75, 'r':40, 'b':120, 't':40},
            'hoveron':'points+fills',
            'mode':'lines',
            'marker':{
                'size': 15,
                'line': {'width': 0.5, 'color': 'blue'}
            },
            'legend':{
                'xanchor': 'center',
                'x': 0.5,
                'y':-0.3,
                'orientation': 'h'
                },
            'legend_orientation': 'h',
            'height': graph_height,
            "plot_bgcolor": plot_bgcolor,
            'paper_bgcolor': paper_bgcolor,
            'font':{'color': font_color}
        }
    }
    return figure

def censusgraph(state, county,
            silent, hosprate, icurate, deathrate,
            hosp_LOS, ICU_LOS, tsteps, title, model):
    data, popstructure, N = createcensus.createPopulation(state, county, uscountydata, model)

    statedata = data['state']
    county_data = data['county'] #this may actually also be whole state data
    known_infected = county_data['Confirmed'].values[-7:]
    estimated_infected = known_infected/(1-silent)
    infected_for_beta = statedata['Confirmed'].values[-7:]
    #infected_for_beta = county_data['Confirmed'].values[-7:]

    I0 = estimated_infected[-1] #current cases as initial condition

    t = np.arange(tsteps)
    dates = [(date.today() + timedelta(int(i))).strftime('%m/%d') for i in t]
    pastdates = pd.to_datetime(county_data.index).strftime('%m/%d')

    gamma = 1./14
    beta = estimate_beta(infected_for_beta, gamma)

    sol = continuousSIR(beta, gamma, N, I0, t)
    projected_infected = sol['I']

    admissionrates = createcensus.calcAdmissionRates(
            popstructure,
            hosprate,
            icurate,
            model
            )

    LOS = createcensus.calcLOS(hosp_LOS, ICU_LOS, model)

    census = createcensus.calcCensus(
        incidence = sol['Inew'],
        admissionrates = admissionrates,
        LOS = LOS
    )

    admissions = dict()
    for idx in admissionrates.index:
        admissions[idx] = np.round(sol['Inew'] * admissionrates.loc[idx])

    censustraces = [
        {
            'x': dates,
            'y': census[col],
            'mode':'line',
            'opacity':0.7,
            'line':{
                'color': 'orange' if 'Hospit' in col else 'red',
                'width': 4,
                'opacity':0.5
                },
                'fill': 'tonexty' if 'high' in col else None,
            'id':col + ' Census',
            'name':col + ' Census',
            'showlegend': True,
        }
        for col in census.columns
    ]

    figure = {
        'data': censustraces,
        'layout': {
            'xaxis': {'title':'Date'},
            'yaxis': {
                'title': 'Patients',
                'type':'linear'
                },
            'hovermode':'closest',
            'title':{
                'text': (state if county=='All' else (county + ' County')) + ' - Hospital Census'
                },
            'margin':{'l':75, 'r':40, 'b':120, 't':40},
            'hoveron':'points+fills',
            'mode':'lines',
            'marker':{
                'size': 15,
                'line': {'width': 0.5, 'color': 'blue'}
            },
            'legend':{
                'xanchor': 'center',
                'x': 0.5,
                'y':-0.3,
                'orientation': 'h'
                },
            'legend_orientation': 'h',
            'height': graph_height,
            "plot_bgcolor": plot_bgcolor,
            'paper_bgcolor': paper_bgcolor,
            'font':{'color': font_color}
        }
    }
    return figure

def admissionsgraph(state, county,
            silent, hosprate, icurate, deathrate,
            hosp_LOS, ICU_LOS, tsteps, title, model):
    data, popstructure, N = createcensus.createPopulation(state, county, uscountydata, model)

    statedata = data['state']
    county_data = data['county'] #this may actually also be whole state data
    known_infected = county_data['Confirmed'].values[-7:]
    estimated_infected = known_infected/(1-silent)
    infected_for_beta = statedata['Confirmed'].values[-7:]
    #infected_for_beta = county_data['Confirmed'].values[-7:]

    #df, popstructure = df['county'] * susceptible, popstructure['county'] * susceptible

    I0 = estimated_infected[-1] #current cases as initial condition

    t = np.arange(tsteps)
    dates = [(date.today() + timedelta(int(i))).strftime('%m/%d') for i in t]
    pastdates = pd.to_datetime(county_data.index).strftime('%m/%d')

    gamma = 1./14
    beta = estimate_beta(infected_for_beta, gamma)

    sol = continuousSIR(beta, gamma, N, I0, t)
    projected_infected = sol['I']

    admissionrates = createcensus.calcAdmissionRates(
            popstructure,
            hosprate,
            icurate,
            model
            )

    admissions = dict()
    for idx in admissionrates.index:
        admissions[idx] = np.round(sol['Inew'] * admissionrates.loc[idx])

    admissionstraces = [
        {
            'x': dates,
            'y': admissions[dispo],
            'type':'line',
            'opacity':0.7,
            'line':{
                'width': 4,
                'opacity':0.5,
                'color': 'orange' if 'Hospit' in dispo else 'red',
                },
            'id':dispo + ' per day',
            'name':dispo + ' per day',
            'showlegend': False,
            'fill': 'tonexty' if 'high' in dispo else None,
        }
        for dispo in admissions.keys()
    ]
    knowntrace = [
        {
            'x': pastdates,
            'y': known_infected,
                'mode':'line',
                'opacity':0.7,
                'line':{
                    'width': 4,
                    'color': 'black',
                    'opacity':0.9
                    },
                'id':'Known Infected',
                'name':'Known Infected',
                'showlegend': True,
        }
    ]
    Inew = [
        {
            'x': dates,
            'y': sol['Inew'],
                'mode':'line',
                'opacity':0.7,
                'line':{
                    'width': 4,
                    'color': 'green',
                    'opacity':0.9
                    },
                'id':'Confirmed',
                'name':'New Infections',
                'showlegend': True,
        }
    ]

    figure = {
        'data': admissionstraces,
        'layout': {
            'xaxis': {'title':'Date'},
            'yaxis': {
                'title': 'Patients',
                'type':'linear'
                },
            'hovermode':'closest',
            'title':{
                'text': 'Admissions'
                },
            'margin':{'l':75, 'r':40, 'b':120, 't':40},
            'hoveron':'points+fills',
            'mode':'lines',
            'marker':{
                'size': 15,
                'line': {'width': 0.5, 'color': 'blue'}
            },
            'height': str(2*int(graph_height)/3),
            "plot_bgcolor": plot_bgcolor,
            'paper_bgcolor': paper_bgcolor,
            'font':{'color': font_color}
        }
    }
    return figure

def deathgraph(state, county,
            silent, deathrate,
            tsteps, model):
    data, popstructure, N = createcensus.createPopulation(state, county, uscountydata, model)

    statedata = data['state']
    county_data = data['county'] #this may actually also be whole state data
    known_infected = county_data['Confirmed'].values[-7:]
    estimated_infected = known_infected/(1-silent)
    infected_for_beta = statedata['Confirmed'].values[-7:]
    #infected_for_beta = county_data['Confirmed'].values[-7:]

    #df, popstructure = df['county'] * susceptible, popstructure['county'] * susceptible

    I0 = estimated_infected[-1] #current cases as initial condition

    t = np.arange(tsteps)
    dates = [(date.today() + timedelta(int(i))).strftime('%m/%d') for i in t]

    gamma = 1./14
    beta = estimate_beta(infected_for_beta, gamma)

    sol = continuousSIR(beta, gamma, N, I0, t)

    deathrates = createcensus.calcDeathRates(deathrate, popstructure, model)

    deaths = dict()
    deathsperday = dict()
    if model==None:
        deaths['Deaths'] = np.round(deathrates * sol['R'])
        deathsperday['Deaths per day'] = np.round(np.gradient(deaths['Deaths']))

    else:
        for idx in deathrates.index:
            deaths[idx] = np.round(sol['R'] * deathrates.loc[idx])
        for key in deaths.keys():
            deathsperday[idx] = np.round(np.gradient(deaths[key]))

    deathtrace = [
        {
            'x': dates,
            'y': val,
            'mode':'line',
            'opacity':0.7,
            'line':{
                'color': 'orange',
                'width': 4,
                'opacity':0.5
                },
            'id':key,
            'name':key,
            'showlegend': True,
            'fill': 'tonexty' if 'high' in key else None,
        } for key, val in deaths.items()
    ]

    deathratetrace = [
        {
            'x': dates,
            'y': val,
            'type':'bar',
            'opacity':0.7,
            'color': 'red',
            'bar':{
                'width': 4,
                'opacity':0.5
                },
            'id': key,
            'name':key,
            'showlegend': True,
        } for key, val in deathsperday.items()
    ]

    figure = {
        'data': deathtrace + deathratetrace,
        'layout': {
            'xaxis': {'title':'Date'},
            'yaxis': {
                'title': 'Patients',
                'type':'linear'
                },
            'hovermode':'closest',
            'title':{
                'text': 'Deaths'
                },
            'margin':{'l':75, 'r':40, 'b':120, 't':40},
            'hoveron':'points+fills',
            'mode':'lines',
            'marker':{
                'size': 15,
                'line': {'width': 0.5, 'color': 'blue'}
            },
            'legend': { 
                'xanchor': 'center', 
                'x': 0.5, 
                'y':-0.3, 
                'orientation': 'h'
                },
            'height': graph_height,
            "plot_bgcolor": plot_bgcolor,
            'paper_bgcolor': paper_bgcolor,
            'font':{'color': font_color}
        }
    }
    return figure

@app.callback(
    Output(component_id='countysir-graph', component_property='figure'),
    [
        Input('state-dropdown', 'value'),
        Input('county-dropdown', 'value'),
        Input('silent-slider', 'value'),
        Input('tsteps', 'value')
    ]
)
def countysirgraph(state, county,
            silent,tsteps):
    return sirgraph(state, county, silent, tsteps)

@app.callback(
    Output(component_id='statesir-graph', component_property='figure'),
    [
        Input('state-dropdown', 'value'),
        Input('county-dropdown', 'value'),
        Input('silent-slider', 'value'),
        Input('tsteps', 'value')
    ]
)
def statesirgraph(state, county,
            silent,tsteps):
    return sirgraph(state, 'All', silent, tsteps)

@app.callback(
    Output(component_id='statemodel-graph', component_property='figure'),
    [
        Input('state-dropdown', 'value'),
        Input('county-dropdown', 'value'),
        Input('silent-slider', 'value'),
        Input('hospitalizationrate-slider', 'value'),
        Input('icurate-slider', 'value'),
        Input('deathrate-slider', 'value'),
        Input('hospmodel', 'value'),
        Input('hosp_LOS', 'value'),
        Input('ICU_LOS', 'value'),
        Input('tsteps', 'value')
    ]
)
def statecensusgraph(state, county,
            silent, hosprate, icurate, deathrate, model,
            hosp_LOS, ICU_LOS, tsteps):
    return censusgraph(state, 'All', silent,
        hosprate, icurate, deathrate,
        hosp_LOS, ICU_LOS, tsteps, state, model)

@app.callback(
    Output(component_id='countymodel-graph', component_property='figure'),
    [
        Input('state-dropdown', 'value'),
        Input('county-dropdown', 'value'),
        Input('silent-slider', 'value'),
        Input('hospitalizationrate-slider', 'value'),
        Input('icurate-slider', 'value'),
        Input('deathrate-slider', 'value'),
        Input('hospmodel', 'value'),
        Input('hosp_LOS', 'value'),
        Input('ICU_LOS', 'value'),
        Input('tsteps', 'value')
    ]
)
def countycensusgraph(state, county,
            silent, hosprate, icurate, deathrate, model,
            hosp_LOS, ICU_LOS, tsteps):
    return censusgraph(state, county, silent,
        hosprate, icurate, deathrate,
        hosp_LOS, ICU_LOS, tsteps, (county+' County'), model)

@app.callback(
    Output(component_id='countyadmissions-graph', component_property='figure'),
    [
        Input('state-dropdown', 'value'),
        Input('county-dropdown', 'value'),
        Input('silent-slider', 'value'),
        Input('hospitalizationrate-slider', 'value'),
        Input('icurate-slider', 'value'),
        Input('deathrate-slider', 'value'),
        Input('hospmodel', 'value'),
        Input('hosp_LOS', 'value'),
        Input('ICU_LOS', 'value'),
        Input('tsteps', 'value')
    ]
)
def countyadmissionsgraph(state, county,
            silent, hosprate, icurate, deathrate, model,
            hosp_LOS, ICU_LOS, tsteps):
    return admissionsgraph(state, county, silent,
        hosprate, icurate, deathrate,
        hosp_LOS, ICU_LOS, tsteps, 'Admissions',model)

@app.callback(
    Output(component_id='stateadmissions-graph', component_property='figure'),
    [
        Input('state-dropdown', 'value'),
        Input('county-dropdown', 'value'),
        Input('silent-slider', 'value'),
        Input('hospitalizationrate-slider', 'value'),
        Input('icurate-slider', 'value'),
        Input('deathrate-slider', 'value'),
        Input('hospmodel', 'value'),
        Input('hosp_LOS', 'value'),
        Input('ICU_LOS', 'value'),
        Input('tsteps', 'value')
    ]
)
def stateadmissionsgraph(state, county,
            silent, hosprate, icurate, deathrate, model,
            hosp_LOS, ICU_LOS, tsteps):
    return admissionsgraph(state, 'All', silent,
        hosprate, icurate, deathrate,
        hosp_LOS, ICU_LOS, tsteps, 'Admissions', model)

@app.callback(
    Output(component_id='countydeath-graph', component_property='figure'),
    [
        Input('state-dropdown', 'value'),
        Input('county-dropdown', 'value'),
        Input('silent-slider', 'value'),
        Input('deathrate-slider', 'value'),
        Input('hospmodel', 'value'),
        Input('tsteps', 'value')
    ]
)
def countydeathgraph(state, county,
            silent,deathrate, model, tsteps):
    return deathgraph(state, county,
            silent, deathrate,
            tsteps,model)

@app.callback(
    Output(component_id='statedeath-graph', component_property='figure'),
    [
        Input('state-dropdown', 'value'),
        Input('county-dropdown', 'value'),
        Input('silent-slider', 'value'),
        Input('deathrate-slider', 'value'),
        Input('hospmodel', 'value'),
        Input('tsteps', 'value')
    ]
)
def statedeathgraph(state, county,
            silent,deathrate, model, tsteps):
    return deathgraph(state, 'All',
            silent, deathrate, tsteps,
            model)

if __name__ == '__main__':

    application.run(debug=True)
