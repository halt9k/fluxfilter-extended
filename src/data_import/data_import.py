import logging
from enum import Enum
from pathlib import Path

from src.data_import.eddypro_loader import BIOMET_HEADER_DETECTION_COLS, EDDYPRO_HEADER_DETECTION_COLS
from src.data_import.ias_loader import IAS_HEADER_DETECTION_COLS
from src.data_import.parse_fnames import try_parse_ias_fname, try_parse_eddypro_fname
from src.data_import.table_loader import load_table_from_file

SUPPORTED_FILE_EXTS_LOWER = ['.csv', '.xlsx', '.xls']


class ImportMode(Enum):
	# extension and data level before import
	EDDYPRO_L1 = 1
	EDDYPRO_L1_AND_BIOMET = 2
	IAS_L2 = 3
	CSF_L = 4
	AUTO = 5


class InputFileType(Enum):
	# extension and processing level
	UNKNOWN = 0
	EDDYPRO = 1
	BIOMET = 2
	CSF = 3
	IAS = 4


class AutoImportException(Exception):
	pass


def detect_file_type(fpath: Path, header_rows=4) -> InputFileType:
	df = load_table_from_file(fpath, nrows=header_rows, header=None)

	# may be also consider exact header row place
	ias_cols = (set(IAS_HEADER_DETECTION_COLS), InputFileType.IAS)
	biomet_cols = (set(BIOMET_HEADER_DETECTION_COLS), InputFileType.BIOMET)
	eddypro_cols = (set(EDDYPRO_HEADER_DETECTION_COLS), InputFileType.EDDYPRO)
	detect_col_targets = [ias_cols, biomet_cols, eddypro_cols]

	def match_ratio(sample: set, target: set):
		return len(sample & target) / len(sample)

	# upper/lower case is yet skipped intentionally
	header_matches = []
	for _, row in df.iterrows():
		fixed_row = row.dropna()
		for cols_set, ftype in detect_col_targets:
			mr = match_ratio(set(fixed_row), cols_set)
			if mr > 0.5:
				header_matches += [(mr, ftype)]

	if len(header_matches) == 1:
		mr, ftype = header_matches[0]
		logging.info(f'Detected file {fpath} as {ftype}')
		return ftype
	else:
		logging.warning(f'Cannot detect file type {fpath}, guesses are {header_matches}')
		return InputFileType.UNKNOWN


def detect_known_files(input_dir='.', from_list: list[str] = None) -> dict[Path, InputFileType]:
	if not from_list:
		root_files = list(Path(input_dir).glob('*.*'))
		input_files = [f for f in root_files if f.suffix.lower() in SUPPORTED_FILE_EXTS_LOWER]
	else:
		input_files = from_list
	input_file_types = {f: detect_file_type(f) for f in input_files}
	return {k: v for k, v in input_file_types.items() if v != InputFileType.UNKNOWN}


def change_if_auto(option, new_option=None, new_option_call=None, ok_msg=None, skip_msg=None):
	# new_option_call can be used instead of new_option to optimise out new option detection:
	# if not auto, detection will be skipped

	if option != 'auto':
		if skip_msg:
			logging.warning(skip_msg)
		return option

	if new_option_call:
		assert new_option is None
		new_option = new_option_call()

	if ok_msg:
		logging.info(ok_msg)
	return new_option


def detect_input_mode(input_file_types: dict[Path, InputFileType]) -> ImportMode:
	input_ftypes = list(input_file_types.values())
	possible_input_modes = []

	if InputFileType.EDDYPRO in input_ftypes:
		if InputFileType.BIOMET not in input_ftypes:
			possible_input_modes += [ImportMode.EDDYPRO_L1]
		else:
			if input_ftypes.count(InputFileType.BIOMET) > 1:
				raise AutoImportException('More than 2 biomet files detected')
			possible_input_modes += [ImportMode.EDDYPRO_L1_AND_BIOMET]

	if InputFileType.IAS in input_ftypes:
		possible_input_modes += [ImportMode.IAS_L2]

	if len(possible_input_modes) == 0:
		raise AutoImportException(f'No import modes detected, ensure files are in script folder and review log.')
	elif len(possible_input_modes) == 1:
		mode = possible_input_modes[0]
	else:
		raise AutoImportException(f'Multiple input modes possible: {possible_input_modes}, cannot auto pick.\n'
		                          "Remove some files or specify manually config['path'].")

	logging.info(f'Picked input mode: {mode}')
	return mode


def auto_config_ias_input(input_file_types: dict[Path, InputFileType], config_meteo):
	# files are already verified in detect_input_mode

	config_path = list(input_file_types.keys())
	config_meteo_use_biomet = True

	if config_meteo['path'] is not None and config_meteo['path'] != 'auto':
		logging.warning(f"config_meteo['path'] value = {config_meteo['path']} "
		                f"will be ignored due to ias_2 input mode (ias file includes biomet)")
	config_meteo_path = None

	ias_output_prefix, ias_output_version = try_parse_ias_fname(str(config_path[0]))
	return config_path, config_meteo_use_biomet, config_meteo_path, ias_output_prefix, ias_output_version


def auto_config_eddypro_input(input_file_types: dict[Path, InputFileType], config_meteo):
	# files are already verified in detect_input_mode
	# 1 or 0 biomet files are already ensured

	config_path = [k for k, v in input_file_types.items() if v == InputFileType.EDDYPRO]

	biomets = [k for k, v in input_file_types.items() if v == InputFileType.BIOMET]
	if len(biomets) == 1:
		config_meteo_use_biomet = True
		config_meteo_path = biomets[0]
	else:
		config_meteo_use_biomet = False
		config_meteo_path = None

	ias_output_prefix, ias_output_version = try_parse_eddypro_fname(str(config_path[0]))
	return config_path, config_meteo_use_biomet, config_meteo_path, ias_output_prefix, ias_output_version


def auto_detect_input_files(config: dict, config_meteo: dict, ias_output_prefix: str, ias_output_version: str):
	# TODO Q why 2 configs intead of one? merge options?

	if config['path'] == 'auto':
		logging.info("Detecting input files due to config['path'] = 'auto' ")
		input_file_types = detect_known_files()
	else:
		user_files = config['path'] if isinstance(config['path'], list) else [config['path']]
		input_file_types = detect_known_files(user_files)

	# noinspection PyPep8Naming
	IM = ImportMode
	assert type(config['mode']) is IM
	detected_mode = detect_input_mode(input_file_types)
	if config['mode'] == IM.AUTO:
		config['mode'] = detected_mode
	elif config['mode'] != detected_mode:
		logging.warning(f"Detected mode: {detected_mode} is different from config['mode']: {config['mode']}. "
		                "Consider changing config['mode'] to .AUTO")

	# TODO 3 update messages to match exact config naming after updating config options
	if config['mode'] == IM.IAS_L2:
		res = auto_config_ias_input(input_file_types, config_meteo)
	elif config['mode'] in [IM.EDDYPRO_L1, IM.EDDYPRO_L1_AND_BIOMET]:
		res = auto_config_eddypro_input(input_file_types, config_meteo)
	else:
		raise NotImplementedError
	config_path, config_meteo_use_biomet, config_meteo_path, ias_output_prefix_d, ias_output_version_d = res

	# TODO 2 this ping pong is result of config['path'] not same as config['all_input_files_list'] = [...]
	# if generalization is possible, would be better
	config['path'] = change_if_auto(config['path'], config_path)
	config_meteo['use_biomet'] = change_if_auto(config_meteo['use_biomet'], new_option=config_meteo_use_biomet,
	                                            skip_msg="config_meteo['use_biomet'] option is not 'auto'. Auto detection skipped.")
	config_meteo['path'] = change_if_auto(config_meteo['path'], new_option=config_meteo_path,
	                                      skip_msg="config_meteo['path'] option is not 'auto'. Auto detection skipped.")
	# TODO Q why ias_output_prefix is not part of config?
	ias_output_prefix = change_if_auto(ias_output_prefix, ias_output_prefix_d)
	ias_output_version = change_if_auto(ias_output_version, ias_output_version_d)

	return config, config_meteo, ias_output_prefix, ias_output_version


def try_auto_detect_input_files(*args, **kwargs):
	try:
		return auto_detect_input_files(*args, **kwargs)
	except AutoImportException as e:
		logging.error(e)
		raise SystemExit()
