from contextlib import contextmanager
from io import TextIOWrapper
from pathlib import Path

import rpy2.robjects as ro
from rpy2 import rinterface_lib as rl


@contextmanager
def capture_r_output(file: TextIOWrapper):
    # proper file name is not known yet, but expected to be finalized under yield

    rc = rl.callbacks
    cb_bkp = rc.consolewrite_print, rc.consolewrite_warnerror, rc.showmessage
    std_print = rc.consolewrite_print

    rc.consolewrite_print = lambda msg: (file.write(msg), std_print(msg))
    rc.consolewrite_warnerror = lambda msg: (file.write(msg), std_print(msg))
    rc.showmessage = lambda msg: (file.write(msg), std_print(msg))

    try:
        yield
    finally:
        (rc.consolewrite_print, rc.consolewrite_warnerror, rc.showmessage) = cb_bkp


def reddyproc_and_postprocess(eddy_options):
    reddyproc_py_options_fix = eddy_options
    reddyproc_py_options_fix.partitioning_methods = ro.StrVector(eddy_options.partitioning_methods)
    reddyproc_r_options = ro.ListVector(vars(reddyproc_py_options_fix))

    err_prefix = 'error'
    draft_log_name = Path(eddy_options.output_dir) / (err_prefix + eddy_options.log_fname_end)

    with open(draft_log_name, 'w') as f, capture_r_output(f):
        ro.r.source('src/reddyproc/reddyproc_wrapper.r')
        func_run_web_tool = ro.globalenv['reddyproc_and_postprocess']

        res = func_run_web_tool(user_options=reddyproc_r_options)
        # [0][0] eproc_info, [1][0] out_prefix

    assert type(res[0][2]) is ro.FloatVector and type(res[0][3]) is ro.FloatVector
    year_start, year_end = int(res[0][2][0]), int(res[0][3][0])
    assert type(res[1]) is ro.StrVector
    fnames_prefix = res[1][0]

    new_path = draft_log_name.parent / draft_log_name.name.replace(err_prefix, fnames_prefix)
    draft_log_name.rename(new_path)

    return year_start, year_end, fnames_prefix
