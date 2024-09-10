from rpy2 import robjects

from cells_mirror.cell_reddyproc_process import eddyproc_options


def run_reddyproc(user_options):
    # do not omit stderr+
    from rpy2 import rinterface_lib
    rinterface_lib.callbacks.consolewrite_print = lambda msg: print(msg, end='')
    rinterface_lib.callbacks.consolewrite_warnerror = lambda msg: print(msg, end='')
    rinterface_lib.callbacks.showmessage = lambda msg: print(msg, end='')

    # this is workaround to avoid %%R code, which supported badly anyway in multiple workflows
    # also to be able to run R tests only using R files
    robjects.r.source('src/reddyproc/web_tool_bridge.r')
    run_web_tool = robjects.globalenv['run_web_tool_bridge_logged']
    eddyproc_options.partitioning_methods = robjects.StrVector(eddyproc_options.partitioning_methods)
    res = run_web_tool(eddyproc_user_options=robjects.ListVector(vars(eddyproc_options)))

    # StrVector to python string
    return res[0]
