# COVID-19 Geographic Impact Calculator (COGIC) 

COGIC is a county- and state- level covid-19 epidemic curve calculator. 

Estimated cases are calculated according to a
**Susceptible-Infected-Removed (SIR)** continuous, deterministic epidemic model.

The model generally follows the methodology of 
[CHIME from UPenn](https://code-for-philly.gitbook.io/chime/). 
This model was developed for estimating hospital resource utilization on a regional 
level. It estimates the epi curve using the SIR equations with a fixed gamma (1/14), 
and calculates beta via the estimated doubling time of the infection in the area.
In Chime, this doubling time is an adjustable parameter. 

The current model makes the following modifications to CHIME:

* The models are US state and county specific.
* The beta parameter for the SIR model is calculated from the 7-day averaged
observed doubling time for the state. State doubling times are used for county calculations
as most US counties currently have a low case count.
* 2018 US population estimates at the state and county levels are used for epidemic curve modeling.
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


