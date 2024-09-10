# patch this file during tests to introduce missing globals

# only site name like 'tv_fy4_22.14'
ias_output_prefix: str = globals()['ias_output_prefix']

# site name with years like 'tv_fy4_22.14_2024' or 'tv_fy4_22.14_23-25'
# must be provided by REddyProc internal naming routines
eddy_out_prefix: str = ''
