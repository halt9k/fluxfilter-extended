import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_io.csf_cols import COLS_CSF_IMPORT_MAP, \
	COLS_CSF_KNOWN,COLS_CSF_TIME, COLS_CSF_UNUSED_NORENAME_IMPORT, CSF_HEADER_DETECTION_COLS
from src.data_io.eddypro_cols import BIOMET_HEADER_DETECTION_COLS
from src.data_io.table_loader import load_table_logged
from src.data_io.time_series_utils import df_init_time_draft
from src.helpers.pd_helpers import df_ensure_cols_case


def process_csf_col_names(df: pd.DataFrame, time_col):
	print('Переменные в csf: \n', df.columns.to_list())

	known_csf_cols = COLS_CSF_KNOWN + [time_col]
	df = df_ensure_cols_case(df, known_csf_cols, ignore_missing=True)

	unknown_cols = df.columns.difference(known_csf_cols)
	if len(unknown_cols) > 0:
		msg = 'Неизвестные CSF переменные: \n', str(unknown_cols)
		logging.exception(msg)
		raise NotImplementedError(msg)

	unused_cols = df.columns.intersection(COLS_CSF_UNUSED_NORENAME_IMPORT)
	if len(unused_cols) > 0:
		# TODO 2 localize properly, remove prints (logging.* goes to stdout too)
		print('Переменные, которые не используются в тетради (присутствуют только в загрузке - сохранении): \n',
		      unused_cols.to_list())
		logging.warning('Unsupported by notebook csf vars (only save loaded): \n' + str(unused_cols.to_list()))

	df = df.rename(columns=COLS_CSF_IMPORT_MAP)
	print('Переменные после загрузки: \n', df.columns.to_list())

	expected_biomet_cols = np.strings.lower(BIOMET_HEADER_DETECTION_COLS)
	biomet_cols_index = df.columns.intersection(expected_biomet_cols)
	return df, biomet_cols_index


def import_csf(config, config_meteo):
	# TODO 2 merge with config, pack biomet into load routines only?
	assert config_meteo['use_biomet']

	if len(config['path']) != 1:
		raise NotImplemented(
			'Multiple csf files detected. Multiple run or combining multiple files is not supported yet.')
	fpath = config['path'][0]
	df = load_table_logged(fpath)

	# TODO QOA 2 (TIMESTAMP_START + TIMESTAMP_END) / 2? which is by CSF specification
	time_col = 'TIMESTAMP'
	df[time_col] = pd.to_datetime(df['TIMESTAMP_START'], format='%Y%m%d%H%M')
	df = df.drop(['TIMESTAMP_START', 'TIMESTAMP_END', 'DTime'], axis='columns')
	df = df_init_time_draft(df, time_col)

	print('Диапазон времени csf (START): ', df.index[[0, -1]])
	logging.info('Time range for full_output: ' + ' - '.join(df.index[[0, -1]].strftime('%Y-%m-%d %H:%M')))

	print('Replacing -9999 to np.nan')
	df.replace(-9999, np.nan, inplace=True)

	df, biomet_cols_index = process_csf_col_names(df, time_col)
	return df, time_col, biomet_cols_index, df.index.freq, config_meteo

