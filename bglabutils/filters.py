import numpy as np
import pandas as pd
from copy import deepcopy as copy
def hampel_filter_pandas(input_series, window_size=20, n_sigmas=3, k=1.4826, **kwargs ):
    print(f"Applying Hampel filter, window_size={window_size}, n_sigmas={n_sigmas}, k={k} ")
    l_k = k  # scale factor for Gaussian distribution
    new_series = input_series.copy()
    indices = None
    # # helper lambda function
    MAD = lambda x: np.median(np.abs(x - np.median(x)))

    rolling_median = input_series.rolling(window=2 * window_size, center=True).median()
    rolling_mad = l_k * input_series.rolling(window=2 * window_size, center=True).apply(MAD)
    diff = np.abs(input_series - rolling_median)

    # print(len(diff.index), len(rolling_mad.index))
    indices = diff > (n_sigmas * rolling_mad)

    return new_series, indices[indices == True].index


def mad_filter(input_df, target_col, z=5.5, fill_method='new', **kwargs):

    print(f"Applying MAD filter, z={z}, fill_method={fill_method}")
    data_if = input_df[[target_col]].copy()
    data_if['rolling_fill'] = data_if[target_col].rolling(10).mean()
    data_if['plus_shift'] = data_if[target_col].shift(1)
    null_index_plus = data_if['plus_shift'].isnull()
    null_index_plus = null_index_plus[null_index_plus == True].index

    data_if['minus_shift'] = data_if[target_col].shift(-1)
    null_index_minus = data_if['minus_shift'].isnull()
    null_index_minus = null_index_minus[null_index_minus == True].index

    if fill_method == 'old':
        data_if.loc[null_index_plus, 'plus_shift'] = data_if.loc[null_index_plus, target_col]
        data_if.loc[null_index_minus, 'minus_shift'] = data_if.loc[null_index_minus, target_col]
    else:
        data_if.loc[null_index_plus, 'plus_shift'] = data_if.loc[null_index_plus, 'rolling_fill']
        data_if.loc[null_index_minus, 'minus_shift'] = data_if.loc[null_index_minus, 'rolling_fill']

    data_if['d_i'] = (data_if[target_col] - data_if['minus_shift']) - (data_if['plus_shift'] - data_if[target_col])
    d_median = np.median(data_if.query('not (d_i != d_i)')['d_i'])
    MAD = np.median(np.abs(data_if.query('not (d_i != d_i)')['d_i'] - d_median))

    down_threshold = d_median - (z * MAD / 0.6745)
    up_threshold = d_median + (z * MAD / 0.6745)

    out_data = np.logical_or(data_if['d_i'] < down_threshold, data_if['d_i'] > up_threshold, data_if['d_i'].isna())
    out_data = np.logical_not(out_data)
    return out_data


def apply_hampel_filter(df_input, target_cols,  **kwargs):

    if not isinstance(df_input, dict):
        l_data = {'default': df_input.copy()}
    else:
        l_data = {key: item.copy() for key, item in df_input.items()}
    l_targets = copy(target_cols)

    if not isinstance(target_cols, list):
        l_targets = [l_targets]


    for key, item in l_data.items():
        for target in l_targets:
            item[f'{target}_hampel'] = True
            _, indices = hampel_filter_pandas(item.loc[np.invert(pd.isnull(item[target])), target], **kwargs)
            item.loc[indices, f'{target}_hampel'] = False
    if 'default' in l_data.keys():
        return l_data['default']
    else:
        return l_data


def apply_mad_filter(df_input, target_cols,  **kwargs):

    if not isinstance(df_input, dict):
        l_data = {'default': df_input.copy()}
    else:
        l_data = {key: item.copy() for key, item in df_input.items()}

    l_targets = target_cols

    if not isinstance(target_cols, list):
        l_targets = [l_targets]

    if 'z' in kwargs.keys():
        z = kwargs['z']
    else:
        z = 5.5

    for key, item in l_data.items():
        for target in l_targets:
            item[f'{target}_mad_{z}'] = True
            item.loc[np.invert(pd.isnull(item[target])), f'{target}_mad_{z}'] = mad_filter(item.loc[np.invert(pd.isnull(item[target])), l_targets], target, **kwargs)

    if 'default' in l_data.keys():
        return l_data['default']
    else:
        return l_data

def apply_hampel_after_mad(df_input, target_cols,  **kwargs):

    if not isinstance(df_input, dict):
        l_data = {'default': df_input.copy()}
    else:
        l_data = {key: item.copy() for key, item in df_input.items()}

    l_targets = target_cols

    if 'z' in kwargs.keys():
        z = kwargs['z']
    else:
        z = 5.5

    for key, item in l_data.items():
        for target in l_targets:
            item[f'{target}_mad_{z}'] = True
            item.loc[np.invert(pd.isnull(item[target])), f'{target}_mad_{z}'] = mad_filter(item.loc[np.invert(pd.isnull(item[target])), l_targets], target, **kwargs)

            item[f'{target}_filtered'] = True
            _, indices = hampel_filter_pandas(item.loc[np.invert(pd.isnull(item[target]) & item[f'{target}_mad_{z}'] == True), target], **kwargs)
            item.loc[indices, f'{target}_filtered'] = False
            item[f'{target}_filtered'] = np.logical_or(item[f'{target}_mad_{z}'], item[f'{target}_filtered'])
            item.drop(columns=[f'{target}_mad_{z}'], inplace=True)

    if 'default' in l_data.keys():
        return l_data['default']
    else:
        return l_data