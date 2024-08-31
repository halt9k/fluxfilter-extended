from types import SimpleNamespace
from src.global_mocks import *  # noqa: F401


eddyproc_options = SimpleNamespace(
    site_id=ias_output_prefix,

    is_to_apply_u_star_filtering=True,

    # uStarSeasoning = "WithinYear", "Continuous" , ...
    u_star_seasoning="Continuous",
    u_star_method="RTw",

    is_bootstrap_u_star=False,

    is_to_apply_gap_filling=True,
    is_to_apply_partitioning=True,

    # "Reichstein05", "Lasslop10", ...
    partitioning_methods=["Reichstein05", "Lasslop10"],
    latitude=56.5,
    longitude=32.6,
    timezone=+3,

    temperature_data_variable="Tair",

    input_file="REddyProc.txt",
    output_dir="./output/REddyProc"
)

# this is workaround to avoid %%R code, which supported badly anyway in multiple workflows
# also to be able to run R tests only using R files
import rpy2.robjects as robjects

r = robjects.r

robjects.globalenv['eddyproc_user_options'] = robjects.ListVector(vars(eddyproc_options))
r.source('src/reddyproc/web_tool_bridge.r')
test_func = robjects.globalenv['run_web_tool_bridge']
test_func(eddyproc_user_options='eddyproc_user_options')
