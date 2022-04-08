# -*- coding: utf-8 -*-
"""
Created on Thu Apr  8 18:20:21 2021

@author: weibe
"""

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from time import process_time
import pandas as pd
import pandapower as pp 
import matplotlib.pyplot as plt

from utils import run_pf_sim


# LOAD DATA #
#############
data = pd.read_csv('data/mesures.csv', index_col=0, parse_dates=True)

# PLOT RAW DATA #
#################
data[['P_NET_TRAFO','P_TENNIS']].plot()
data[['V_avg_trafo','V_avg_tennis']].plot()


# Run Powerflow simulation #
############################
start_date = str(data.index[0])
end_date = str(data.index[-1])
output_dir = 'sim_result'
t1_start = process_time()
 
run_pf_sim(1.03, data, start_date, end_date, output_dir)

t1_stop = process_time()
print("Elapsed time during the whole program in seconds:", t1_stop-t1_start) 


# PLOT #
########
res_raw = pd.read_csv(output_dir+str('/res_bus/vm_pu.csv'), sep=';', index_col=0)
res_raw.index = pd.to_datetime(res_raw.index)
plt.figure()
plt.plot(data[start_date: end_date].V_avg_tennis,  label='Mesuré')
plt.plot(res_raw['7']*230, label='Simulé', C='r', linewidth=2)
plt.ylabel('Tension [V]', fontsize=17)
plt.legend(fontsize=15)









