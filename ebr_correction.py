# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---
import numpy as np
# %% [markdown] id="HEead7faY22W"
# # EBR correction

# %% id="E4rv4ucOX8Yz"

import pandas as pd
# data.to_pickle("test.pkl")
data: pd.DataFrame = pd.read_pickle("test.pkl")
# 'Rn_1_1_1' = 'NETRAD_1_1_1'
# shf_1_1_1 = g_1_1_1

# assert в местное время 22:00 – 02:30 и 10:00-14:30 (ensure via solar radiation?)

'''
Index(['timestamp_start', 'timestamp_end', 'dtime', 'alb_1_1_1',
       'co2_mole_fraction', 'co2_signal_strength', 'co2_flux', 'qc_co2_flux',
       'x_70%', 'x_90%', 'x_peak', 'fh2o_1_1_1', 'shf_1_1_1', 'shf_2_1_1',
       'shf_3_1_1', 'h', 'qc_h', 'le', 'qc_le', 'lwin_1_1_1', 'lwout_1_1_1',
       'l', 'rn_1_1_1', 'p_1_1_1', 'pa_1_1_1', 'ppfd_1_1_1', 'rh_1_1_1',
       'co2_strg', 'h_strg', 'le_strg', 'swin_1_1_1', 'swout_1_1_1',
       't_dp_1_1_1', 'sonic_temperature', 'ta_1_1_1', 'tau', 'qc_tau',
       'ts_1_1_1', 'ts_1_2_1', 'ts_1_3_1', 'ts_1_4_1', 'u_sigma_1_1_1',
       'u_star', 'v_sigma_1_1_1', 'vpd_pi_1_1_1', 'w_sigma_1_1_1', 'wd_1_1_1',
       'mws_1_1_1', 'wtd_1_1_1', '(z-d)/l', 'datetime', 'vpd_1_1_1',
       'rg_1_1_1', 'p_rain_1_1_1', 'par', 'nee'],
      dtype='object')
'''

data['ebc_cf'] = (data['rn_1_1_1'] - data['shf_1_1_1']) / (data['h'] + data['le'])


# важны только в местное время 22:00 – 02:30 и selected_time_index = data.index.indexer_between_time('22:00', '02:30') or data.index.indexer_between_time('22:00', '02:30')10:00-14:30
idx_1 = data.index.indexer_between_time('22:00', '02:30')
idx_2 = data.index.indexer_between_time('22:00', '02:30')
idx = np.hstack((idx_1, idx_2))

data['ebc_cf_filtered'] = data['ebc_cf']
data['ebc_cf_filtered'].iloc[~idx] = np.nan

t_delta = pd.Timedelta(15, 'days')
# t_delta = pd.Timedelta(3, 'hours')
data['ebc_cf_15_days_count'] = data['ebc_cf_filtered'].rolling(window=t_delta, center=True).count()



pass