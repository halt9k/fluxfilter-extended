import os
import pandas as pd
import sys
import numpy as np
from string import digits
from sklearn.preprocessing import FunctionTransformer
import calendar
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from copy import deepcopy as copy
import random

def load_df(d_config, sheet_name=None):

    if isinstance(d_config['path'], list) or isinstance(d_config['path'], tuple):
        multi_out = []
        time = None
        for file in d_config['path']:
            temp_config = d_config.copy()
            temp_config['path'] = file
            loaded_data, time = load_df(temp_config)
            multi_out = multi_out + [df for df in loaded_data.values()]
        freqs = [df.index.freq for df in  loaded_data.values()]
        if not np.all(np.array(freqs) == freqs[0]):
            print("Different freq in data files. Aborting!")
            return None

        multi_out = pd.concat(multi_out)
        multi_out = multi_out.sort_index()
        multi_out = repair_time(multi_out, time)
        return {'default':multi_out}, time

    file_name = d_config['path']#os.path.normpath(d_config['path'])
    _, file_extension = os.path.splitext(file_name)
    ext = 'csv' if '.csv' in file_extension.lower() else None
    ext = 'excel' if file_extension.lower() in ['.xls', '.xlsx'] else ext

    load_func = None
    l_config = {}

    if 'debug' in d_config.keys():
        if d_config['debug'] == True and 'nrows' not in l_config.keys():
            l_config['nrows'] = 500

    if ext == 'csv':
        load_func = pd.read_csv
    if ext == 'excel':
        load_func = pd.read_excel
        l_config['sheet_name'] = sheet_name

    if not load_func:
        print(f"Wrong file extension, got {ext}, need csv, xls or xlsx")
        return None
    tmp_config = l_config.copy()
    tmp_config['nrows'] = 4
    tmp_config['header'] = None
    # tmp_config['engine'] = 'openpyxl'
    df_dict = None
    with open(file_name, encoding='utf8', errors='backslashreplace') as f:
        df_dict = load_func(f, **tmp_config)

    if ext == 'csv':
        df_dict = {'default': df_dict}

    l_config['skiprows'] = []

    for key, item in df_dict.items():
        item = item.dropna(how='all', axis=1)
        if (item.loc[0, :].isnull()).sum() > 2:
            print(f"skipping line 1, 3")
            l_config['skiprows'] = [0, 2]  # .append(i)
            continue

        item = item.replace('NAN', np.nan)
        item = item.dropna(how='all', axis=1)
        cond_1 = np.isreal(item.loc[1, :].to_numpy()) == False#(item.loc[1, :].astype(str).str.isnumeric() == False)#(item.loc[0, item.columns != d_config['time']].astype(str).str.isnumeric() == False)
        cond_2 = (item.loc[1, :].isna())#(item.loc[0, item.columns != d_config['time']].isna())


        if (cond_1.sum() > 1 and cond_2.sum() !=len(item.columns) - 1) or (cond_1.sum()==0 and cond_2.sum()==0): #cond_1.sum() > 1 and cond_2.sum() != len(item.columns) - 1: #any(item.loc[0, item.columns != d_config['time']].astype(str).str.isnumeric() == False) and not all(item.loc[0, item.columns != d_config['time']].isna()):
            l_config['skiprows'].append(1)#[1]#lambda x: x == 1
            print(f"skipping line #{1}")
            # else:
            #     pass
            #     # l_config['skiprows'] = None

    with open(file_name, encoding='utf8', errors='backslashreplace') as f:
        df_dict = load_func(f, **l_config)
    if ext == 'csv':
        df_dict = {'default': df_dict}

    if 'time' not in d_config:
        test_df = next(iter(df_dict.values()))
        tmp_time = [col for col in test_df.columns if is_datetime(test_df[col].dtype)]
        if len(tmp_time) == 1:
            print(f'Time column detected, {tmp_time[0]}')
            # d_config['time'] = tmp_time[0]
        else:
            print("can't detect datetime column, specify one in the config!")
            return None

    else:
        tmp_time = [d_config['time']['column_name']]
        for key, item in df_dict.items():
            item[tmp_time[0]] = d_config['time']['converter'](item) #pd.to_datetime(item[tmp_time[0]], format=d_config['time']['format'])

    if d_config['-9999_to_nan']:
        print('Replacing -9999 to np.nan')
        for key, item in df_dict.items():
            item.replace(to_replace=-9999, value=np.nan, inplace=True)


    for key, item in df_dict.items():

        # if not item.index.is_monotonic_increasing:
        #     print(f'WARNING the time-index is not monotonic for {key}!')
        # Проверяем время на монотонность
        item.dropna(how='all', axis=0, inplace=True)
        correct_number_of_time_entries = pd.date_range(item[tmp_time[0]].iloc[0], item[tmp_time[0]].iloc[-1],
                                                       freq=item[tmp_time[0]].iloc[1] - item[tmp_time[0]].iloc[0])

        if not correct_number_of_time_entries.size == len(item.index):
            print("Missing time values")

        if item[tmp_time[0]].is_monotonic_increasing:
            print(f"The time in {key} looks fine")
        else:
            print(f"The time is not monotonic in {key}")
            test_data = item.copy()
            test_data['shift'] = test_data[tmp_time[0]].shift(1)
            test_data['diff'] = test_data[tmp_time[0]] - test_data['shift']
            print("Try to check near: ", test_data.loc[~(test_data['diff'] > np.timedelta64(20, 's')), tmp_time[0]])
        if d_config['repair_time']:
            print("Fixing time")
            # item[tmp_time[0]] = pd.date_range(item[tmp_time[0]].iloc[0], item[tmp_time[0]].iloc[-1],
            #                            freq=item[tmp_time[0]].iloc[1] - item[tmp_time[0]].iloc[0])
            df_dict[key] = repair_time(item, tmp_time[0])
        item.index = item[tmp_time[0]]

    return df_dict, tmp_time[0]

def get_freq(df, time):
    try_max = 100
    try_ind = 0
    t_shift = 5
    start = 1
    deltas = df[time] - df[time].shift(1)
    while try_ind < try_max:
        del_arr = deltas.iloc[start + try_ind*t_shift : start + try_ind*t_shift + t_shift].values
        if not np.all(del_arr == del_arr[0]) and del_arr[0] is not None:
            try_ind = try_ind + 1
            continue
        else:
            return del_arr[0]

def repair_time(df, time):
    freq = get_freq(df, time)
    df = df.set_index(time, drop=False)
    tmp_index = df.index.copy()
    df = df[~df.index.duplicated(keep='first')]

    if not tmp_index.equals(df.index):
        print("Duplicated indexes! check lines:", tmp_index[tmp_index.duplicated() == True])

    start = 0
    stop = -1
    while True:
        try:
            pd.to_datetime(df[time].iloc[start])
            break
        except:
            start = start + 1
            continue
    while True:
        try:
            pd.to_datetime(df[time].iloc[stop])
            break
        except:
            stop = stop - 1
            continue
    new_time = pd.DataFrame(index=pd.date_range(start=df[time].iloc[start], end=df[time].iloc[stop],
                                                freq=pd.to_timedelta(freq)))
    # new_time[time] = new_time.index
    new_time = new_time.join(df, how='left')
    # new_time[time] = new_time[time+'_new']
    # new_time = new_time.drop(time+'_new', axis=1)
    return new_time

def concat_by_year(df_dict):

    sheets = [k for k in df_dict.keys()]
    sheets = [k.translate({ord(kl): None for kl in digits}) for k in sheets]
    unique_names = set(sheets)
    out_dict = {k: [] for k in unique_names}

    for key, item in df_dict.items():
        for group in unique_names:
            if group in key:
                out_dict[group].append(item)

    for group in out_dict.keys():
        out_dict[group] = pd.concat(out_dict[group])#, ignore_index=True)

    return  out_dict

def dict_transformer(func):
    def wrapper(*args, **kwargs):

        if isinstance(args[0], dict):
            output = {}
            isTuple = False
            for key, item in args[0].items():
                # new_args = copy(args)
                new_args = [item] + list(args[1:])
                output[key] = func(*new_args, **kwargs)
                if not isTuple and isinstance(output[key], tuple):
                    isTuple = True
            if isTuple:
                add_out = next(iter(output.values()))[1:]
                output = {key: item[0] for key, item in output.items()}
                return output, add_out
            else:
                return output

        else:
            return func(*args, **kwargs)

    return wrapper


def double_dict_transformer(func):
    def wrapper(*args, **kwargs):

        if isinstance(args[0], dict):
            output = {}
            isTuple = False
            for key, item in args[0].items():
                # new_args = copy(args)
                new_args = [item] + [args[1][key]] + list(args[2:])
                output[key] = func(*new_args, **kwargs)
                if not isTuple and isinstance(output[key], tuple):
                    isTuple = True
            if isTuple:
                add_out = next(iter(output.values()))[1:]
                output = {key: item[0] for key, item in output.items()}
                return output, add_out
            else:
                return output

        else:
            return func(*args, **kwargs)

    return wrapper

def sin_transformer(period):
    return FunctionTransformer(lambda x: np.sin(x / period * 2 * np.pi))

def cos_transformer(period):
    return FunctionTransformer(lambda x: np.cos(x / period * 2 * np.pi))

@dict_transformer
def add_time_features(data_f, time_col, year_sincos=True, hour_sincos=True):
    data = data_f.copy()
    data['day_of_year_f'] = data[time_col].dt.dayofyear
    data['year_f'] = data[time_col].dt.year
    years_in_dataset = data[time_col].dt.year.unique()
    n_Days_in_year = {i:366 if calendar.isleap(i) else 365 for i in years_in_dataset}
    new_features = []
    if year_sincos:
        new_features.append('year_sin')
        new_features.append('year_cos')
    for year in years_in_dataset:
      data.loc[data['year_f']==year, "year_sin"] = sin_transformer(n_Days_in_year[year]).fit_transform(data["day_of_year_f"])
      data.loc[data['year_f']==year, "year_cos"] = cos_transformer(n_Days_in_year[year]).fit_transform(data["day_of_year_f"])
    if hour_sincos:
        new_features.append('hour_sin')
        new_features.append('hour_cos')
        data['hour_sin'] = sin_transformer(24).fit_transform(data[time_col].dt.hour)
        data['hour_cos'] = sin_transformer(24).fit_transform(data[time_col].dt.hour)

    return data, new_features

@dict_transformer
def apply_func(data, func, **kwargs):
    return func(data, **kwargs)

# @dict_transformer
# def save_to_excel(data, path_to_file):
#     with pd.ExcelWriter("path to file\filename.xlsx") as writer:
#         # use to_excel function and specify the sheet_name and index
#         # to store the dataframe in specified sheet
#         data_frame1.to_excel(writer, sheet_name="Fruits", index=False)
#         data_frame2.to_excel(writer, sheet_name="Vegetables", index=False)
#         data_frame3.to_excel(writer, sheet_name="Baked Items", index=False)

def add_albedo(dataT, out_sw, in_sw):
    dataD = dataT.copy()
    dataD['Albedo'] = 0.
    loc_mask = dataD[out_sw]!=0 & ~dataD[out_sw].isna() & ~dataD[in_sw].isna()
    dataD.loc[loc_mask, 'Albedo'] =  np.divide(dataD.loc[loc_mask, out_sw].astype(float), dataD.loc[loc_mask, in_sw].astype(float))
    return dataD

@dict_transformer
def regenerate_time(data):
    pass

def calc_rolling(x_in, step=24 * 2, rolling_window=10, min_periods=False, ffill=True):
    if not min_periods:
        min_periods = int(rolling_window / 2) - 1
    rolling_mean = x_in.rolling(rolling_window, min_periods=min_periods, center=True, closed='both').apply(lambda x: np.mean(x[::step]))#, raw=True, engine="numba")
    if step % 2 == 0:
        closed='left'
    else:
        closed='both'
    rolling_mean =pd.concat([x_in.iloc[i::step].rolling(window=rolling_window, min_periods=min_periods, center=True, closed=closed).mean() for i in range(step)]).sort_index()
    # if ffill:
    #     rolling_mean = rolling_mean.ffill(limit_area='outside', limit=rolling_window-min_periods)
    #     rolling_mean = rolling_mean.bfill(limit_area='outside', limit=rolling_window-min_periods)
    return  rolling_mean
