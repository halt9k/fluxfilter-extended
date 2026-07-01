""" original source: https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null """

import numpy as np
import pandas as pd

from bglabutils import basic as bg, filters as bf
from src.config.ff_config import QuantileIQRFilterConfig, QuantileFilterConfig, RollingDiurnalOutlierFilterConfig
from src.ff_logger import ff_logger
from src.plots import get_column_filter, plot_cols


def rolling_diurnal_outlier_filter_col(df, col_name, cfg_rolling: RollingDiurnalOutlierFilterConfig):
    """
    Applies a rolling diurnal outlier filter to a specified column in a DataFrame.
    Outliers are detected based on the median and IQR of values within a rolling
    weekly window and a +/- 'hour_tolerance' time-of-day window.

    Args:
        df (pd.DataFrame): The input DataFrame. Must contain 'TIMESTAMP_START_DATETIME'
                           and 'TIMESTAMP_END_DATETIME' columns.
        col_name (str): The name of the column to filter.
        window_days (int): The size of the rolling window in days (e.g., 7 for weekly).
        hour_tolerance (int): The number of hours +/- the current time to consider
                              for the diurnal distribution.
        iqr_multiplier (float): The multiplier for the IQR to define outlier bounds.

    Returns:
        pd.Series: A new Series with outliers replaced by NaN.
    """
    if col_name not in df.columns:
        print(f"  Error: Column '{col_name}' not found in DataFrame. Skipping filter.")
        return df[col_name].copy()
    
    filtered_series = df[col_name].copy()
    
    # TODO 1 what is going on
    df['TIMESTAMP_START_DATETIME'] = df.index
    time_series = df['TIMESTAMP_START_DATETIME']
    
    df_temp = df[[col_name, 'TIMESTAMP_START_DATETIME']].copy()
    df_temp['hour'] = df_temp['TIMESTAMP_START_DATETIME'].dt.hour
    df_temp['minute'] = df_temp['TIMESTAMP_START_DATETIME'].dt.minute
    
    for idx, current_ts in enumerate(time_series):
        current_val = filtered_series.iloc[idx]
        if pd.isna(current_val):
            continue
        
        window_start_date = current_ts - pd.Timedelta(days=cfg_rolling.window_size_days / 2)
        window_end_date = current_ts + pd.Timedelta(days=cfg_rolling.window_size_days / 2)
        
        date_window_data = df_temp[
            (df_temp['TIMESTAMP_START_DATETIME'] >= window_start_date) &
            (df_temp['TIMESTAMP_START_DATETIME'] <= window_end_date)
            ]
        
        if date_window_data.empty:
            continue
        
        min_hour = (current_ts.hour - cfg_rolling.hour_tolerance) % 24
        max_hour = (current_ts.hour + cfg_rolling.hour_tolerance) % 24
        
        if min_hour <= max_hour:
            diurnal_window_data = date_window_data[
                (date_window_data['hour'] >= min_hour) &
                (date_window_data['hour'] <= max_hour) &
                (date_window_data['minute'] == current_ts.minute)
                ]
        else:
            diurnal_window_data = date_window_data[
                ((date_window_data['hour'] >= min_hour) | (date_window_data['hour'] <= max_hour)) &
                (date_window_data['minute'] == current_ts.minute)
                ]
        
        values_in_window = diurnal_window_data[col_name].dropna()
        
        if len(values_in_window) < 2:
            continue
        
        median_val = values_in_window.median()
        q1 = values_in_window.quantile(0.25)
        q3 = values_in_window.quantile(0.75)
        iqr_m = cfg_rolling.iqr_multiplier * (q3 - q1)
        
        if iqr_m == 0:
            if not np.isclose(current_val, median_val, equal_nan=True):
                filtered_series.iloc[idx] = np.nan
        else:
            lower_bound = median_val - iqr_m
            upper_bound = median_val + iqr_m
            
            if not (lower_bound <= current_val <= upper_bound):
                filtered_series.iloc[idx] = np.nan
    
    return filtered_series


def rolling_diurnal_outlier(df_in: pd.DataFrame, filters_db_in, cfg_new: RollingDiurnalOutlierFilterConfig):
    if not cfg_new.enabled:
        return df_in, filters_db_in    
    
    # TODO 1 is copy meaningful? add proper filter for nee to plot it?
    df = df_in.copy() 
    filters_db = filters_db_in.copy()
    
    # TODO 1  preprocessing step ?
    # if 'TIMESTAMP_START_DATETIME' not in df.columns:
    #    raise ValueError(
    #        "Column 'TIMESTAMP_START_DATETIME' not found in df_selected. Please ensure preprocessing step is complete.")
        
    print(f"\nStarting rolling weekly window outlier cleaning ({cfg_new.window_size_days} days), "
          f"comparison with distribution for corresponding time of day (+/- {cfg_new.hour_tolerance} hours) "
          f"and median +/- {cfg_new.iqr_multiplier} IQR criterion:")
    
    for col in cfg_new.variables_to_filter:
        if col not in df.columns:
            ff_logger.info(f"Variable '{col}' is missing. Skipping rolling durinal filter for that variable.")
            continue
        
        initial_nan_count = df[col].isnull().sum()     
        # TODO 1 not yet a proper filter for nee, nee filters (and possibly others) should wark as mask
        df[col] = rolling_diurnal_outlier_filter_col(df, col, cfg_new)            
        filtered_count = df[col].isnull().sum() - initial_nan_count
        
        if filtered_count > 0:
            print(f"  Variable '{col}': Zeroed {filtered_count} outliers based on rolling weekly window and IQR.")
        else:
            print(f"  Variable '{col}': No outliers detected or no values to filter.")    
    
    print("\nRolling weekly window outlier filtering completed. First 5 rows of updated df_selected:")
    # display(df_in.head())

    return df, filters_db
