
import numpy as np
import pandas as pd

from src.config.ff_config import QuantileIQRFilterConfig
from src.filters import quantile_iqr_filter
from src.plots import debug_plot_changes, plot_cols

# data.to_pickle("test.pkl")
# load pre-saved final result of FluxFilter from file
data: pd.DataFrame = pd.read_pickle("tv_fy4_2016_v01.xlsx.pkl")
# 'Rn_1_1_1' = 'NETRAD_1_1_1'
# shf_1_1_1 = g_1_1_1


WINDOW_DAYS=30 
# WINDOW_DAYS = 2
# data = pd.concat([data[0: 1000], data[14000:14200]])


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


# ### removing spikes with IQR 1.5
data['ebc_cf_f'] = data['ebc_cf'] 
iqr_cfg = QuantileIQRFilterConfig(enabled=True, window_size_days=30, tgt_cols={'ebc_cf_f': 1.5})
data, _ = quantile_iqr_filter(df_in=data, filters_db_in={'ebc_cf_f': []}, debug=False, cfg_quantile=iqr_cfg, df_copy=False)
data.loc[~data['ebc_cf_f_quantile_iqr_filter'].astype(bool), 'ebc_cf_f'] = np.nan
# plot_cols(data, ['ebc_cf', 'ebc_cf_f'], title='after IQR')

# ### важны только в местное время 22:00–02:30 и 10:00-14:30
idx_night = data.index.indexer_between_time('22:00', '02:30')
idx_day = data.index.indexer_between_time('10:00', '14:30')
idx_ok = np.hstack((idx_night, idx_day))
time_mask = np.zeros(len(data), dtype=bool)
time_mask[idx_ok] = True

data.loc[~time_mask, 'ebc_cf_f'] = np.nan
plot_cols(data, ['ebc_cf', 'ebc_cf_f'], title='after IQR and sunset sunrise remove')


# ### preparing ebr_cf quantiles
t_delta = pd.Timedelta(WINDOW_DAYS, 'days')
# t_delta = pd.Timedelta(3, 'hours')
data['ebc_cf_f_count_in_15_days'] = data['ebc_cf_f'].rolling(window=t_delta, center=True).count()

data['ebc_cf_f_30d_q25'] = data['ebc_cf_f'].rolling(window=t_delta, center=True).quantile(0.25)
data['ebc_cf_f_30d_q50'] = data['ebc_cf_f'].rolling(window=t_delta, center=True).quantile(0.50)
data['ebc_cf_f_30d_q75'] = data['ebc_cf_f'].rolling(window=t_delta, center=True).quantile(0.75)
data['ebc_cf_f_30d_mean'] = data['ebc_cf_f'].rolling(window=t_delta, center=True).mean()

gr_5_ecf = data['ebc_cf_f_count_in_15_days'] > 5
data_gr5 = data[gr_5_ecf]
between_1_5_ecf = data['ebc_cf_f_count_in_15_days'].isin(range(1, 5 + 1))
data_b1_5 = data[between_1_5_ecf]

plot_cols(data, ['ebc_cf_f', 'ebc_cf_f_count_in_15_days', 'ebc_cf_f_30d_mean', 'ebc_cf_f_30d_q25', 'ebc_cf_f_30d_q50', 'ebc_cf_f_30d_q75'])


# ### applying corrections where possible
data['h_corr_25'] = data_gr5['h'] * data_gr5['ebc_cf_f_30d_q25']
data['h_corr'] = data_gr5['h'] * data_gr5['ebc_cf_f_30d_q50']
data['h_corr_75'] = data_gr5['h'] * data_gr5['ebc_cf_f_30d_q75']
data['l_corr_25'] = data_gr5['l'] * data_gr5['ebc_cf_f_30d_q25']
data['l_corr'] = data_gr5['l'] * data_gr5['ebc_cf_f_30d_q50']
data['l_corr_75'] = data_gr5['l'] * data_gr5['ebc_cf_f_30d_q75']

data['h_corr'] = data_b1_5['l'] * data_b1_5['ebc_cf_f_30d_mean']
data['l_corr'] = data_b1_5['l'] * data_b1_5['ebc_cf_f_30d_mean']

plot_cols(data, ['h', 'h_corr_25', 'h_corr', 'h_corr_75'])
plot_cols(data, ['l', 'l_corr_25', 'l_corr', 'l_corr_75'])
