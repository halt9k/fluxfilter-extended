import rpy2.robjects as ro
from rpy2 import rinterface_lib as rl


def print_sink(msg):
    # endings are already included in msg
    print(msg, end='')


def run_reddyproc(reddyproc_py_options):
    # do not omit stderr+
    rl.callbacks.consolewrite_print = print_sink
    rl.callbacks.consolewrite_warnerror = print_sink
    rl.callbacks.showmessage = print_sink

    reddyproc_py_options_fix = reddyproc_py_options
    reddyproc_py_options_fix.partitioning_methods = ro.StrVector(reddyproc_py_options.partitioning_methods)
    reddyproc_r_options = ro.ListVector(vars(reddyproc_py_options_fix))

    # this is workaround to avoid %%R code, which supported badly anyway in multiple workflows
    # also to be able to run R tests only using R files
    ro.r.source('src/reddyproc/reddyproc_wrapper.r')
    func_run_web_tool = ro.globalenv['run_web_tool_bridge_logged']

    res = func_run_web_tool(eddyproc_user_options=reddyproc_r_options)
    # StrVector to python string
    r_fnames_suffix = res[0]

    return r_fnames_suffix
