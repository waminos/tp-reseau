# -*- coding: utf-8 -*-
"""
Created on Sun Jun  2 00:33:14 2019

@author: weibel
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pulp import LpVariable, LpProblem, LpStatus, lpSum, value, LpInteger, LpMinimize



# INITIALIZATION
###########
power_load = pd.read_csv('data/cdc_ferme.csv', index_col = 0, parse_dates=True)/1000
irradiation = pd.read_csv('data/irradiation.csv', index_col=0, parse_dates=True)/1000

power_load.plot()
irradiation.plot()


# CALCULATE TIMESTEP
tstep = float(power_load.index.inferred_freq[:-1])
print('#############')
print('Data resolution: '+str(round(tstep,3))+' minutes')

tstep = tstep/60
power_load = power_load.values
irradiation = irradiation.values

# MAKE SURE DATA HAVE SAME LENGTH
#####################
assert(len(power_load) == len(irradiation))

# DATA HORIZON
#####################
horizon = len(power_load)          

# PV PARAMETRES
#####################
rend_dc_ac = 0.99            # [-]
rend_pv= 0.18                # [%]
capital_pv= 200       # [CHF/m2]  
Smax = 50             # [m2] surface maximale disponible

# BATTERY PARAMETRES
#####################
rend_batt_in = 0.99
rend_batt_out = 0.99
Emax = 500             # [kWh] energie maximale possible
capital_batt = 300     # [CHF/kWh]
p_batt_max = 20

# ELECTRICITY PRICES
#####################
amortissement = 15
sell_price = tstep*0.06
buy_price  = tstep*0.25

fixed_sell_price = [sell_price for i in range(horizon)]
fixed_buy_price = [buy_price for i in range(horizon)]


#####################
# OPTIMIZATION
#####################


# OPTIMIZATION PROBLEM 
#####################
prb = LpProblem('OptimDim', sense = LpMinimize)
  
# PV VARIABLES
#####################
pv_cap = LpVariable('pv_cap', lowBound=0, upBound=Smax)
pv_out = [rend_dc_ac * rend_pv * irradiation[i] * pv_cap for i in range(horizon)]
pv_invest = capital_pv * pv_cap
        
    
# BATTERY VARIABLES
#####################
bat_cap = LpVariable('batt_cap', lowBound=0, upBound=Emax)  
bat_store = [LpVariable('bat_store{}'.format(i), 0, None) for i in range(horizon)]        # Batterie énergie (SOC) [kWh]
bat_in =    [LpVariable('batt_in_{}'.format(i), 0, None) for i in range(horizon)]        # Batterie charge [kW]
bat_out =   [LpVariable('batt_out_{}'.format(i), 0, None) for i in range(horizon)]      # Batterie décharge [kW]
bat_invest = capital_batt * bat_cap

    
# BATTERY CONSTRAINTS 
#####################
prb += bat_store[0] == 0

for i in range(horizon):
    prb += bat_store[i] == bat_store[i-1] + tstep * (rend_batt_in*bat_in[i] - rend_batt_out*bat_out[i]) 
    prb += bat_store[i] <= bat_cap    
    prb += bat_in[i] <= p_batt_max
    prb += bat_out[i] <= p_batt_max
        
 # BALANCE EQUATIONS 
#####################
grid = [LpVariable('power{}'.format(i), -np.max(power_load), None) for i in range(horizon)] 
cost = [LpVariable('cost{}'.format(i), None, None) for i in range(horizon)]      # Power cost [kW]

for i in range(horizon):
    prb +=  grid[i] == power_load[i]  - pv_out[i] - bat_out[i] + bat_in[i]
    prb += cost[i] >= fixed_buy_price[i] * grid[i] * tstep
    prb += cost[i] >= fixed_sell_price[i] * grid[i] * tstep


# OBJECTIVE FUNCTION 
#####################
prb +=  bat_invest + pv_invest + amortissement*26*lpSum(cost)     ## Minimisation des couts sur 10 ans
prb.solve()


print('#############')
print('Solution status : '+ str(LpStatus[prb.status]))
print('#############')
print('Amortissement sur : '+ str(amortissement)+' années')
print('PV : '+str(round(value(pv_cap),1)) + ' [m2]')
print('Batterie : '+str(round(value(bat_cap),1))+' [kWh]')
print('Investissement : '+str(round(value(pv_invest)+value(bat_invest)))+' [CHF]')
print('Facture élec. annuelle : '+str(round(value(26*lpSum(cost))))+' [CHF]')





