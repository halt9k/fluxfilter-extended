import contextlib
import logging
import sys
from pathlib import Path


@contextlib.contextmanager
def catch(on_exception=None, err_types=Exception):
	if not err_types:
		yield
		return

	try:
		yield
	except err_types as e:
		if on_exception:
			on_exception(e)


def invert_dict(d: dict):
	vals = d.values()
	vals_set = set(vals)
	if len(vals) != len(vals_set):
		raise Exception('Cannot invert dictionary with duplicate values')

	return {v: k for k, v in d.items()}


def replace_in_dict_by_values(d: dict, replacements: dict):
	assert set(replacements.values()) <= set(d.values())

	rd = invert_dict(d)
	rv = invert_dict(replacements)
	for k, v in rv.items():
		rd[k] = v
	return invert_dict(rd)


def fix_strs_case(strs: list[str], correct_case: list[str]):
	correct_l_to_correct = {c.lower(): c for c in correct_case}
	if len(correct_l_to_correct) != len(correct_case):
		raise Exception('Possibly correct_case contains duplicates with different cases')

	missing = [c for c in strs if c.lower() in correct_l_to_correct]
	new_strs = [correct_l_to_correct.get(c.lower(), c) for c in strs]
	renames = [(s, n) for s, n in zip(strs, new_strs) if s != n]
	return new_strs, renames, missing


def debug_stdout_to_log(debug_log_fpath):
	# stdout->log was required for something, but for what?
	# duplicates all prints to file

	class Logger(object):
		def __init__(self):
			self.terminal = sys.stdout
			self.log = open(debug_log_fpath, "w")

		def write(self, message):
			self.terminal.write(message)
			self.log.write(message)

		def flush(self):
			# this flush method is needed for python 3 compatibility.
			# this handles the flush command by doing nothing.
			# you might want to specify some extra behavior here.
			pass

	sys.stdout = Logger()


def init_logging(level=logging.INFO, fpath: Path = None, to_stdout=True):
	# this function is also required during tests, so placing not in ipynb is optimal

	if fpath:
		logging.basicConfig(level=level, filename=fpath, filemode="w", force=True)
		if to_stdout:
			logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
	else:
		# when no file is specified, writes to stderr
		logging.basicConfig(level=level, force=True)

	logging.info("START")


def sort_fixed(list_: list[str], fix_underscore: bool):
	# sort: ['NETRAD_1_1_1', 'PA_1_1_1', 'PPFD_IN_1_1_1', 'P_1_1_1']
	# fix_underscore = True: ['NETRAD_1_1_1', 'P_1_1_1', 'PA_1_1_1', 'PPFD_IN_1_1_1']
	def key(s):
		return s.replace('_', ' ') if fix_underscore else s
	list_.sort(key=key)


def ensure_list(list_, transform_func=None) -> list:
	if not isinstance(list_, list):
		ret = [list_]
	else:
		ret = list_

	if transform_func:
		return [transform_func(el) for el in ret]
	else:
		return ret


def intersect_list(items: list, valid_items: list) -> list:
	"""Same as intersect sets, but keeps order"""
	return [el for el in items if el in valid_items]


@contextlib.contextmanager
def switch_log_level(level, logger_name=None):
	logger = logging.getLogger(logger_name)
	old_level = logger.level
	logger.setLevel(level)
	try:
		yield
	finally:
		logger.setLevel(old_level)
