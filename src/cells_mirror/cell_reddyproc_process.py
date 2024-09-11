from types import SimpleNamespace

from src.reddyproc.reddyproc_bridge import reddyproc_and_postprocess
from src.ipynb_globals import *
import src.ipynb_globals as ig
from src.helpers.io_helpers import ensure_empty_dir

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
    timezone=+3.0,

    temperature_data_variable="Tair",

    input_file="REddyProc.txt",
    output_dir="output/reddyproc",
    log_fname_end='_log.txt'
)

ensure_empty_dir(eddyproc_options.output_dir)
ig.eddy_out_prefix = reddyproc_and_postprocess(eddyproc_options)