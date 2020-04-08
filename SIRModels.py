import numpy as np
from scipy.integrate import odeint
from scipy.optimize import minimize, curve_fit

def doubling_time(y):
    """Finds doubling time of series y.
    Calculates instantaneous doubling times, 
    then returns ewma.
    """
    x = np.arange(len(y))
    lny = np.log(y)#.replace([np.inf, -np.inf], np.nan).dropna()
    Td = np.log(2)/np.gradient(lny)

    #remove nan, inf, 0 values
    Td = np.delete(Td,np.where(Td==0))
    Td = Td[np.logical_not(np.isnan(Td))]
    Td = np.delete(Td,np.where(np.abs(Td)==np.inf))
    return Td

def beta_from_doubling_time(Td, gamma):

    return 2**(1/Td) - 1 + gamma

def fitexpgrowthrate(x, y):
    def func(x, A, B, C):
        return A * np.exp(B*x) + C
    popt, pfit = curve_fit(func, x, y, p0=(1.,.01,1.))
    return popt[1] # exp growth rate

def estimate_beta(x, gamma):
    """Estimate gamma parameter from SIR model
    based on exponential growth rate. Calcs based in
    part on CHIME.
    old code:
    B = fitexpgrowthrate(len(x), x)
    beta = B + gamma
    return beta
    """
    Td = doubling_time(x)
    return beta_from_doubling_time(Td, gamma)[-7:].mean()

# The SIR model differential equations.
def SIR(y, t, N, beta, gamma):
    S, I, R = y
    dSdt = -beta * S * I / N
    dIdt = beta * S * I / N - gamma * I
    dRdt = gamma * I
    return dSdt, dIdt, dRdt

def continuousSIR(beta, gamma, N, I0, timepts):
    I0 = I0 #initial infected
    R0 = 0 #inital recovered
    S0 = N - I0 - R0 #initial Susceptible

    y0 = S0, I0, R0
    #print('initial conditions', y0)
    result = odeint(SIR, y0, timepts, args=(N, beta, gamma))
    S, I, R = result.T

    Inew = -np.gradient(S) # incidence is neg gradient of susceptible

    return {'S':S,'I':I,'R':R, 'Inew':Inew}

# Discrete SIR model. Adapted from
# https://code-for-philly.gitbook.io/chime/what-is-chime/sir-modeling
def discreteSIR(beta, gamma, N, I0, tsteps):
    """beta - vector of effectivate reproduction values
    γ - 1/infection duration
    N - total susceptible population
    I0 - initial infections
    tsteps - timesteps
    """
    S = np.zeros_like(tsteps) #current susceptible
    I = np.zeros_like(tsteps) #current infected
    R = np.zeros_like(tsteps) # removed
    Inew = np.zeros_like(tsteps) #newly infected per timestep
    I[0] = I0
    Inew = I
    S[0] = N-I0
    R[0] = 0

    for i in tsteps[1:]:
        Inew[i] = (beta/N) * S[i-1] * I[i-1]
        S[i] = S[i-1] - Inew[i]
        I[i] = I[i-1] + Inew[i] - gamma * I[i-1]
        R[i] = R[i-1] + gamma * I[i-1]

    return {'S':S, 'I':I, 'Inew':Inew, 'R':R}



