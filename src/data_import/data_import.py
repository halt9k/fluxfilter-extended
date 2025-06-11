import logging
from copy import copy
from enum import Enum
from pathlib import Path

'''
class ImportMode(Enum):
	# extension and processing level
	EDDYPRO1 = 1
	IAS2 = 2
	CSF1 = 3
	AUTO = 4
'''


def auto_detect_input_files(config, config_meteo, ias_output_prefix, ias_output_version):
	n_config, n_config_meteo = copy(config), copy(config_meteo)
	n_ias_output_prefix, n_ias_output_version = copy(ias_output_prefix), copy(ias_output_version)

	root_files = list(Path('.').glob('*.*'))
	lower_table_file_exts = ['.csv', '.xlsx', '.xls']
	input_files = [f for f in root_files if f.suffix.lower() in lower_table_file_exts]

	assert config['mode'] in ['csf_', 'ias_2', 'eddypro_1', 'auto']
	if config['mode'] == 'auto':
		logging.warning('auto currently only supports single ias file.' )
		n_config['mode'] = 'ias_2'

	if config['path'] == 'auto':
		config['path'] = ['eddy_pro result_SSB 2023.csv']

	if n_config['mode'] == 'ias_2' and config_meteo['path'] != '':
		logging.warning(f"config_meteo['path'] value = {config_meteo['path']} "
		                f"will be ignored due to ias_2 input mode which reads just single ias file")
	# TODO why ias_output_prefix is not part of config?
	if ias_output_prefix == 'auto':
		ias_output_prefix = 'tv_fy4'

	if ias_output_version == 'auto':
		ias_output_version = 'v01'

	logging.info('Detected next auto settings: %s', ias_output_prefix)

	return config, config_meteo, ias_output_prefix, ias_output_version
