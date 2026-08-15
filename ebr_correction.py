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

from src.config.ff_config import QuantileIQRFilterConfig
from src.filters import quantile_iqr_filter
from src.plots import debug_plot_changes

# data.to_pickle("test.pkl")
data: pd.DataFrame = pd.read_pickle("test.pkl")
# 'Rn_1_1_1' = 'NETRAD_1_1_1'
# shf_1_1_1 = g_1_1_1

data = data[0: 200]

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


# removing spikes with IQR 1.5
data['ebc_cf_f'] = data['ebc_cf'] 
iqr_cfg = QuantileIQRFilterConfig(enabled=True, window_size_days=31, tgt_cols={'ebc_cf_f': 1.5})
with debug_plot_changes(debug=True, df=data, cols=['ebc_cf_f'], extra_cols=None, title='iqr_filter'):
    data, _ = quantile_iqr_filter(df_in=data, filters_db_in={'ebc_cf_f': []}, debug=False, cfg_quantile=iqr_cfg, df_copy=False)
    data.loc[~data['ebc_cf_f_quantile_iqr_filter'].astype(bool), 'ebc_cf_f'] = np.nan


# важны только в местное время 22:00–02:30 и 10:00-14:30
idx_1 = data.index.indexer_between_time('22:00', '02:30')
idx_2 = data.index.indexer_between_time('10:00', '14:30')
idx = np.hstack((idx_1, idx_2))
time_mask = np.zeros(len(data), dtype=bool)
time_mask[idx] = True

data.loc[time_mask, 'ebc_cf_f'] = np.nan


t_delta = pd.Timedelta(30, 'days')
# t_delta = pd.Timedelta(3, 'hours')
data['ebc_cf_f_count_in_15_days'] = data['ecf'].rolling(window=t_delta, center=True).count()

data['ebc_cf_f_q25'].rolling(window=t_delta, center=True).quantile(0.25)
data['ebc_cf_f_q50'].rolling(window=t_delta, center=True).quantile(0.50)
data['ebc_cf_f_q75'].rolling(window=t_delta, center=True).quantile(0.75)

more_than_5_ecf = data['ebc_cf_f_count_in_15_days'] > 5

data['h_corr'] = np.nan
data['l_corr'] = np.nan
data['h_corr'][more_than_5_ecf] = data['h'][more_than_5_ecf] * data['ebc_cf']
data['l_corr'][more_than_5_ecf] = data['l'][more_than_5_ecf] * data['ebc_cf']

pass
