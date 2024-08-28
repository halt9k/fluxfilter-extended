# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# + [markdown] id="pqQVYpfkwA8E"
# # **FluxFilter**

# + [markdown] id="oE87fcFbwlIu"
# ## **Введение**
# Этот скрипт разработан для визуализации и фильтрации 30-минутных данных с вышек, работающих по методу турбулентных пульсаций (eddy covariance). Скрипт работает с данными об экосистемных потоках тепла и парниковых газов, а также 30-минутными метеорологическими данными. Иначе, это инструмент перевода данных из уровня 1 в уровни 2 и 3.
# * Под уровнем 1 подразумеваются потоки, как они рассчитаны EddyPro (LI-COR Inc., США) и "сырая" 30-минутная метеорология в том виде, как она записывается на регистраторы на вышках.
# * Под уровнем 2 подразумеваются незаполненные 30-минутные данные, ответственный за станцию исключает периоды заведомо плохой работы приборов (т.е. данные за эти периоды заполнены кодом пропуска -9999). Такие данные собираются для Информационно-Аналитической системы (ИАС, разработчик ИКИ РАН).
# * Под уровнем 3 подразумеваются данные уровня 2, также незаполненные, но прошедшие тщательную физическую, статистическую и (в случае надобности) визуальную фильтрацию.
#
# ## **Входные файлы**
# Форматы входных файлов: выходной файл EddyPro - full output (см. [мануал EddyPro](https://licor.app.boxenterprise.net/s/1ium2zmwm6hl36yz9bu4)) для потоков, а также biomet-файл EddyPro (см. [его же](https://licor.app.boxenterprise.net/s/1ium2zmwm6hl36yz9bu4)) для метеорологии. Турбулентные потоки и u* берутся из файла full output, а все метеорологические переменные (температура, относительная влажность и т.д.) берутся из файла biomet. Основные требования ко входным файлам:
# *   Файлы должны быть в формате .csv (текстовый файл, разделенный запятыми).
# *   Заголовки столбцов должны быть строго по руководству EddyPro, в скрипте переменные идентифицируются по названиям колонок (co2_flux для потока CO2 в full output, Ta_1_1_1 для температуры воздуха в biomet и т.д.).
# *   Код пропуска во входных файлах должен быть -9999
# *   Единицы для переменных файла biomet должны быть как основные единицы для файла biomet по руководству EddyPro. Исключение: температура воздуха/почвы должна быть в градусах Цельсия
# *   Файл-пример full output можно скачать [здесь](https://drive.google.com/file/d/1TyuHYZ0uh5teRiRFAga0XIqfU4vYW4-N/view?usp=sharing)
# *   Файл-пример biomet можно скачать [здесь](https://drive.google.com/file/d/1FjiBcSspDBlYlcg9Vzy71Sm49gOFZGBF/view?usp=sharing)
# *   В файле full output должны быть 3 строки заголовка и названия переменных должны быть записаны во 2-й строке
# *   В файле biomet должны быть 2 строки заголовка и названия переменных должны быть записаны во 2-й строке. По умолчанию без проблем читаются файлы, у которых дата и время записаны в колонке TIMESTAMP_1 в формате yyyy-mm-dd HHMM
#
# ## **Выходные файлы**
# Форматы выходных файлов:
# 1.   Файл базы данных ИАС уровня 2;
# 2.   Входной файл для инструмента фильтрации по u*, заполнения пропусков и разделения потоков [REddyProcWeb](https://www.bgc-jena.mpg.de/5624918/Input-Format) (Институт Макса Планка, Германия)
# 3. Входной файл для инструмента заполнения пропусков [Flux Analysis Tool](https://atmenv.envi.osakafu-u.ac.jp/staff/ueyama/softwares/) (M. Ueyama, Япония)
# 4. Basic - какие фильтры были применены, что получилось
# 5. Лог - записи в ходе работы скрипта, введенные для фильтрации параметры в данном пробеге
#
# ## **Загрузка входных файлов**
# *   загрузить на google-диск файлы full output и biomet,
# *   открыть к ним доступ
# *   в конфиге загрузки данных заменить названия входных файлов на импортируемые
# *   в конфиге загрузки данных проверить формат входных даты и времени
# *   скопировать часть публичной ссылки в раздел Загружаем данные в команду !gdown
#
# ## **Перед фильтрацией**
# *   Можно загружать несколько файлов full output и biomet, они будут автоматически расположены по возрастанию дат-времени и слиты в одну таблицу
# *   Осуществляется проверка меток времени для каждого входного файла (регуляризация)
# *   Рассчитываются VPD <-> RH, SWIN <-> RG <-> PAR в случае отсутствия
# *   Можно работать с потоком CO2 либо проверить данные о накоплении, прибавить их к потоку CO2 и работать с NEE
#
# ## **Как происходит фильтрация**
# Скрипт позволяет выявить и удалить некачественные и выбивающиеся значения с помощью  1) физической, 2) статистической  фильтрации, проходящей под визуальным контролем - с просмотром графиков до фильтраций и после.
# 1. Физическая фильтрация включает удаление плохих значений потоков с флагом EddyPro больше порогового, при уровне сигнала газоанализатора (CO2SS) ниже порогового значения, в дождь и после дождей, при высокой влажности, по ночным и дневным допустимым диапазонам.
# 2. Статистическая фильтрация включает удаление выбивающихся значений (outliers/spikes/выбросы/пики/спайки) с помощью фильтров по минимальным и максимальным допустимым значениям, по перцентилям, по отклонениям от среднего суточного хода в окне несколько дней, отклонениям от средних в скользящем окне на несколько точек MAD (Sachs, 2006) и HAMPEL (Pearson et al., 2016).
# 3. Опцию визуальной фильтрации данных (ручное удаление точек при просмотре графика) Google Colab не позволяет реализовать, но в версии для запуска в среде программирования визуальная фильтрация планируется.
# 4. Можно исключить данные по списку интервалов (исключить с ... - по ...), например, калибровки по журналу технических работ.
#
# (с)Евгений Курбатов, Вадим Мамкин, Ольга Куричева
#

# + [markdown] id="sj6Z0gnhVM-R"
# # Технический блок
# Импорт библиотек и определение функций

# + colab={"base_uri": "https://localhost:8080/", "height": 306} id="lZliIHxRJiqk" outputId="3ce11f32-87bd-4138-d0ee-cf431824a0ac"
from google.colab import userdata
key = userdata.get('registry_key')

# + id="E-a6ANTGBsqg"
# %pip install plotly-resampler dateparser
# %pip install --index-url https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.12

# + id="Ywv5kp0rzanK"
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pylab as plt
import os
from pandas.api.types import is_datetime64_any_dtype as is_datetime
import dateutil
from copy import deepcopy as copy

import plotly.io as pio
pio.renderers.default = "colab"
from IPython.display import display


from google.colab import output
output.enable_custom_widget_manager()

from plotly.subplots import make_subplots
import plotly.express as px
import plotly_resampler
import dateparser

import bglabutils.basic as bg
import bglabutils.filters as bf

import logging
import re
# import bglabutils.boosting as bb
# import textwrap
# %load_ext autoreload
# %autoreload 2

logging.basicConfig(level=logging.INFO, filename="/content/log.log", filemode="w", force=True)
logging.info("START")


# + [markdown] id="c_5uwjkzfk45"
# ## Функции для отрисовки

# + id="5AXOLjh5VeMp"
def colapse_filters(data, filters_db_in):
  out_filter = {}
  for feature, filters in filters_db_in.items():
    if len(filters)>0:
      out_filter[feature] = data[filters[0]].astype(int) if len(filters)==1 else np.logical_and.reduce((data[filters].astype(int)), axis=1).astype(int)
  return out_filter

def get_column_filter(data, filters_db_in, column_name):
  if column_name not in filters_db_in.keys():
    return np.array([1]*len(data.index))
  if len(filters_db_in[column_name]) > 0:
    return colapse_filters(data, filters_db_in)[column_name]
  else:
    return np.array([1]*len(data.index))

def basic_plot( data, col2plot, filters_db=None,  min_days=8, window_days = 10, steps_per_day=2*24, use_resample=False):

  multiplot = isinstance(col2plot, list)

  window_days = window_days   # дней в окне
  min_days = window_days//2 - 1
  pl_data = data.copy()

  layout = go.Layout(
      paper_bgcolor='rgba(0,0,0,0)',
      plot_bgcolor='rgba(0,0,0,0)'
  )
  color_data = 'darkorange'
  color_line = 'darkslateblue'

  add_color_data = copy(px.colors.qualitative.Pastel1)
  add_color_line = copy(px.colors.qualitative.Prism)

  add_color_data.insert(0, color_data)
  add_color_line.insert(0, color_line)

  fig = go.Figure(layout=layout)
  if multiplot:
    fig = make_subplots(rows=len(col2plot), cols=1, shared_xaxes=True, figure=fig, subplot_titles=[i.upper() for i in col2plot])
  else:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, figure=fig, row_heights=[.8, .2], subplot_titles=[col2plot.upper(), 'Residuals'])

  fig.update_xaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey', minor_ticks='inside', minor_tickcolor='Grey')
  fig.update_yaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey')
  # fig.update_layout(
  #     title = col2plot,
  #     xaxis_tickformat = '%H:%M %d %B <br>%Y'
  # )
  if not multiplot:
    cols = [col2plot]
  else:
    cols = col2plot

  fig.update_layout(
    # title = " ".join(cols),
    xaxis_tickformat = '%H:%M %d %B <br>%Y'
  )
  for row, col2plot in enumerate(cols):
    if filters_db is not None:
      filters =  get_column_filter(pl_data, filters_db, col2plot)
      pl_data.loc[~filters.astype(bool), col2plot] = np.nan

    if steps_per_day % 2 == 0:
      closed='left'
    else:
      closed='both'
    rolling_mean = bg.calc_rolling(pl_data[col2plot], step=steps_per_day, rolling_window=window_days, min_periods=min_days)

    fig.add_trace(go.Scattergl(x=pl_data.index, y=pl_data[col2plot], mode='markers', name=col2plot, marker_color=add_color_data[row]), row=row+1, col=1)
    fig.add_trace(go.Scattergl(x=rolling_mean.index, y=rolling_mean, mode='lines', name=f'{col2plot} mean {window_days} days', opacity=.7, line_color=add_color_line[row]), row=row+1, col=1)
    if not multiplot:
      fig.add_trace(go.Scattergl(x=rolling_mean.index, y=rolling_mean - pl_data[col2plot], mode='lines', name=f'residuals'), row=2, col=1)

  if use_resample:
    fig = plotly_resampler.FigureResampler(fig, default_n_shown_samples=5000)

  fig_config = {'toImageButtonOptions': {'filename': '_'.join(cols),}}
  fig.show(config=fig_config)



def plot_nice_year_hist_plotly(df, to_plot, time_col, filters_db):
    pl_data = df.copy()#[to_plot]
    if filters_db is not None:
      print()
      filters =  get_column_filter(df, filters_db, to_plot)
      pl_data['filter'] = filters
      pl_data.loc[~filters.astype(bool), to_plot] = np.nan
    # print(pl_data.loc[pd.to_datetime('26 June 2016 1:30'), ['nee', 'nee_nightFilter', 'swin_1_1_1', 'filter']].to_string())
    fig = go.Figure()
    fig.update_layout(title = f'{to_plot}')
    fig.add_trace(go.Heatmap(x=pl_data[time_col].dt.date, y=pl_data[time_col].dt.hour + 0.5*(pl_data[time_col].dt.minute//30), z=pl_data[to_plot]))
    fig_config = {'toImageButtonOptions': {'filename': f'{to_plot}',}}

    fig.show(config=fig_config)


def make_filtered_plot(data_pl, col, filters_db):
  data = data_pl.copy()
  layout = go.Layout(
      paper_bgcolor='rgba(0,0,0,0)',
      plot_bgcolor='rgba(0,0,0,0)'
  )
  add_color_dot = copy(px.colors.qualitative.Dark24)
  fig = go.Figure(layout=layout)
  fig.update_xaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey', minor_ticks='inside', minor_tickcolor='Grey')
  fig.update_yaxes(showline=True, linewidth=2, linecolor='black', gridcolor='Grey')

  data['full_filter'] =  get_column_filter (data, filters_db, col)
  data['full_filter'] = data['full_filter'].astype(int)
  pl_data = data.query(f"full_filter==0")
  color_ind = 0
  fig.add_trace(go.Scattergl(x=data.query("full_filter==1").index, y=data.query("full_filter==1")[col], mode='markers', name="Good data", marker_color=add_color_dot[color_ind] ))
  color_ind += 1

  if len(filters_db[col]) > 0:
    for filter_name in filters_db[col]:
      fig.add_trace(go.Scattergl(x=pl_data.query(f"{filter_name}==0").index, y=pl_data.query(f"{filter_name}==0")[col], mode='markers',   name=filter_name, marker_color=add_color_dot[color_ind]))
      color_ind += 1
      pl_data = pl_data.query(f"{filter_name}==1")

  fig.update_layout(
      title = f'{col2plot}',
      xaxis_tickformat = '%H:%M %d %B <br>%Y'
  )
  fig_config = {'toImageButtonOptions': {'filename': f'{col}',}}
  fig.show(config=fig_config)


def plot_albedo (plot_data, filters_db):
  pl_data = plot_data.copy()

  layout = go.Layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
    )


  if ('swin_1_1_1' not in pl_data.columns) or ('swout_1_1_1' not in pl_data.columns):
    print("No swin_1_1_1/sout_1_1_1")
    return 0
  pl_data['albedo'] = pl_data['swout_1_1_1'].div(pl_data['swin_1_1_1'])
  pl_data.loc[pl_data['swin_1_1_1']<=0, 'albedo'] = np.nan
  pl_data.loc[pl_data['swout_1_1_1']<=0, 'albedo'] = np.nan

  pl_ind  = pl_data[pl_data['albedo']<pl_data['albedo'].quantile(0.95)].index
  fig = go.Figure(layout=layout)
  fig.add_trace(go.Scattergl(x=pl_data.loc[pl_ind].index, y=pl_data.loc[pl_ind, 'albedo'], name="Albedo"))
  fig.update_layout(title = 'Albedo')
  fig_config = {'toImageButtonOptions': {'filename': 'albedo',}}
  fig.show(config=fig_config)


# + [markdown] id="PKznP_r1foao"
# ## Функции для фильтрации

# + id="EuUwWEPRaVT5"
def min_max_filter(data_in, filters_db_in, config):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    for col, limits in config.items():
      if col not in data.columns:
        print(f"No column with name {col}, skipping...")
        continue
      filter = get_column_filter(data, filters_db, col)

      if len(filter) == 0:
        filter = [1]*len(data.index)


      data[f"{col}_minmaxfilter"] = filter

      if col not in ['rh_1_1_1', 'sw_in_1_1_1', 'ppfd_1_1_1']:
        data.loc[data.query(f"{col}<{limits[0]}|{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0
      else:
        if col == 'rh_1_1_1':
          data[col] = data[col].clip(upper=limits[1])
          data.loc[data.query(f"{col}<{limits[0]}|{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0
        else:
          data[col] = data[col].clip(lower=limits[0])
          data.loc[data.query(f"{col}<{limits[0]}|{col}>{limits[1]}").index, f"{col}_minmaxfilter"] = 0

      if f"{col}_minmaxfilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_minmaxfilter")
      else:
        print("filter already exist but will be overwritten")
    logging.info(f"min_max_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def qc_filter(data_in, filters_db_in, config):
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col, limits in config.items():
      if col not in data.columns:
        print(f"No column with name {col}, skipping...")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      data[f"{col}_qcfilter"] = filter
      if f"qc_{col}" not in data.columns and col != 'nee':
        print(f"No qc_{col} in data")
        continue
      if col != 'nee':
        data.loc[data[f"qc_{col}"] > config[col], f"{col}_qcfilter"] = 0
      else:
        data.loc[data[f"qc_co2_flux"] > config['co2_flux'], f"nee_qcfilter"] = 0

    if f"{col}_qcfilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_qcfilter")
    else:
      print("filter already exist but will be overwritten")
    logging.info(f"qc_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def std_window_filter(data_in, filters_db_in, config):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    for col, lconfig in config.items():
      sigmas = lconfig['sigmas']
      window_size = lconfig['window']
      min_periods = lconfig['min_periods']#(window_size//2-1)
      points_per_day = lconfig['points_per_day']
      if col not in data.columns:
        print(f"No column with name {col}, skipping...")
        continue
      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      data[f"{col}_stdwindowfilter"] = filter
      data['tmp_col'] = data[col]
      data.loc[~filter.astype(bool), 'tmp_col'] = np.nan
      rolling_mean = bg.calc_rolling(data['tmp_col'], rolling_window=window_size, step=points_per_day, min_periods= min_periods)
      residuals = data['tmp_col'] - rolling_mean
      rolling_sigma = residuals.rolling(window=window_size * points_per_day, center=True, closed='both',  min_periods=window_size * points_per_day//2).std()
      data = data.drop(columns='tmp_col')
      # print(rolling_sigma, rolling_mean)
      upper_bound = rolling_mean + rolling_sigma * sigmas
      lower_bound = rolling_mean - rolling_sigma * sigmas
      upper_inds = upper_bound[upper_bound < data[col]].index
      lower_inds = lower_bound[lower_bound > data[col]].index
      data.loc[upper_inds , f"{col}_stdwindowfilter"] = 0
      data.loc[lower_inds , f"{col}_stdwindowfilter"] = 0
      # # print(len(lower_inds), len(upper_inds))
      # plt.plot(rolling_mean)
      # plt.title(col)
      # plt.show()

      if f"{col}_stdwindowfilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_stdwindowfilter")
      else:
        print("filter already exist but will be overwritten")
    logging.info(f"std_window_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_filter(data_in, filters_db_in, config, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    data = data_in.copy()
    filters_db = filters_db_in.copy()


    for col in ["co2_flux", 'h', 'le', 'ch4_flux']:

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_physFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_physFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_physFilter"] = filter

    if 'co2_signal_strength' in data.columns and 'CO2SS_min' in config.keys():
      data.loc[data['co2_signal_strength'] < config['CO2SS_min'], 'co2_flux_physFilter'] = 0
    else:
      print("No co2_signal_strength found")

    if 'ch4_signal_strength' in data.columns and 'CH4SS_min' in config.keys():
      data.loc[data['ch4_signal_strength'] < config['CH4SS_min'], 'ch4_flux_physFilter'] = 0
    else:
      print("No ch4_signal_strength found")

    if 'p_rain_limit' in config.keys():
      data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'co2_flux_physFilter'] = 0
      data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'h_physFilter'] = 0
      data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'le_physFilter'] = 0
      if 'rain_forward_flag' in config:
        rain_forward_flag = config['rain_forward_flag']
        for i in range(rain_forward_flag):
          ind = data.loc[data['p_rain_1_1_1'] >  config['p_rain_limit']].index.shift(i, freq=file_freq)
          data.loc[ind, 'co2_flux_physFilter'] = 0
          data.loc[ind, 'h_physFilter'] = 0
          data.loc[ind, 'le_physFilter'] = 0

    if 'RH_max' in config.keys():
      RH_max = config['RH_max']
      data.loc[data['rh_1_1_1']>RH_max, 'co2_flux_physFilter'] = 0
      data.loc[data['rh_1_1_1']>RH_max, 'le_physFilter'] = 0
    logging.info(f"meteorological_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def meteorological_rh_filter(data_in, filters_db_in, config, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["co2_flux", 'le', 'nee']:

      if col not in data.columns:
        print(f"no {col}")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_rhFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_rhFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_rhFilter"] = filter

    if 'RH_max' in config.keys():
      RH_max = config['RH_max']
      data.loc[data['rh_1_1_1']>RH_max, 'co2_flux_rhFilter'] = 0
      if 'nee' in data.columns:
        data.loc[data['rh_1_1_1']>RH_max, 'nee_rhFilter'] = 0
      data.loc[data['rh_1_1_1']>RH_max, 'le_rhFilter'] = 0
    logging.info(f"meteorological_rh_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_night_filter(data_in, filters_db_in, config, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    col_of_interest = ["h", 'le', 'nee', 'co2_flux']

    for col in col_of_interest:
      if col not in data.columns:
        print(f"no {col} column")
        continue
      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_nightFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_nightFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_nightFilter"] = filter

    if "nee" in data.columns:
      data_night_index = data.query("swin_1_1_1<10&nee<0").index
      data.loc[data_night_index, f"nee_nightFilter"] = 0

    if "co2_flux" in data.columns:
      data_night_index = data.query("swin_1_1_1<10&co2_flux<0").index
      data.loc[data_night_index, f"co2_flux_nightFilter"] = 0

    data_night_index = data.query(f"(h<{config['night_h_limits'][0]}|h>{config['night_h_limits'][1]})&swin_1_1_1<10").index
    data.loc[data_night_index, f"h_nightFilter"] = 0

    data_night_index = data.query(f"(h<{config['night_le_limits'][0]}|h>{config['night_le_limits'][1]})&swin_1_1_1<10").index
    data.loc[data_night_index, f"le_nightFilter"] = 0

    # if 'nee' in data.columns:
    #   data_night_index = data.query(f'nee>{config["day_nee_limit"]}&swin_1_1_1>=10').index
    #   data.loc[data_night_index, f"nee_nightFilter"] = 0
    logging.info(f"meteorological_night_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def meteorological_day_filter(data_in, filters_db_in, config, file_freq='30T'):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    col_of_interest = ['nee']

    for col in col_of_interest:
      if col not in data.columns:
        print(f"no {col} column")
        continue
      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_dayFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_dayFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_dayFilter"] = filter

    if 'nee' in data.columns:
      data_day_index = data.query(f'nee>{config["day_nee_limit"]}&swin_1_1_1>=10').index
      data.loc[data_day_index, f"nee_dayFilter"] = 0
    logging.info(f"meteorological_day_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def meteorological_co2ss_filter(data_in, filters_db_in, config, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    if 'CO2SS_min' not in config.keys():
      return data_in, filters_db_in

    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["co2_flux", 'nee']:

      if col not in data.columns:
        print(f"no {col} column")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_co2ssFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_co2ssFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_co2ssFilter"] = filter

    if 'co2_signal_strength' in data.columns:
      data.loc[data['co2_signal_strength'] < config['CO2SS_min'], 'co2_flux_co2ssFilter'] = 0
    else:
      print("No co2_signal_strength found")
    logging.info(f"meteorological_co2ss_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def meteorological_ch4ss_filter(data_in, filters_db_in, config, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    if 'CH4SS_min' not in config.keys():
      return data_in, filters_db_in

    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["ch4_flux"]:

      if col not in data.columns:
        print(f"no {col} column")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_ch4ssFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_ch4ssFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_ch4ssFilter"] = filter

    if 'ch4_signal_strength' in data.columns:
      data.loc[data['ch4_signal_strength'] < config['CH4SS_min'], 'ch4_flux_ch4ssFilter'] = 0
    else:
      print("No ch4_signal_strength found")
    logging.info(f"meteorological_coh4ss_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def meteorological_rain_filter(data_in, filters_db_in, config, file_freq='30T'):#,rain_forward_flag=3, p_rain_limit=.1,  filter_css=True):
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col in ["co2_flux", 'h', 'le', 'nee', "co2_flux"]:
      if col not in data.columns:
        print(f"no {col}")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_rainFilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_rainFilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_rainFilter"] = filter

    if 'p_rain_limit' in config.keys():
      data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'co2_flux_rainFilter'] = 0
      data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'h_rainFilter'] = 0
      data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'le_rainFilter'] = 0
      if 'nee' in data.columns:
        data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'nee_rainFilter'] = 0
      if 'ch4_flux' in data.columns:
        data.loc[data['p_rain_1_1_1'] > config['p_rain_limit'], 'ch4_flux_rainFilter'] = 0

      if 'rain_forward_flag' in config:
        rain_forward_flag = config['rain_forward_flag']
        for i in range(rain_forward_flag):
          ind = data.loc[data['p_rain_1_1_1'] >  config['p_rain_limit']].index.shift(i, freq=file_freq)
          if 'nee' in data.columns:
            data.loc[ind, 'nee_rainFilter'] = 0
          if 'ch4_flux' in data.columns:
            data.loc[ind, 'ch4_flux_rainFilter'] = 0
          data.loc[ind, 'co2_flux_rainFilter'] = 0
          data.loc[ind, 'h_rainFilter'] = 0
          data.loc[ind, 'le_rainFilter'] = 0
    logging.info(f"meteorological_rain_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def quantile_filter(data_in, filters_db_in, config):
    if len(config) == 0:
      return data_in, filters_db_in

    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col, limits in config.items():
      limit_down, limit_up = limits
      if col not in data.columns:
        print(f"No column with name {col}, skipping...")
        continue

      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_quantilefilter" not in filters_db[col]:
        filters_db[col].append(f"{col}_quantilefilter")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_quantilefilter"] = filter
      up_limit = data.loc[data[f'{col}_quantilefilter'] == 1, col].quantile(limit_up)
      down_limit = data.loc[data[f'{col}_quantilefilter'] == 1, col].quantile(limit_down)
      f_inds = data.query(f"{col}_quantilefilter==1").index
      print("Quantile filter cut values: ", down_limit, up_limit)
      # data.loc[f_inds, f'{col}_quantilefilter'] = ((data.loc[f_inds, col] <= up_limit) & (data.loc[f_inds, col] >= down_limit)).astype(int)
      data.loc[data[col] > up_limit, f'{col}_quantilefilter'] = 0
      data.loc[data[col] < down_limit, f'{col}_quantilefilter'] = 0

      # print(col, (data.loc[f_inds, col] < down_limit).sum(), (data.loc[f_inds, col] > up_limit).sum(), len(data.loc[f_inds, col].index), ((data.loc[f_inds, col] < up_limit) & (data.loc[f_inds, col] > down_limit)).astype(int).sum())
      # print(filter.sum(), data[f'{col}_quantilefilter'].sum(), filter.sum() - data[f'{col}_quantilefilter'].sum())
    logging.info(f"quantile_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def mad_hampel_filter(data_in, filters_db_in, config):
    if len(config) == 0:
      return data_in, filters_db_in
    data = data_in.copy()
    filters_db = filters_db_in.copy()

    for col, lconfig in config.items():
      if col not in data.columns:
        print(f"No column with name {col}, skipping...")
        continue

      hampel_window = lconfig['hampel_window']
      z = lconfig['z']
      filter = get_column_filter(data, filters_db, col)
      if len(filter) == 0:
        filter = [1]*len(data.index)

      if f"{col}_madhampel" not in filters_db[col]:
        filters_db[col].append(f"{col}_madhampel")
      else:
        print("filter already exist but will be overwritten")

      data[f"{col}_madhampel"] = filter

      # hampel_window = 20
      print(f"Processing {col}")
      outdata = bf.apply_hampel_after_mad(data.loc[data[f'{col}_madhampel']==1, :], [col], z=z, window_size=hampel_window)
      data.loc[data[f'{col}_madhampel']==1, f'{col}_madhampel'] = outdata[f'{col}_filtered'].astype(int)
      data[f"{col}_madhampel"] = data[f"{col}_madhampel"].astype(int)

    logging.info(f"mad_hampel_filter applied with the next config: \n {config}  \n")
    return data, filters_db

def manual_filter(data_in, filters_db_in, col_name, range, value ):
    data = data_in.copy()
    filters_db = filters_db_in.copy()
    filter = get_column_filter(data, filters_db, col_name)
    if len(filter) == 0:
      filter = [1]*len(data.index)
    data[f"{col_name}_manualFilter"] = filter
    # if range not in data.index:
    #   print('WARNING date range is not in index! Nothing is changed!')
    #   return data, filters_db
    try:
      data.loc[range, f"{col_name}_manualFilter"] = value
    except KeyError:
      print("ERROR! Check the date range!")
      return data, filters_db

    if f"{col_name}_manualFilter" not in filters_db[col_name]:
        filters_db[col_name].append(f"{col_name}_manualFilter")
    else:
      print("filter already exist but will be overwritten")
    logging.info(f"manual_filter applied with the next config: \n {config}  \n")
    return data, filters_db


def winter_filter(data_in, filters_db_in, config, date_ranges):
  data = data_in.copy()
  filters_db = filters_db_in.copy()
  if ('winter_nee_limits' not in config.keys()) and ('winter_ch4_flux_limits' not in config.keys()):
    return data, filters_db

  if 'winter_nee_limits' in config.keys():
      for col in ['nee', 'co2_flux']:
        if col not in data.columns:
          print(f"No column with name {col}, skipping...")
          continue

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
          filter = [1]*len(data.index)
        data[f"{col}_winterFilter"] = filter
        try:
          for start, stop  in date_ranges:
            range=pd.date_range(pd.to_datetime(start, dayfirst=True), pd.to_datetime(stop, dayfirst=True), freq='30min')
            inds_down = data.loc[range].query(f"{col}<{config['winter_nee_limits'][0]}").index
            inds_up = data.loc[range].query(f"{col}>{config['winter_nee_limits'][1]}").index
            data.loc[inds_up, f"{col}_winterFilter"] = 0
            data.loc[inds_down, f"{col}_winterFilter"] = 0
        except KeyError:
          print("ERROR! Check the date range!")
          return data, filters_db

        if f"{col}_winterFilter" not in filters_db[col]:
          filters_db[col].append(f"{col}_winterFilter")
        else:
          print("filter already exist but will be overwritten")

  if 'winter_ch4_flux_limits' in config.keys():
      for col in ['ch4_flux']:
        if col not in data.columns:
          print(f"No column with name {col}, skipping...")
          continue

        filter = get_column_filter(data, filters_db, col)
        if len(filter) == 0:
          filter = [1]*len(data.index)
        data[f"{col}_winterFilter"] = filter
        try:
          for start, stop  in date_ranges:
            range=pd.date_range(pd.to_datetime(start, dayfirst=True), pd.to_datetime(stop, dayfirst=True), freq='30min')
            inds_down = data.loc[range].query(f"{col}<{config['winter_ch4_flux_limits'][0]}").index
            inds_up = data.loc[range].query(f"{col}>{config['winter_ch4_flux_limits'][1]}").index
            data.loc[inds_up, f"{col}_winterFilter"] = 0
            data.loc[inds_down, f"{col}_winterFilter"] = 0
        except KeyError:
          print("ERROR! Check the date range!")
          return data, filters_db

        if f"{col}_winterFilter" not in filters_db[col]:
          filters_db[col].append(f"{col}_winterFilter")
        else:
          print("filter already exist but will be overwritten")

  logging.info(f"winter_filter applied with the next config: \n {config}  \n")
  return data, filters_db


# + [markdown] id="WfWRVITABzrz"
# #Формируем конфиг для загрузки и обработки данных
#

# + [markdown] id="ox0UplWMe7wn"
# ## Конфиг загрузки данных
# **Необходимо поменять:**
#
# `###Запишите название Ваших файлов и путь к ним.`
#
# В `config['path']` должен быть либо путь до файла (`= ['1.csv']`) при имени файла 1.csv, либо лист путей в случае загрузки нескольких файлов (`= ['1.csv', '2.csv']`). При импорте через !gdown файла с google-диска достаточно указать в одинарной кавычке *имя файла.расширение*. Не забывайте расширение .csv!
#
# **Необходимо проверить:**
#
# `  format = "%Y-%m-%d %H:%M"  #"%d/%m/%Y %H:%M"  #"%Y-%m-%d %H:%M:%S"`
#
# Проверьте порядок записи даты (год, месяц, день) и разделители даты-времени во входных файлах, открыв их в текстовом редакторе. Возможные варианты:
# 1.  Дата записана как 29.05.2024 и время как 12:00. Тогда они кодируются как
# "%d.%m.%Y %H:%M" – этот формат записан ниже по умолчанию, менять ничего не надо;
# 2.  Дата записана как 29/05/2024 и время как 12:00. Измените в строке ниже формат на "%d/%m/%Y %H:%M"
# 3.  Дата записана как 2024-05-29 и время как 1200. Измените в строке ниже формат на "%Y-%m-%d %H%M"
# 4.  В остальных случаях действуйте по аналогии. Если в графе time есть секунды, то формат кодируется как "%Y-%m-%d %H:%M:%S".
#
# **Дополнительные опции (без уровня PRO лучше не менять)**:
#
# В `config['time']['converter']` должна находиться функция, которая примет на входа DataFrame и на выходе вернет корректную колонку формата DateTime, которая будет использоваться как временная метка.
#
# `config['-9999_to_nan']` будучи установленным `True` заменит -9999 на np.nan для адекватной работы алгоритмов.
#
# `config['repair_time']` будучи установленным `True` - проверит колонку с датой-временем на пропуски и монотонность, проведет регенерацию по первой-последней точке с учетом предполагаемой длины шага (вычисляется по паре первых значений ряда).

# + [markdown] id="CXIuHMoSHMts"
# ## Конфиг загрузки файла full output

# + id="tVJ_DRBrlpYd"
config = {}
config['debug'] = False  # True загрузит небольшой кусок файла, а не целый
config['-9999_to_nan'] = True #заменяем -9999  на np.nan
config['repair_time'] = True #генерируем новые временные метки в случае ошибок

#####################
#на случай сложных колонок времени
config['time'] = {}
config['time']['column_name'] = 'datetime'
def my_datetime_converter(x):
    date = x['date'].astype(str) #x['date'].dt.strftime('%d.%m.%Y') if is_datetime(x['date'].dtype) else x['date'].astype(str)
    time = x['time'].astype(str) #x['time'].dt.strftime('%H:%M') if is_datetime(x['time'].dtype) else x['time'].astype(str)

    x['tmp_datetime'] = date + " " + time
    #Проверить формат даты-времени в FullOutput
    format = "%d.%m.%Y %H:%M"#"%d/%m/%Y %H:%M"# "%Y-%m-%d %H:%M"  #"%d/%m/%Y %H:%M"  #"%Y-%m-%d %H:%M:%S"
    return pd.to_datetime(x['tmp_datetime'], format=format)#dayfirst=True)#, format=format)
config['time']['converter'] = my_datetime_converter
#####################

###Запишите название Ваших файлов и путь к ним. Если файлы будут импортированы с google-диска
###через команду !gdown, то достаточно заменить название файла
config['path'] = ['eddy_pro result_SSB 2023.csv']#['eddypro_GHG_biomet_CO2SS_Express_full_output_2023-03-29T020107_exp.csv']#['eddypro_noHMP_full_output_2014_1-5.csv', 'eddypro_noHMP_full_output_2014_5-12.csv']#['/content/eddypro_NCT_GHG_22-23dry_full_output.xlsx', '/content/eddypro_NCT_GHG_22wet_full_output.xlsx', '/content/eddypro_NCT_GHG_23wet_full output.xlsx']#'/content/new.csv'
# config['path'] = '/content/DT_Full output.xlsx'

# + [markdown] id="S2Qc-fltJLaF"
# ## Конфиг загрузки файла biomet
# **Необходимо поменять:**
#
# `###Запишите название Ваших файлов и путь к ним.`
#
# В config['path'] должен быть либо путь до файла (= ['1.csv']) при имени файла 1.csv, либо лист путей в случае загрузки нескольких файлов (= ['1.csv', '2.csv']). При импорте через !gdown файла с google-диска достаточно указать в одинарной кавычке имя файла.расширение. Не забывайте расширение .csv!
#
# **Необходимо проверить:**
#
# `  format = "%Y-%m-%d %H%M"  #"%d.%m.%Y %H:%M"  #yyyy-mm-dd HHMM`
#
# Проверьте порядок записи даты (год, месяц, день) и разделители даты-времени во входных файлах, открыв их в текстовом редакторе. В биомет-файле по умолчанию дата записана как 2011-11-12 и время как 1200. Кодируется как "%Y-%m-%d %H%M". В других случаях поменяйте код формата дат-времени согласно инструкции для блока Конфиг загрузки файла full output

# + id="H7E5LGx1DVsA"
config_meteo = {}
config_meteo ['use_biomet'] = True
config_meteo['debug'] = False  # True загрузит небольшой кусок файла, а не целый
config_meteo['-9999_to_nan'] = True #заменяем -9999  на np.nan
config_meteo['repair_time'] = True #генерируем новые временные метки в случае ошибок

#####################
#на случай сложных колонок времени
config_meteo['time'] = {}
config_meteo['time']['column_name'] = 'datetime'
def my_datetime_converter(x):
    format = "%Y-%m-%d %H%M"  #"%d.%m.%Y %H:%M"  #yyyy-mm-dd HHMM
    return pd.to_datetime(x["TIMESTAMP_1"], format=format)
config_meteo['time']['converter'] = my_datetime_converter
#####################

###Запишите название Ваших файлов и путь к ним. Если файлы будут импортированы с google-диска
###через команду !gdown, то достаточно заменить название файла
config_meteo['path'] = 'BiometFy4_2023.csv'#'BiometFy4_2016.csv'#'BiometNCT_2011-22.csv'

# + [markdown] id="DtxFTNnEfENz"
# ## Выбор колонок для графиков и фильтраций

# + id="nLnivFTtg9cu"
#Соберем обзорную информацию о нужных величинах:
cols_to_investigate = []
cols_to_investigate.append("co2_flux")
cols_to_investigate.append("ch4_flux")
cols_to_investigate.append("LE")
cols_to_investigate.append("H")
cols_to_investigate.append("co2_strg")
cols_to_investigate.append("Ta_1_1_1")
cols_to_investigate.append("RH_1_1_1")
cols_to_investigate.append("VPD_1_1_1")
cols_to_investigate.append("P_1_1_1")
cols_to_investigate.append("SWIN_1_1_1")
cols_to_investigate.append("PPFD_1_1_1")
# cols_to_investigate.append("co2_signal_strength")
# cols_to_investigate.append("ch4_signal_strength")

cols_to_investigate =  [k.lower()for k in cols_to_investigate]

# + [markdown] id="wVpYvr9_fKBU"
# ## Настройка параметров анализа данных
#
# Все настройки для co2_flux будут применены для nee, в случае его расчета

# + [markdown] id="FH2uRGi4p5Zj"
# ### Фильтрация физическая

# + id="pPemVdWVbq2E"
points_per_day = 2*24
window_size = 10

file_freq = '30T'
calc_nee = True

ias_output_prefix = 'tv_fy4'
ias_output_version = 'v01'

# + [markdown] id="5MK90gyzQryZ"
# Конфиг фильтрации по флагам качества, данные с флагами в интервале (-inf, val] будут помечены как валидные, а данные с значением флага больше порога будут исключены.

# + id="ukl734CBblay"
qc_config = {}
qc_config['h'] = 1  #Если система флагов была 1-9, поправить
qc_config['le'] = 1  #Если система флагов была 1-9, поправить
qc_config['co2_flux'] = 1  #Если система флагов была 1-9, поправить
qc_config['ch4_flux'] = 1  #Если система флагов была 1-9, поправить

# + [markdown] id="QPIFpLN_-8Uf"
# Конфиг фильтрации по метеопараметрам, возможные опции:
#
# *   `CO2SS_min` - уберет co2_signal_strength ниже указанного значения
# *   `p_rain_limit` - уберет H, LE и CO2_FLUX для P_rain_1_1_1 выше указанного лимита
# *   `rain_forward_flag` - уберет  значения на указанное число записей вперед от каждого отфильтрованного на прошлом шаге значения
# *   `RH_max` - уберет значения LE и CO2_FLUX для которых RH_1_1_1 больше указанного порога
# * `day_nee_limit` порог для nee в дневное время (исключение положительных NEE днем)
# * `night_h_limits` `night_le_limits` допустимые ночные диапазоны LE и H
#
# Ночные (Swin<10)  NEE<0 исключаются
#
# При отсутствии в конфиге какого-либо из параметров фильтрация не применяется.
#
#
#
#
#
#

# + id="vxpiAbWk2yYr"
meteo_filter_config = {}
meteo_filter_config['CO2SS_min'] = 80.
meteo_filter_config['p_rain_limit'] = .1
meteo_filter_config['rain_forward_flag'] = 2
# meteo_filter_config['RH_max'] = 98 #нужно применять только тогда, когда нет CO2SS (образование конденсата) и диагностики анемометра
#и данные не были отфильтрованы по этим показателям на этапе расчета в EddyPro
meteo_filter_config['day_nee_limit'] = 5
meteo_filter_config['night_h_limits'] = [-50, 20]
meteo_filter_config['night_le_limits'] = [-50, 20]

meteo_filter_config['winter_nee_limits'] = [0, 5]
meteo_filter_config['winter_ch4_flux_limits'] = [-1, 1]

meteo_filter_config['CH4SS_min'] = 20.

# + [markdown] id="utUX7SA4qA_I"
# ### Фильтрация статистическая

# + id="6wFri3jhZeu3"



# + [markdown] id="wWISuF-xQCwq"
# Конфиг фильтрации по абсолютным значениям.
# Для `rh_1_1_1` значения выше границы не отбрасываются, а заменяются на пограничные. Для `ppfd_1_1_1`, `swin_1_1_1` аналогично обрабатываются минимальные значения.

# + id="HQfIYFOd9uzi"
min_max_config  = {}
min_max_config['co2_flux'] = [-40, 40]
min_max_config['co2_strg'] = [-20, 20]
min_max_config['h'] = [-100, 800]
min_max_config['le'] = [-100, 1000]
min_max_config['u_star'] = [0, 10]
min_max_config['ta_1_1_1'] = [-50, 50]
min_max_config['p_1_1_1'] = [0, 100]
min_max_config['vpd_1_1_1'] = [0, 50]
min_max_config['rh_1_1_1'] = [0, 100]#max
min_max_config['swin_1_1_1'] = [0, 1200]#min
min_max_config['ppfd_1_1_1'] = [0, 2400]#min
min_max_config['ch4_flux'] = [-10, 10]

# + [markdown] id="vmyTKbV1RdjD"
# Конфиг фильтрации по отклонению от среднего хода.
# * `window` - размер окна в днях для подсчета среднего хода
# * `points_per_day` - число измерений в сутках
# * `sigmas` - допустимый интервал отклонения от среднего хода; вне интервала значения помечаются как отфильтрованные

# + id="xfRVNYbFYzG3"
window_filter_config = {}
window_filter_config['co2_flux'] = {'sigmas': 2, 'window': 10, 'points_per_day': points_per_day, 'min_periods': 4}
window_filter_config['ch4_flux'] = {'sigmas': 2, 'window': 10, 'points_per_day': points_per_day, 'min_periods': 4}
window_filter_config['ta_1_1_1'] = {'sigmas': 2, 'window': 10, 'points_per_day': points_per_day, 'min_periods': 4}
window_filter_config['u_star'] = {'sigmas': 2, 'window': 10, 'points_per_day': points_per_day, 'min_periods': 4}
for col in ['h', 'le', 'rh_1_1_1', 'vpd_1_1_1']:
  window_filter_config[col] = {'sigmas': 4, 'window': 10, 'points_per_day': points_per_day, 'min_periods': 4}
for col in ['swin_1_1_1', 'ppfd_1_1_1']:
  window_filter_config[col] = {'sigmas': 4, 'window': 10, 'points_per_day': points_per_day, 'min_periods': 4}

# + [markdown] id="KF_MGD7pSGre"
# Конфиг фильтрации выше-ниже порога по перцентилям (выпадающие строки отфильтровываются)

# + id="asO_t2tZmiD0"
quantile_filter_config = {}
quantile_filter_config['co2_flux'] = [0.01, 0.99]
quantile_filter_config['ch4_flux'] = [0.01, 0.99]
quantile_filter_config['co2_strg'] = [0.01, 0.99]

# + [markdown] id="cPiTN288UaP3"
# Конфиг для статистической фильтрации.

# + id="2b3eBVFUq3AU"
# madhampel_filter_config = {i:{'z': 5.5, 'hampel_window': 10} for i in cols_to_investigate if 'p_1_1_1' not in i}
madhampel_filter_config = {}
madhampel_filter_config['co2_flux'] = {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config['ch4_flux'] = {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config['le'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config['h'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config['co2_strg'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config[ 'ta_1_1_1'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config[ 'rh_1_1_1'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config[ 'vpd_1_1_1'] =  {'z': 5.5, 'hampel_window': 10}
madhampel_filter_config[ 'swin_1_1_1'] =  {'z': 7.0, 'hampel_window': 10}
madhampel_filter_config[ 'ppfd_1_1_1'] =  {'z': 7.0, 'hampel_window': 10}

# + [markdown] id="wVF1vDm4EauW"
# # Загружаем данные

# + [markdown] id="LV9FvvtnVqdN"
# **Необходимо поменять:**
#
# После !gdown вставьте символы после d/ и до следующего / из публичной ссылки на файл, лежащий на google-диске. К примеру, если ссылка
# https://drive.google.com/file/d/1fGhmvra0evNzM0xkM2nu5T-N_rSPoXUB/view?usp=sharing,
# то команда будет записана как
# `!gdown 1fGhmvra0evNzM0xkM2nu5T-N_rSPoXUB`
#
# `#Загрузка файла full output`
# Здесь нужно прописать символы из ссылки на файл full output
#
# `#Загрузка файла biomet`
# Здесь нужно прописать символы из ссылки на файл biomet

# + id="KMu4IqY45HG6"
# # # !gdown https://docs.google.com/spreadsheets/d/1Xb3hKpL0vZEfa8ZfSlQE78Jn41gEekfvJtFnKAcotMA/export?format=csv -O new.csv
# # # !gdown 1-e8Bx9UXj_yZxlPamb6s80YriIEWcL_i

#Загрузка файла full output
#https://drive.google.com/file/d/1fGhmvra0evNzM0xkM2nu5T-N_rSPoXUB/view?usp=sharing
# # !gdown 1fGhmvra0evNzM0xkM2nu5T-N_rSPoXUB
# !gdown 1CGJmXyFu_pmzTLitG5aU8fwY8gW3CI1n

#Загрузка файла biomet
#https://drive.google.com/file/d/1FjiBcSspDBlYlcg9Vzy71Sm49gOFZGBF/view?usp=sharing
# # !gdown 1FjiBcSspDBlYlcg9Vzy71Sm49gOFZGBF
# !gdown 19XsOw5rRJMVMyG1ntRpibfkUpRAP2H4k

# + id="Xw5TapK10EhR"
data, time = bg.load_df(config)
data = data[next(iter(data))]  #т.к. изначально у нас словарь

# + [markdown] id="6j7ombDYqyC8"
# Проверяем корректность временных меток. Убираем повторы, дополняем пропуски. На случай загрузки нескольких файлов. При загрузке одного делается автоматически.

# + id="FWCJ-EVrjnH3"
correct_number_of_time_entries = pd.date_range(data[time].iloc[0], data[time].iloc[-1],
                                                freq=data[time].iloc[1] - data[time].iloc[0])
if not correct_number_of_time_entries.size == len(data.index):
    if correct_number_of_time_entries.size < len(data.index):
      print('Removing duplicates')
      data = data[~data.index.duplicated(keep='first')]
    else:
      print("Adding missed timestamps")
      dates = pd.date_range(data.index.min(), data.index.max())
      data = data.reindex(dates, fill_value=np.nan)
data.index = pd.DatetimeIndex(data.index, freq="30T")
print("Диапазон времени full_output: ", data.index[[0, -1]])
logging.info(f"Data loaded from {config['path']}")
logging.info("Time range for full_output: "+ " - ".join(data.index[[0,-1]].strftime('%Y-%m-%d %H:%M')))

# + id="65DLIIucNOPe"
if config_meteo ['use_biomet']:
  data_meteo, time_meteo  = bg.load_df(config_meteo)
  data_meteo = data_meteo[next(iter(data_meteo))]  #т.к. изначально у нас словарь
  print("Диапазон времени метео: ", data_meteo.index[[0, -1]])
  logging.info(f"MeteoData loaded from {config_meteo['path']}")
  logging.info("Time range for meteo: "+ " - ".join(data_meteo.index[[0,-1]].strftime('%Y-%m-%d %H:%M')))

# + id="rZbqd6adhHEP"
print("Колонки в FullOutput \n", data.columns.to_list())
if config_meteo ['use_biomet']:
  print("Колонки в метео \n", data_meteo.columns.to_list())

# + [markdown] id="FF78Wlq9rD_n"
# Сливаем в один DataFrame.

# + id="9v0rxHehhZEI"
if config_meteo ['use_biomet']:
  data = data.join(data_meteo, how='left', rsuffix='_meteo')
  if data[data_meteo.columns[-1]].isna().sum() == len(data.index):
    print("Bad meteo data range, skipping! Setting config_meteo ['use_biomet']=False")
    config_meteo ['use_biomet'] = False

# + id="C8lLDYOWzH2d"
data.columns= data.columns.str.lower()

# + [markdown] id="QDHkyl_PruXE"
# # Предобработка

# + [markdown] id="Nh5MosYXS6aj"
# Переименовываем колонки для единого формата, рассчитываем VPD <-> RH, SWIN <-> RG и PAR <-> SWIN в случае отсутствия.
#

# + id="mAdYXJFdSRbJ"
have_rh_flag = False
have_vpd_flag = False
have_par_flag = False
have_swin_flag = False
have_rg_flag = False
have_p_flag = False
have_pr_flag = False
have_ppfd_flag = False

for col_name in data.columns:
  if 'u*' in col_name:
    print(f"renaming {col_name} to u_star")
    data = data.rename(columns={col_name: 'u_star'})
  if 'ppfd_in_1_1_1' in col_name:
    print(f"renaming {col_name} to ppfd_1_1_1")
    data = data.rename(columns={col_name: 'ppfd_1_1_1'})
  if 'sw_in_1_1_1' in col_name:
    print(f"renaming {col_name} to swin_1_1_1")
    data = data.rename(columns={col_name: 'swin_1_1_1'})
  if 'co2_signal_strength' in col_name:
    print(f"renaming {col_name} to co2_signal_strength")
    data = data.rename(columns={col_name: 'co2_signal_strength'})
  if "rh_1_1_1" in col_name:
    have_rh_flag =True
  if "vpd_1_1_1" in col_name:
    have_vpd_flag = True
  if 'swin' in col_name or 'sw_in' in col_name:
    have_swin_flag = True
  if 'par' in col_name:
    have_par_flag = True
  if 'rg_1_1_1' in col_name:
    have_rg_flag = True
  if 'p_1_1_1' in col_name:
    have_p_flag = True
  if 'p_rain_1_1_1' in col_name:
    have_pr_flag = True
  if 'ppfd_1_1_1' in col_name:
    have_ppfd_flag = True
  if col_name in ['co2_signal_strength_7500_mean', 'CO2SS'.lower()] or 'co2_signal_strength' in col_name:
    print(f"renaming {col_name} to co2_signal_strength")
    data = data.rename(columns={col_name: 'co2_signal_strength'})
  if col_name in ['ch4_signal_strength_7700_mean', 'CH4SS'.lower()] or 'ch4_signal_strength' in col_name:
    print(f"renaming {col_name} to ch4_signal_strength")
    data = data.rename(columns={col_name: 'ch4_signal_strength'})

if not (have_rg_flag or have_swin_flag):
  print("NO RG AND SWIN")
else:
  print("Checking RG-SWIN pair")
  if not have_rg_flag:
    data['rg_1_1_1'] = data['swin_1_1_1']
  if not have_swin_flag:
    data['swin_1_1_1'] = data['rg_1_1_1']
    have_swin_flag = True


if not (have_p_flag or have_pr_flag):
  print("NO P and P_RAIN")
else:
  print("Checking P <-> P_rain pair")
  if not have_p_flag:
    data['p_1_1_1'] = data['p_rain_1_1_1']
  if not have_pr_flag:
    data['p_rain_1_1_1'] = data['p_1_1_1']


if not (have_vpd_flag or have_rh_flag):
  print("NO RH AND VPD")
else:
    temp_k = (data['ta_1_1_1'] + 273.15)
    logE = 23.5518-(2937.4/temp_k)-4.9283*np.log10(temp_k)
    ehpa = np.power(10, logE)
    if not have_vpd_flag:
      print("calculating vpd_1_1_1 from rh")
      data['vpd_1_1_1'] = ehpa - (ehpa*data['rh_1_1_1']/100)
    if not have_rh_flag:
      print("calculating rh_1_1_1 from vpd")
      data['rh_1_1_1'] = ehpa


if not (have_par_flag or have_swin_flag):
  print("NO PAR and SWin")
else:
    if not have_par_flag:
      data['par'] = data['swin_1_1_1'] / 0.47#SWin=PAR*0.47
    if not have_swin_flag:
      data['swin_1_1_1'] = 0.47 * data['par']

if not (have_ppfd_flag or have_swin_flag):
  print("NO PPFD and SWin")
else:
    if not have_ppfd_flag:
      data['ppfd_1_1_1'] = data['swin_1_1_1'] / 0.47
    if not have_swin_flag:
      data['swin_1_1_1'] = 0.47 * data['ppfd_1_1_1']

for col_name in ['co2_signal_strength_7500_mean', 'CO2SS'.lower()]:
  # print(data.columns.to_list())
  if col_name in data.columns.to_list():
    print(f"renaming {col_name} to co2_signal_strength")
    data = data.rename(columns={col_name: 'co2_signal_strength'})

for col_name in ['ch4_signal_strength_7700_mean', 'CH4SS'.lower()]:
  # print(data.columns.to_list())
  if col_name in data.columns.to_list():
    print(f"renaming {col_name} to ch4_signal_strength")
    data = data.rename(columns={col_name: 'ch4_signal_strength'})


# + [markdown] id="soyyX-MCbaXt"
# ## Получение NEE из потока CO2 и накопления

# + [markdown] id="lqWwGSMObro4"
# Проверка накопления. Рассчитанное по одному уровню в EddyPro не всегда корректно. Корректность проверяется суточным ходом: должен быть рост запаса в течение ночи, резкое уменьшение утром.

# + [markdown] id="2yqwO7Uhcjmz"
# Фильтрация co2_strg с удалением значений выше и ниже пороговых перцентилей. Заполнение пропусков co2_strg  длиной 3 точки и менее – линейной интерполяцией. Полученные отфильтрованные и заполненные значения co2_strg показываются на графике. Принятие решения, суммировать ли co2_flux и co2_strg для получения NEE или работать дальше с co2_flux.

# + id="cjt05XXtbr69"
#Пробелы длиной 3 и меньше заполняются линейно
if calc_nee and 'co2_strg' in data.columns:
  tmp_data = data.copy()
  tmp_data['co2_strg_tmp'] = tmp_data['co2_strg'].copy()
  tmp_filter_db =  {'co2_strg_tmp': []}
  if 'co2_strg' in  quantile_filter_config.keys():
    tmp_q_config = {'co2_strg_tmp':quantile_filter_config['co2_strg']}
  else:
    tmp_q_config = {}
  tmp_filter_db = {'co2_strg_tmp':[]}
  tmp_data, tmp_filter_db = quantile_filter(tmp_data, tmp_filter_db, tmp_q_config)
  tmp_data.loc[~get_column_filter(tmp_data, tmp_filter_db, 'co2_strg_tmp').astype(bool), 'co2_strg_tmp'] = np.nan
  # tmp_data['co2_strg_tmp'] = tmp_data['co2_strg_tmp'].interpolate(limit=3)
  # tmp_data['co2_strg_tmp'].fillna(bg.calc_rolling(tmp_data['co2_strg_tmp'], rolling_window=10 , step=24 * 2, min_periods=4))
  basic_plot(tmp_data, ['co2_strg_tmp'], tmp_filter_db)
  print(tmp_q_config, tmp_filter_db, tmp_data['co2_strg_tmp_quantilefilter'].value_counts())


# + id="2IQ7W6pslYF-"
#Решаем, суммировать ли исходный co2_flux и co2_strg_filtered_filled для получения NEE
calc_with_strg = True   #В случае, если дальше работаем с NEE, оставить True.
logging.info(f"calc_with_strg is set to {calc_with_strg}")
#Для того, чтобы работать дальше с co2_flux, игнорируя co2_strg, поставить False

# + id="ueuvsNxYdtgs"
if calc_nee and 'co2_strg' in data.columns:
  if calc_with_strg:
    data['nee'] = (tmp_data['co2_flux'] + tmp_data['co2_strg_tmp']).copy()
  else:
    data['nee'] = data['co2_flux'].copy()
  del tmp_data
  if 'nee' not in cols_to_investigate:
    cols_to_investigate.append('nee')
  for filter_config in [qc_config, meteo_filter_config, min_max_config, window_filter_config, quantile_filter_config, madhampel_filter_config]:
    if 'co2_flux' in filter_config:
      filter_config['nee'] = filter_config['co2_flux']

# + [markdown] id="mUgwuaFYribB"
# #Обзор статистики по интересующим колонкам

# + id="dhcplCMbXtkK"
cols_to_investigate = [p for p in cols_to_investigate if p in data.columns]

# + id="YfusqiotOi3n"
data.loc[:, cols_to_investigate].describe()

fig, axs = plt.subplots(ncols=min(3, len(cols_to_investigate)), nrows=int(np.ceil(len(cols_to_investigate)/3)), squeeze=False, figsize=(13, 8))

for ind, ax in enumerate(axs.reshape(-1)):
  if ind >= len(cols_to_investigate):
    break
  feature = cols_to_investigate[ind]
  ax.boxplot(data[feature].to_numpy()[~np.isnan(data[feature].to_numpy())])
  ax.set_title(f"Boxplot for {feature}")
plt.tight_layout()
fig.show()

data[cols_to_investigate].describe()

# + [markdown] id="0oJLXYGbr93S"
# #Фильтрация данных физическая

# + id="apGNk8eBxgBv"
plot_data = data.copy()
filters_db = {col: [] for col in plot_data.columns.to_list()}
print(plot_data.columns.to_list())

# + [markdown] id="BL_6XxGGsCBK"
# ## по флагам качества

# + id="GGwe7_uU1C8U"
unroll_filters_db = filters_db.copy()
plot_data, filters_db = qc_filter(plot_data, filters_db, qc_config)

# + [markdown] id="M_gKSTNYyzjS"
# ## по порогу CO2SS и CH4SS

# + id="viq7BZue9Ett"
unroll_filters_db = filters_db.copy()
plot_data, filters_db = meteorological_co2ss_filter(plot_data, filters_db, meteo_filter_config)

# + id="5RrPfxfiJGhN"
unroll_filters_db = filters_db.copy()
plot_data, filters_db = meteorological_ch4ss_filter(plot_data, filters_db, meteo_filter_config)

# + [markdown] id="qwqVDeH6y73_"
# ## по допустимым значениям RH

# + id="11isfvNZ9FGu"
unroll_filters_db = filters_db.copy()
plot_data, filters_db = meteorological_rh_filter(plot_data, filters_db, meteo_filter_config)

# + [markdown] id="oSX2h9QzzFkT"
# ## по наличию дождя

# + id="jz696mc09FlB"
if config_meteo ['use_biomet']:
  unroll_filters_db = filters_db.copy()
  plot_data, filters_db = meteorological_rain_filter(plot_data, filters_db, meteo_filter_config)

# + [markdown] id="Xy2y00P1zJtZ"
# ## по ночным и дневным допустимым диапазонам

# + id="ED_Qh6TS0Qkc"
if config_meteo ['use_biomet']:
  unroll_filters_db = filters_db.copy()
  plot_data, filters_db = meteorological_night_filter(plot_data, filters_db, meteo_filter_config)

# + id="X3Vguu8MK635"
if config_meteo ['use_biomet']:
  unroll_filters_db = filters_db.copy()
  plot_data, filters_db = meteorological_day_filter(plot_data, filters_db, meteo_filter_config)

# + [markdown] id="fzfTJdNe68Eu"
# ## фильтрация зимних периодов, уточните даты!

# + id="wJ87D57S7A91"
if ('winter_nee_limits' in meteo_filter_config.keys()) or ('winter_ch4_flux_limits' in meteo_filter_config.keys()):
  plot_albedo(plot_data, filters_db)

# + id="Z_RAYINf67PO"
if config_meteo ['use_biomet']:
  unroll_filters_db = filters_db.copy()
  date_ranges = [
      ['01.01.2023 00:00', '26.03.2023 00:00'],
      ['13.11.2023 00:00', '31.12.2023 00:00'],
  ]
  #date_ranges = []
  # date_ranges.append(['25.8.2014 00:00', '26.8.2014 00:00'])
  plot_data, filters_db = winter_filter(plot_data, filters_db, meteo_filter_config, date_ranges)


# + [markdown] id="iipFLxf6fu5Y"
# Фильтрация по футпринту
# будет в следующей версии скрипта
#
# `fetch = 1 #или 0. 1 – остаются, 0 – убираются `

# + [markdown] id="UAdRtCPGq6_y"
# # Фильтрация данных статистическая

# + [markdown] id="LcwZplknsHJv"
# ## по минимальным и максимальным допустимым значениям

# + id="FyJaM1zC1DDg"
# if config_meteo ['use_biomet']:
unroll_filters_db = filters_db.copy()
plot_data, filters_db = min_max_filter(plot_data, filters_db, min_max_config)

# + [markdown] id="j62U1dw8sTEm"
# ## по перцентилям

# + id="aNQ4XDK01DME"
# if config_meteo ['use_biomet']:
unroll_filters_db = filters_db.copy()
plot_data, filters_db = quantile_filter(plot_data, filters_db, quantile_filter_config)

# + [markdown] id="7Sg76Bwasnb4"
# ## по отклонению от среднего хода

# + id="uoDvHhoQ2MMe"
unroll_filters_db = filters_db.copy()
plot_data, filters_db = std_window_filter(plot_data, filters_db, window_filter_config)

# + [markdown] id="iXl5RdINss9D"
# ## Фильтрация выбросов MAD & Hampel

# + id="gl9cImVr2MO3"
unroll_filters_db = filters_db.copy()
plot_data, tmp_filter = mad_hampel_filter(plot_data, filters_db, madhampel_filter_config)

# + [markdown] id="iu8MLKyh1AFk"
# ## Ручная фильтрация
#
# 1- оставить,
# 0 -удалить
#

# + id="ADy534At0_fN"
man_ranges = [
    ['1.5.2023 00:00', '1.6.2023 00:00'],
    # ['25.8.2015 00:00', '26.8.2015 00:00'],
]
for start, stop in man_ranges:
  plot_data, tmp_filter = manual_filter(plot_data, filters_db, col_name="nee", range=pd.date_range(pd.to_datetime(start, dayfirst=True), pd.to_datetime(stop, dayfirst=True), freq='30min'), value=0)

# + [markdown] id="APyqyqSEHx3K"
# ## На случай необходимости откатить последний фильтр
# Не работает с повторно-запущенными несколько раз

# + id="IYmSC2gpH4zo"
#filters_db = unroll_filters_db.copy()

# + [markdown] id="quGbtDaJ_gID"
# ## Сводная таблица результатов фильтрации

# + id="Pg78qGJ9_miW"
all_filters = {}
for key, filters in filters_db.items():
   if len(filters) > 0:
    pl_data = plot_data.copy()
    for filter_name in filters:
      all_filters[filter_name] = []
      all_filters[filter_name].append(len(pl_data.index))
      filtered_amount = len(pl_data.query(f"{filter_name}==0").index)
      all_filters[filter_name].append(filtered_amount)
      # old_val =  len(pl_data.index)
      pl_data = pl_data.query(f"{filter_name}==1")
      # print(filter_name, filtered_amount, len(pl_data.index) - old_val)
fdf_df = pd.DataFrame(all_filters)
print("Какая часть данных от общего количества (в %) была отфильтрована:")
print(fdf_df.iloc[1]/len(plot_data)*100)
logging.info("Какая часть данных от общего количества (в %) была отфильтрована:")
logging.info(fdf_df.iloc[1]/len(plot_data)*100)

# + [markdown] id="gA_IPavss0bq"
# # Отрисовка рядов

# + [markdown] id="ijPM6mnJtMv8"
# ## Отрисовка результатов фильтрации данных

# + id="50Xhczc-BRc2"
plot_terator = iter(cols_to_investigate)

# + [markdown] id="uat4oESzU4__"
# Для экономии памяти и адекватной работы колаба графики будут выводиться поочередно при повторном запуске ячейки.

# + id="NhNoFAd7DqNN"
col2plot = next(plot_terator, False)
col2plot = 'nee' #Подставить нужное: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1, co2_signal_strength
#Или просто запускать повторно для переключения к следующему параметру
if col2plot:
  make_filtered_plot(plot_data, col2plot, filters_db)
else:
  print("No more data, start from the begining!")
  plot_terator = iter(cols_to_investigate)

# + id="ZG_wF2qW-Qwb"
# #линейное заполнение пропусков, limit - сколько может быть пропущенных подряд
# for col in cols_to_investigate:
#   plot_data[col] = plot_data[col].interpolate(limit=5)

# + id="VtJ8wyx2-XCX"
# #Заполнение ходом
# for col in cols_to_investigate:
#   plot_data[col].fillna(bg.calc_rolling(plot_data[col], rolling_window=10 * 2 * 24, step=24 * 2, min_periods=7*2*24))

# + [markdown] id="MwuXRVTMtBz2"
# ## Отрисовка среднего хода для отфильтрованных рядов

# + id="pWDTiucTgRlI"
plot_terator = iter(cols_to_investigate)

# + id="COKiwe7020D4"
#Пример вычисления среднего хода

col2plot = next(plot_terator, False)
#Можно задать вручную
# col2plot = 'h'#"co2_flux"
col2plot = ['nee', 'le'] #Подставить нужное: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1
#Или просто запускать повторно для переключения к следующему параметру
if col2plot:
  basic_plot(plot_data, col2plot, filters_db)
else:
  print("No more data, start from the begining!")
  plot_terator = iter(cols_to_investigate)

# + [markdown] id="RKEg6YBstXMp"
# ## Тепловые карты потоков для отфильтрованных данных

# + id="mCUJYURKEL-f"
for col in ['nee', 'le', 'h']: #Подставить нужное: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1
#Или просто запускать повторно для переключения к следующему параметру
  plot_nice_year_hist_plotly(plot_data, col ,time, filters_db)


# + [markdown] id="dokSxicNtdva"
# # Сохранение данных в формате REddyProc

# + [markdown] id="tDqsi61kSeak"
# Создадим шаблон шапки для файла REddyProc и сохраним требуемые переменные, не забыв учесть фильтрацию.

# + id="YVu2UrCzLqb4"
reddyproc_filename = "REddyProc.txt"
output_template = {'Year': ['-'],	'DoY': ['-'],	'Hour': ['-'],	'NEE': ['umolm-2s-1'],	'LE': ['Wm-2'],	'H': ['Wm-2'],	'Rg': ['Wm-2'],	'Tair': ['degC'], 	'Tsoil': ['degC'],	'rH': ['%'], 	'VPD': ['hPa'], 	'Ustar': ['ms-1']}

# + id="GFulh7FtNWtM"
if config_meteo ['use_biomet']:
  eddy_df = plot_data.copy()

  for column, filter in filters_db.items():
    filter = get_column_filter(eddy_df, filters_db, column)
    eddy_df.loc[~filter.astype(bool), column] = np.nan


  eddy_df['Year'] = eddy_df[time].dt.year
  eddy_df['DoY'] = eddy_df[time].dt.dayofyear
  eddy_df['Hour'] = eddy_df[time].dt.hour + eddy_df[time].dt.minute/60

  eddy_df['NEE'] = eddy_df['nee'].fillna(-9999)
  eddy_df['LE'] = eddy_df['le'].fillna(-9999)
  eddy_df['H'] = eddy_df['h'].fillna(-9999)
  eddy_df['Rg'] = eddy_df['rg_1_1_1'].fillna(-9999)
  eddy_df['Tair'] = eddy_df['ta_1_1_1'].fillna(-9999)
  if 'ts_1_1_1' in eddy_df.columns:
    eddy_df['Tsoil'] = eddy_df['ts_1_1_1'].fillna(-9999)
  eddy_df['rH'] = eddy_df['rh_1_1_1'].fillna(-9999)
  eddy_df['VPD'] = eddy_df['vpd_1_1_1'].fillna(-9999)
  eddy_df['Ustar'] = eddy_df['u_star'].fillna(-9999)

  i=0
  while eddy_df.iloc[i]['Hour'] != 0.5:
    i += 1
  eddy_df = eddy_df.iloc[i:]

  if len(eddy_df.index) < 90 * points_per_day:
    print("WARNING!  < 90 days in reddyproc file!")
  pd.DataFrame({key: item for key, item in output_template.items() if key in eddy_df.columns}).to_csv(reddyproc_filename, index=False, sep=' ')
  eddy_df.to_csv(reddyproc_filename,  index=False, header=False, columns = [i for i in output_template.keys()  if i in eddy_df.columns], mode='a', sep=' ')
  del eddy_df
  logging.info(f"REddyProc file saved to {reddyproc_filename}")

# + [markdown] id="62o5-p8ZzR5T"
# # Сохранение данных ИАС

# + id="yaLoIQmtzaYd"
if config_meteo ['use_biomet']:
	ias_df = plot_data.copy()
	for column, filter in filters_db.items():
		filter = get_column_filter(ias_df, filters_db, column)
		ias_df.loc[~filter.astype(bool), column] = np.nan
	ias_df = ias_df.fillna(-9999)

	col_match =  {"co2_flux" : "FC_1_1_1", "qc_co2_flux" : "FC_SSITC_TEST_1_1_1", "LE" : "LE_1_1_1",
		"qc_LE" : "LE_SSITC_TEST_1_1_1", "H" : "H_1_1_1", "qc_H" : "H_SSITC_TEST_1_1_1", "Tau" : "TAU_1_1_1",
		"qc_Tau" : "TAU_SSITC_TEST_1_1_1", "co2_strg" : "SC_1_1_1", "co2_mole_fraction" : "CO2_1_1_1",
		"h2o_mole_fraction" : "H2O_1_1_1", "sonic_temperature" : "T_SONIC_1_1_1", "u*" : "USTAR_1_1_1",
		"Ta_1_1_1" : "TA_1_1_1", "Pa_1_1_1" : "PA_1_1_1", "Swin_1_1_1" : "SW_IN_1_1_1", "Swout_1_1_1" : "SW_OUT_1_1_1",
		"Lwin_1_1_1" : "LW_IN_1_1_1", "Lwout_1_1_1" : "LW_OUT_1_1_1", "PPFD_1_1_1" : "PPFD_IN_1_1_1",
		"Rn_1_1_1" : "NETRAD_1_1_1", "MWS_1_1_1" : "WS_1_1_1", "Ts_1_1_1" : "TS_1_1_1", "Ts_2_1_1" : "TS_2_1_1",
		"Ts_3_1_1" : "TS_3_1_1", "Pswc_1_1_1" : "SWC_1_1_1", "Pswc_2_1_1" : "SWC_2_1_1", "Pswc_3_1_1" : "SWC_3_1_1",
		"SHF_1_1_1" : "G_1_1_1", "SHF_2_1_1" : "G_2_1_1", "SHF_3_1_1" : "G_3_1_1", "L" : "MO_LENGTH_1_1_1",
		"(z-d)/L" : "ZL_1_1_1", "x_peak" : "FETCH_MAX_1_1_1", "x_70%" : "FETCH_70_1_1_1", "x_90%" : "FETCH_90_1_1_1", "ch4_flux" : "FCH4_1_1_1", "qc_ch4_flux" : "FCH4_SSITC_TEST_1_1_1", "ch4_mole_fraction" : "CH4_1_1_1", "ch4_strg" : "SCH4_1_1_1",  "ch4_signal_strength" : "CH4_RSSI_1_1_1", "co2_signal_strength" : "CO2_STR_1_1_1"}
	col_match = {key.lower(): item for key, item in col_match.items()}

	ias_df = ias_df.rename(columns=col_match)
	time_cols = ['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime']
	var_cols = [col_match[col] for col in col_match.keys() if col_match[col] in ias_df.columns]

	ias_df['TIMESTAMP_START'] = ias_df[time].dt.strftime('%Y%m%d%H%M')
	ias_df['TIMESTAMP_END'] = (ias_df[time] + pd.Timedelta(0.5, "H")).dt.strftime('%Y%m%d%H%M')
	ias_df['DTime'] = np.round(ias_df[time].dt.dayofyear + 1./48*2*ias_df[time].dt.hour + 1./48*(ias_df[time].dt.minute//30), decimals=3)

	if 'h_strg' in ias_df.columns:
		ias_df['SH'] = ias_df['h_strg']
		var_cols.append('SH')
	if 'le_strg' in ias_df.columns:
		ias_df['SLE'] = ias_df['le_strg']
		var_cols.append('SLE')

	ias_year = ias_df[time].dt.year.min()
	var_cols.sort()
	col_list_ias = time_cols + var_cols
	print(col_list_ias)
	ias_df = ias_df[col_list_ias]
	ias_df.to_csv(f"{ias_output_prefix}_{ias_year}_{ias_output_version}.csv", index=False)
	logging.info(f"IAS file saved to {ias_output_prefix}_{ias_year}_{ias_output_version}.csv")

# + [markdown] id="Pm8hiMrb_wRW"
# # Сохранение данных FAT

# + [markdown] id="0ll51nOal6Lz"
# ![image.png](data:image/png;base64,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)

# + id="w9hkPLkB_zd1"
if config_meteo ['use_biomet']:
  fat_output_template = {'DoY': ['--'], r'u*': ['m s-1'],	'H': ['W m-2'], 'lE': ['-'],	'NEE': ['umol m-2 s-1'],	'PPFD': ['umol m-2 s-1'], 'Ta':['oC'], 'VPD':['kPa'], 'PPFD_gapfilling': ['umol m-2 s-1'], 'Ta_gapfilling': ['oC'], 'VPD_gapfilling': ['kPa'], 'period': ['--']}

  fat_df = plot_data.copy()


  for column, filter in filters_db.items():
    filter = get_column_filter(fat_df, filters_db, column)
    fat_df.loc[~filter.astype(bool), column] = np.nan



  fat_df['DoY'] = np.round(fat_df[time].dt.dayofyear + 0.02*fat_df[time].dt.hour + 0.01*(fat_df[time].dt.minute//30), decimals=2)
  fat_df[r'u*'] = fat_df['u_star'].fillna(-99999)
  fat_df['H'] = fat_df['h'].fillna(-99999)
  fat_df['lE'] = fat_df['le'].fillna(-99999)
  fat_df['NEE'] = fat_df['nee'].fillna(-99999)
  fat_df['PPFD'] = fat_df['ppfd_1_1_1'].fillna(-99999)
  fat_df['Ta'] = fat_df['ta_1_1_1'].fillna(-99999)
  fat_df['VPD'] = fat_df['vpd_1_1_1'].fillna(-99999)

  fat_df['period'] = fat_df.index.month%12//3 + 1

  fat_df['PPFD_gapfilling'] = fat_df['ppfd_1_1_1'].interpolate(limit=3).fillna(bg.calc_rolling(fat_df['ppfd_1_1_1'], rolling_window=10 , step=24 * 2, min_periods=4)).fillna(-99999)
  fat_df['Ta_gapfilling'] = fat_df['ta_1_1_1'].interpolate(limit=3).fillna(bg.calc_rolling(fat_df['ta_1_1_1'], rolling_window=10 , step=24 * 2, min_periods=4)).fillna(-99999)
  fat_df['VPD_gapfilling'] = fat_df['vpd_1_1_1'].interpolate(limit=3).fillna(bg.calc_rolling(fat_df['vpd_1_1_1'], rolling_window=10 , step=24 * 2, min_periods=4)).fillna(-99999)

  for year in fat_df.index.year.unique():
    fat_filename = f"FAT_{year}.csv"
    pd.DataFrame(fat_output_template).to_csv(fat_filename, index=False)
    save_data = fat_df.loc[fat_df[time].dt.year==year]
    fat_df.to_csv(fat_filename,  index=False, header=False, columns = [i for i in fat_output_template.keys()], mode='a')#, sep=' ')
  del fat_df
  logging.info(f"FAT file saved to {fat_filename}")
# -

# # Общий файл

plot_data.to_csv('basic.csv', index=None)
logging.info(f"Basic file saved to 'basic.csv'")

# # Модифицированный общий файл

# +
columns_to_save = ['Date', 'Time', 'DoY', 'ta', 'rh', 'vpd', 'swin', 'ppfd', 'p', 'h', 'le', 'co2_flux', 'co2_strg']

basic_df = plot_data.copy()

basic_df['Date'] = basic_df[time].dt.date
basic_df['Time'] = basic_df[time].dt.time
basic_df['DoY'] = np.round(basic_df[time].dt.dayofyear + 0.02*basic_df[time].dt.hour + 0.01*(basic_df[time].dt.minute//30), decimals=2)

#метео
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p']:
  # print(f"{col}(_[1-9]){{1,4}})")
  col_pos = [bool(re.fullmatch(f"{col}(_[1-9]){{1,4}}", col_in)) for col_in in  basic_df.columns]
  if not any(col_pos):
    continue
  else:
    real_col_name = basic_df.columns[np.argmax(col_pos)]
    basic_df[col] = basic_df[real_col_name]

#Фильтрованные потоки
for col in ['nee', 'h', 'le', 'co2_strg']:
  if col not in basic_df.columns:
    continue
  basic_df[f"{col}_filtered"] = basic_df[col]
  filter = get_column_filter(basic_df, filters_db, col)
  basic_df.loc[~filter.astype(bool), f"{col}_filtered"] = np.nan
  columns_to_save.append(f"{col}_filtered")

#Фильтрованные метео
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p']:
  if col not in basic_df.columns:
    continue
  basic_df[f"{col}_filtered"] = basic_df[col]
  filter = get_column_filter(basic_df, filters_db, col)
  basic_df.loc[~filter.astype(bool), f"{col}_filtered"] = np.nan
  columns_to_save.append(f"{col}_filtered")

#флаги
for col in ['nee', 'ch4', 'le', 'h']:
  if col not in basic_df.columns:
    continue
  basic_df[f"{col}_integral_flag"] = get_column_filter(basic_df, filters_db, col)
  columns_to_save.append(f"{col}_integral_flag")

for key, item in filters_db.items():
  columns_to_save = columns_to_save + item


basic_df = basic_df[[col for col in columns_to_save if col in basic_df.columns]]
basic_df = basic_df.fillna(-99999)
basic_df.to_csv('basic_new.csv', index=None)
logging.info(f"New basic file saved to 'basic.csv'")
# -

# # Обработка утилитами REddyProc

# ## Технический блок

# +
# RUN_MODE = "LOCAL_IPYNB", "LOCAL_PY", "COLAB_IPYNB" ?
# can "LOCAL_IPYNB" be excluded completely in favor of "LOCAL_PY"? 
# def section_*(): + ipynb to py convert? 
# if %%R extracted to *.r?
# if some sections are designed as colab only?

# TODO breakpoint fixed if skip conda env?
# # !source activate myenv
# # !python -m ipykernel install --user --name myenv --display-name "Python (myenv)"

import importlib.util
if importlib.util.find_spec("google") is None:
    RUN_MODE = "LOCAL"
else: 
    RUN_MODE = "COLAB"
    # !pip install wget
    

# TODO LOCAL_PY
if RUN_MODE == "LOCAL":
    ias_output_prefix = 'tv_fy4'


from pathlib import Path
Path("output").mkdir(parents=True, exist_ok=True)

if RUN_MODE == "COLAB":
    SRC_FILES = [
        'src/helpers/image_tools.py',
        'src/helpers/os_helpers.py',
        'src/reddyproc/draw_reddyproc_graphs.py',
        'src/reddyproc/eddyproc_web_tool_copy.r',
        'src/reddyproc/calc_averages.r'
    ]
    DOWNLOAD_SOURCE = "https://raw.githubusercontent.com/halt9k/fluxfilter-extended/dev_draft/"
    import wget
    for file in SRC_FILES:
        Path(file).unlink(missing_ok=True)
        Path(file).parent.mkdir(parents=True, exist_ok=True)
        wget.download(out=file, url= DOWNLOAD_SOURCE + file)

if RUN_MODE == "LOCAL":
    import os, sys
    env_folder = os.path.dirname(sys.executable)
    r_folder = str(Path(env_folder) / "Lib/R")
    assert Path(r_folder).exists()
    os.environ['R_HOME'] = r_folder


# Enabling R support in %%R cells
# %load_ext rpy2.ipython
# -

# ## Основной блок обработки
#
# В следующей секции eddyProcConfiguration - настройки, совпадающие с опциями [онлайн утилиты](https://www.bgc-jena.mpg.de/REddyProc/ui/REddyProc.php):
#
# Название местности, которое будет добавлено в названия выходных файлов  
# siteId = 'yourSiteID'
#
# Включение фильтрации u* методом Moving Point Test, выбор Seasoning "Continuous" или "WithinYear".  
# Также отключено предположение статистики?? неопределенностей (bootstrap).  
# isToApplyUStarFiltering = TRUE  
# uStarSeasoning =  factor("Continuous", levels = "Continuous")  
# isBootstrapUStar = FALSE  
#   
# Включение и выбор методов разделения потоков "Reichstein05" и/или "Lasslop10"  
# isToApplyGapFilling = TRUE  
# isToApplyPartitioning = TRUE  
# partitioningMethods = c("Reichstein05", "Lasslop10")  
#
# Широта, долгота, временная зона  
# latitude = 56.5  
# longitude = 32.6  
# timezone = +3  
#
# Столбец температур воздуха  
# temperatureDataVariable = "Tair", 

# + magic_args="-i ias_output_prefix" language="R"
#
#
# eddyproc_config <- list(
#     # siteId = 'yourSiteID',
#     siteId = ias_output_prefix,
#
#     isToApplyUStarFiltering = TRUE,
#     # uStarSeasoning = "WithinYear", "Continuous" , ...
#
#     # could be more levels somewhere around
#     uStarSeasoning =  factor("Continuous", levels = "Continuous"),
#     uStarMethod = factor("RTw", levels = "RTw"),
#
#     isBootstrapUStar = FALSE,
#
#     isToApplyGapFilling = TRUE,
#     isToApplyPartitioning = TRUE,
#     # "Reichstein05", "Lasslop10", ...
#     partitioningMethods = c("Reichstein05", "Lasslop10"),
#     latitude = 56.5,
#     longitude = 32.6,
#     timezone = +3,
#
#     # there is also $temperatureVarName ?
#     temperatureDataVariable = "Tair",
#
#     isCatchingErrorsEnabled = TRUE,
#
#     input_format = "onlinetool",
#     output_format = "onlinetool",
#
#     # figureFormat used from processEddyData
#     useDevelopLibraryPath = FALSE,
#     debugFlags = ""
# )
#
#
# # formatR::tidy_rstudio()
# # REddyProc global vars
# INPUT_FILE = "REddyProc.txt"
# OUTPUT_DIR = "./output/REddyProc"
# OUTPUT_PLOTS_MASK = "*.png"
#
# dir.create(OUTPUT_DIR, showWarnings = FALSE)
# unlink(file.path(OUTPUT_DIR, "*.png"))
# unlink(file.path(OUTPUT_DIR, "*.csv"))
# unlink(file.path(OUTPUT_DIR, "output.txt"))
#
#
# # 1.3.2 vs 1.3.3 have different outputs
# # to test,
# # install.packages('https://cran.r-project.org/bin/windows/contrib/4.1/REddyProc_1.3.2.zip', repos = NULL, type = "binary")
# install_if_missing <- function(package, repos) {
#     if (!require(package, character.only = TRUE)) {
#         install.packages(package, dependencies = TRUE, repos=repos)
#         library(package, character.only = TRUE)
#     }
# }
# install_if_missing("REddyProc", repos='http://cran.rstudio.com/')
#
#
# library(REddyProc)
# source("src/reddyproc/eddyproc_web_tool_copy.r", chdir = T)
# source("src/reddyproc/calc_averages.r", chdir = T)
#
# options(max.print = 50)
# # fix of stderr output spammed under rpy2.ipython
# sink(stdout(), type = "message")
#
# ext = tools::file_ext(OUTPUT_PLOTS_MASK)
# df_output <- processEddyData(eddyproc_config, dataFileName = INPUT_FILE, figureFormat = ext)
# calc_averages(df_output, OUTPUT_DIR, eddyproc_config$siteId)
# -

# ## Контрольные графики
#  Совпадают с графиками онлайн утилиты

# +
# Full list of outputs (not all are included in OUTPUT_ORDER):
# 'DC_H_f', 'DC_LE_f', 'DC_NEE_uStar_f', 'DC_Rg_f', 'DC_rH_f', 'DC_Tair_f', 'DC_VPD_f',
# 'DSum_Rg_f', 'DSum_rH_f', 'DSum_Tair_f', 'DSum_VPD_f', 'DSumU_H_f', 'DSumU_LE_f', 'DSumU_NEE_uStar_f',
# 'Flux_H', 'Flux_H_f', 'Flux_LE', 'Flux_LE_f', 'Flux_NEE', 'Flux_NEE_uStar_f', 'Flux_Rg', 
# 'Flux_Rg_f', 'Flux_rH', 'Flux_rH_f', 'Flux_Tair','Flux_Tair_f', 'Flux_VPD','Flux_VPD_f',
# 'FP_GPP_DT_uStar', 'FP_GPP_uStar_f', 'FP_H', 'FP_H_f', 'FP_LE', 'FP_LE_f', 'FP_NEE', 
# 'FP_NEE_uStar_f', 'FP_Reco_DT_uStar', 'FP_Reco_uStar',
# 'FP_Rg', 'FP_Rg_f', 'FP_rH', 'FP_rH_f', 'FP_Tair', 'FP_Tair_f', 'FP_VPD', 'FP_VPD_f'


# TODO what if 2023 is not only year or REddyProc output for images?
# TODO HEAT_MAPS 'FP_NEE_uStar_f' or 'FP_NEE' ?
CROP_POSTFIX = '_crop'
CROP = ['FP_NEE', 'FP_NEE_uStar_f',
        'FP_LE', 'FP_LE_f',
        'FP_H', 'FP_H_f',]


REMOVED_LEGEND_POSTFIX = '_bare'
REMOVE_LEGENDS = ['FP_NEE_crop',
                  'FP_LE_crop',
                  'FP_H_crop']


# just for the record: unicode in code is not great
OUTPUT_ORDER = (
    "Тепловые карты", 
    ['FP_NEE_crop_bare', 'FP_NEE_uStar_f_crop'],
    ['FP_LE_crop_bare', 'FP_LE_f_crop'],
    ['FP_H_crop_bare', 'FP_H_f_crop'],
    "Суточный ход", 
    ['DC_NEE_uStar_f'], 
    ['DC_LE_f'], 
    ['DC_H_f'],
    "30-минутные потоки", 
    ['Flux_NEE', 'Flux_NEE_uStar_f'],
    ['Flux_LE', 'Flux_LE_f'],
    ['Flux_H', 'Flux_H_f']
)


# %load_ext autoreload
# %autoreload 2
from src.reddyproc.draw_reddyproc_graphs import prepare_images, display_images  
prepare_images(CROP, CROP_POSTFIX,  REMOVE_LEGENDS, REMOVED_LEGEND_POSTFIX)
display_images(OUTPUT_ORDER)
