# hospCensusModels.py

import pandas as pd
import numpy as np
from populationModels import census2cdc, census2verity, loadUSCountyPopStructure

# CDC data from MMWR data, corrected to NYC population
# structure and
cdc_hosp_correction_factor = 0.132
cdc_deaths_correction_factor = 0.184

class HospitalCensus:
    def __init__(self):
        self.cdcadmissions = pd.read_csv('data/cdcadmissions.csv')
        self.cdcdeaths = pd.read_csv('data/cdcdeaths.csv')

        self.verityadmissions = pd.read_csv('data/verityadmissions.csv')
        self.veritydeaths = pd.read_csv('data/veritydeaths.csv')

        self.us_popstructure = loadUSCountyPopStructure()

    def calcCDCAdmissionRates(self,popstructure):
        return pd.Series(
            popstructure@self.cdcadmissions.values,
            index=self.cdcadmissions.columns
            ) * cdc_hosp_correction_factor

    def calcCDCDeathRates(self, popstructure):
        return pd.Series(
            popstructure@self.cdcdeaths.values,
            index=self.cdcdeaths.columns
            ) * cdc_deaths_correction_factor

    def calcVerityAdmissionRates(self,popstructure):
        """Assumes 1/2 of admissions are ICU.
        This correction is already in the file.
        """
        print(self.verityadmissions.values)
        return pd.Series(
            popstructure@self.verityadmissions.values,
            index=self.verityadmissions.columns
        )

    def calcVerityDeathRates(self, popstructure):
        return pd.Series(
            popstructure@self.veritydeaths.values,
            index=self.veritydeaths.columns
            )

    def calcAdmissions(self, incidence, admissionrates):
        return pd.DataFrame(
            {
                key: pd.Series(admissionrates[key]*incidence,
                            index=np.arange(len(incidence)))
                for key in admissionrates.index
            }
        ).apply(np.round)

    def calcCensus(self,
                   incidence,
                   admissionrates,
                   LOS):
        """Use the incidence data above, along with
        length-of-stay to calc census
        Use incidence, a dataframe of Censustype:admissionrate
        and a vector of lengths of stay to calculate
        hospital census
        """

        admissions = self.calcAdmissions(incidence, admissionrates)
        census = pd.DataFrame({
                key: (
                    admissions[key].cumsum()
                    -admissions[key].cumsum().shift(los).fillna(0)
                ) for key, los in LOS.items()
                })

        return census


    def createPopulation(self, state, county, data, model):

        # create state and county-specific dataframes and parameters

        # Note: the state names in popstructure do not have
        # whitespace, unlike the statenames from the dropdown
        # (e.g., 'New York' vs 'NewYork'). That's the reason
        # for .replace() below
        # .replace(' City','') is specifically for New York
        # TODO: make the popstructure and countylist
        # county headings consistent

        # sum all counties to get state case data
        tmpdata = data[state].swaplevel(0,-1,axis=1)
        statedata = pd.DataFrame()
        for i in [x for x in set(tmpdata.columns.get_level_values(0))]:
            statedata[i] = tmpdata[i].sum(axis=1)

        if county=='All':
            statekey = state.replace(' ','')
            popstructure = self.us_popstructure[statekey].sum(axis=1)
            data = {
                'state': statedata,
                'county':statedata
                }
        else:
            # for individual county
            statekey = state.replace(' ','')
            countykey = county.replace(' City','')
            popstructure = self.us_popstructure[statekey][countykey]
            data = {
                'state': statedata,
                'county':data[state][county]
                }
        # 0 represents whole state list
        # return both the state case data and county case
        # data, so one can cose with which to fit beta
        # later on

        N = popstructure.sum()
        popstructure /= popstructure.sum()
        if model=='Verity':
            popstructure = census2verity(popstructure)
        else:
            popstructure = census2cdc(popstructure)

        return (data, popstructure, N)

    def calcAdmissionRates(self, popstructure, hosprate, icurate, model=None):
        if model=='CDC':
            admissionrates = self.calcCDCAdmissionRates(popstructure)
        elif model=='Verity':
            admissionrates = self.calcVerityAdmissionRates(popstructure)
        else:
            admissionrates = pd.Series({
                'Hospitalized': hosprate,
                'ICU': icurate
            })
        return admissionrates

    def calcLOS(self, hosp_LOS, ICU_LOS, model):
        if model=='CDC':
            LOS = {
                'Hospitalized-low': hosp_LOS,
                'Hospitalized-high': hosp_LOS,
                'ICU-low': ICU_LOS,
                'ICU-high': ICU_LOS,
            }
        elif model=='Verity':
            LOS = {
                'Hospitalized-low': hosp_LOS,
                #'Hospitalized-mean': hosp_LOS,
                'Hospitalized-high': hosp_LOS,
                'ICU-low': ICU_LOS,
                #'ICU-mean': ICU_LOS,
                'ICU-high': ICU_LOS,
            }
        else:
            LOS = {
                'Hospitalized': hosp_LOS,
                'ICU': ICU_LOS,
            }
        return LOS

    def calcDeathRates(self, deathrate, popstructure, model=None):
        if model=='CDC':
            return self.calcCDCDeathRates(popstructure)
        elif model=='Verity':
            return self.calcVerityDeathRates(popstructure)
        else:
            return deathrate

