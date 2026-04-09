from copy import copy
from pathlib import Path

import numpy as np
import pandas as pd

from src.config.ff_config import RepConfig
from src.data_io.rep_level3_export import export_rep_level3
from src.helpers.io_helpers import ensure_empty_dir
from src.helpers.pd_helpers import equal_series
from src.plots import get_column_filter
from src.reddyproc.preprocess_rg import prepare_rg
from src.reddyproc.reddyproc_bridge import reddyproc_and_postprocess


def run_ustar(config, gl, data, time_col, extract_rep_cols):
    cfg_ustar = copy(config)
    output_template = {
        'Year': ['-'], 'DoY': ['-'], 'Hour': ['-'], 'NEE': ['umol_m-2_s-1'], 'LE': ['Wm-2'], 'H': ['Wm-2'],
        'Rg': ['Wm-2'], 'Tair': ['degC'], 'Tsoil': ['degC'], 'rH': ['%'], 'VPD': ['hPa'], 'Ustar': ['ms-1'],
        'CH4flux': ['umol_m-2_s-1']
    }
    rep_df = data.copy()
    
    gl.rep_level3_fpath = gl.out_dir / f"REddyProc_ustar_test.txt"
    export_rep_level3(gl.rep_level3_fpath, rep_df, time_col, output_template, cfg_ustar, gl.points_per_day)
    
    config_ustar = RepConfig(
        is_to_apply_u_star_filtering=True,
        # if default REP cannot detect threshold, this value may be used instead; None to disable
        ustar_threshold_fallback=0.01,
        # REP ustar requires Rg to detect nights; when real data is missing, 3 workarounds are possible
        # "Rg_th_Py", "Rg_th_REP" - estimate by theoretical algs,
        # "Rg" - by real data, "" - ignore Rg and filter both days and nights
        ustar_rg_source="Rg",
        is_bootstrap_u_star=True,
        skip_gap_filling_after_ustar=True,
        # u_star_seasoning: one of "WithinYear", "Continuous", "User"
        u_star_seasoning="Continuous",
        
        is_to_apply_partitioning=False,
        
        # partitioning_methods: one or both of "Reichstein05", "Lasslop10"
        partitioning_methods=["Reichstein05", "Lasslop10"],
        
        latitude=56.5,
        longitude=32.6,
        timezone=+3.0,
        
        # "Tsoil"
        temperature_data_variable="Tair",
        
        # do not change
        site_id=cfg_ustar.metadata.site_name,
        u_star_method="RTw",
        is_to_apply_gap_filling=True,
        input_file=str(gl.rep_level3_fpath),
        output_dir=str(gl.out_dir / 'reddyproc'),
    )
    
    # if not cfg_ustar.from_file:
    cfg_ustar.reddyproc = config_ustar
    
    cfg_ustar.reddyproc.input_file = config_ustar.input_file
    cfg_ustar.reddyproc.output_dir = config_ustar.output_dir
    cfg_ustar.reddyproc.site_id = config_ustar.site_id
    
    prepare_rg(cfg_ustar.reddyproc)
    ensure_empty_dir(cfg_ustar.reddyproc.output_dir)
    rep_out_info, config_reddyproc = reddyproc_and_postprocess(cfg_ustar.reddyproc, gl.repo_dir)
    out_file = Path(config_ustar.output_dir) / (rep_out_info.fnames_prefix + '_filled.txt')
    assert out_file.exists()
    data_rep_long = pd.read_csv(out_file, sep="\t", header=0, skiprows=[1], na_values=-9999.0)
   
    # test on ias, drop first row
    res = data.copy()    
    data_rep_long.index = pd.to_datetime(data_rep_long['Date Time'], format='%Y-%m-%d %H:%M:%S')   
    data_rep = data_rep_long.reindex(res.index)    
    if len(data_rep) != len(res):
        Exception('Cannot cut REP output to input')
        
    
    '''    
    ustar_applied_mask = ~res['nee'].isna() & data_rep['NEE_orig'].isna()
    res['nee_without_ustar'] = res['nee']
    # assert ustar_applied_mask.sum() > 0 and data_rep['NEE_orig'][ustar_applied_mask].isna().all()
    res['nee'][ustar_applied_mask] = np.nan    
    print('Applied uStar threshold to NEE values: \n\n', res[['nee', 'nee_without_ustar']][ustar_applied_mask], '\n')
    '''
    
    ensure_empty_dir(cfg_ustar.reddyproc.output_dir)
    return data_rep[extract_rep_cols]
    
