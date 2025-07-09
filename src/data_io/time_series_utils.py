from bglabutils.basic import repair_time
import pandas as pd


def df_init_time_draft(df: pd.DataFrame, time_col: str, repair=True):
	if not repair:
		raise NotImplementedError

	# TODO 3 more transparent rework could be handy:
	#  with support of repair=False and separation of checks, repairs, and standard routines
	return repair_time(df, time_col)