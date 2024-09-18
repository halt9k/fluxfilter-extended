# this file is for mocking missing globals during tests and local runs
# expected us in every cell:from src.ipynb_globals import *
# do not declare variables here, only describe
from types import SimpleNamespace

# only site name like 'tv_fy4_22.14'
# ias_output_prefix: str = 'tv_fy4_22-14'
ias_output_prefix: str

# site name with years like 'tv_fy4_22.14_2024' or 'tv_fy4_22.14_23-25'
# must be provided by REddyProc internal naming routines
# eddy_out_prefix: str = 'tv_fy4_22-14_2023'
eddy_out_prefix: str

eddyproc_options: SimpleNamespace
