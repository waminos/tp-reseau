# -*- coding: utf-8 -*-
"""
Created on Thu Apr  8 18:26:53 2021

@author: weibe
"""


import pandas as pd
import numpy as np
import time
import pandapower as pp 
import os

from sklearn.preprocessing import MinMaxScaler, Normalizer
from pulp import LpVariable, LpProblem, LpStatus, lpSum, value, LpMinimize, const

from pandapower.timeseries import DFData
from pandapower.timeseries import OutputWriter
from pandapower.timeseries.run_time_series import run_timeseries
from pandapower.control import ConstControl


def network_hyp_opt(vm_mag):
    #create an empty network
    net = pp.create_empty_network() 
    
    # create bus of the network topology
    bus_MV = pp.create_bus(net, name="MV bus", vn_kv=20, type="n")
    bus_LV = pp.create_bus(net, name="LV bus", vn_kv=0.4, type="b")
    bus1 = pp.create_bus(net, name="LV bus 1", vn_kv=0.4, type="b")
    bus2 = pp.create_bus(net, name="LV bus 2", vn_kv=0.4, type="b")
    bus3 = pp.create_bus(net, name="LV bus 3", vn_kv=0.4, type="b")
    bus4 = pp.create_bus(net, name="LV bus 4", vn_kv=0.4, type="n")
    bus5 = pp.create_bus(net, name="LV bus 5", vn_kv=0.4, type="b")
    bus6 = pp.create_bus(net, name="LV bus 6", vn_kv=0.4, type="b")
    bus7 = pp.create_bus(net, name="LV bus 7", vn_kv=0.4, type="b")

    
    # create external grid
    pp.create_ext_grid(net, bus_MV, vm_pu=vm_mag)
    
    # create trafos
    pp.create_transformer(net, bus_MV, bus_LV, name="Trafo 1", std_type="0.4 MVA 20/0.4 kV")
    # pp.create_transformer_from_parameters(net=net, vm_pu=tap_ratio, hv_bus=bus_MV, lv_bus=bus_LV, name="TRAFO", sn_mva=16, vn_hv_kv=20, vn_lv_kv=0.4, vkr_percent=1, vk_percent=9.5, pfe_kw=5, i0_percent=0.15)
    
    # create lines
    pp.create_line_from_parameters(net, bus_LV, bus1, length_km=0.5, max_i_ka=1.5, r_ohm_per_km=0.373, x_ohm_per_km=0.08, c_nf_per_km=580, name='Line 1')
    pp.create_line_from_parameters(net, bus_LV, bus2, length_km=0.32,max_i_ka=1.5, r_ohm_per_km=0.373, x_ohm_per_km=0.08, c_nf_per_km=580, name='Line 2')
    pp.create_line_from_parameters(net, bus2, bus3, length_km=0.06,max_i_ka=1.5, r_ohm_per_km=0.373, x_ohm_per_km=0.08, c_nf_per_km=580, name='Line 1')
    pp.create_line_from_parameters(net, bus2, bus4, length_km=0.14,max_i_ka=1.5, r_ohm_per_km=0.373, x_ohm_per_km=0.08, c_nf_per_km=580, name='Line 1')
    pp.create_line_from_parameters(net, bus2, bus5, length_km=0.08,max_i_ka=1.5, r_ohm_per_km=0.373, x_ohm_per_km=0.08, c_nf_per_km=580, name='Line 1')
    pp.create_line_from_parameters(net, bus2, bus6, length_km=0.17,max_i_ka=1.5, r_ohm_per_km=0.373, x_ohm_per_km=0.08, c_nf_per_km=580, name='Line 1')
    pp.create_line_from_parameters(net, bus2, bus7, length_km=0.15,max_i_ka=1.5, r_ohm_per_km=0.373, x_ohm_per_km=0.08, c_nf_per_km=580, name='Line 1')

    # create loads
    pp.create_load(net, bus6, p_mw=0, name="tennis")
    pp.create_load(net, bus3, p_mw=0, name="load")
    
    return net



def create_data_source_hyp_opt(df, start_date, end_date):
    profiles = pd.DataFrame()
    profiles['net_tennis'] = df.loc[start_date : end_date].P_TENNIS * (10**-6)
    profiles['net_trafo'] = df.loc[start_date : end_date].P_NET_TRAFO * (10**-6)
    ds = DFData(profiles)

    return profiles, ds


def create_controllers_hyp_opt(net, ds):
    ConstControl(net, element='load', variable='p_mw', element_index=[0],
                 data_source=ds, profile_name=["net_tennis"])
    
    ConstControl(net, element='load', variable='p_mw', element_index=[1],
              data_source=ds, profile_name=["net_trafo"])


def create_output_writer_hyp_opt(net, time_steps, output_dir):
    ow = OutputWriter(net, time_steps, output_path=output_dir, output_file_type=".csv", log_variables=list())
    ow.log_variable('res_load', 'p_mw')
    ow.log_variable('res_bus', 'vm_pu')
    ow.log_variable('res_line', 'loading_percent')
    ow.log_variable('res_line', 'i_ka')
    return ow



def run_pf_sim(tap_ratio, data, start_date, end_date, output_dir):
    # 1. create test net
    net = network_hyp_opt(tap_ratio)

    # 2. create (random) data source
    profiles, ds = create_data_source_hyp_opt(data, start_date, end_date)

    # 3. create controllers (to control P values of the load and the sgen)
    create_controllers_hyp_opt(net, ds)

    # time steps to be calculated. Could also be a list with non-consecutive time steps
    time_steps = profiles.index

    # 4. the output writer with the desired results to be stored to files.
    ow = create_output_writer_hyp_opt(net, time_steps, output_dir=output_dir)

    # 5. the main time series function
    run_timeseries(net, time_steps, verbose=False)