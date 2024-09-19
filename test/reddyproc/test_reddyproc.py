import shutil
from pathlib import Path
import os, sys
from types import SimpleNamespace

import pytest

import src.helpers.os_helpers  # noqa: F401
from src.helpers.io_helpers import ensure_empty_dir
import src.ipynb_globals as ig


@pytest.fixture
def use_r_from_python_env():
    env_folder = os.path.dirname(sys.executable)
    r_folder = str(Path(env_folder) / "Lib/R")
    assert Path(r_folder).exists()
    os.environ['R_HOME'] = r_folder


def test_process(use_r_from_python_env):
    ig.ias_output_prefix = 'tv_fy4_22-14'

    import src.cells_mirror.cell_reddyproc_process  # noqa: F401
    # import src.cells_mirror.cell_reddyproc_draw  # noqa: F401


def test_draw():
    ig.eddyproc_options = SimpleNamespace(is_to_apply_u_star_filtering=True)
    ig.eddy_out_prefix = 'tv_fy4_22-14_22-23'
    ig.eddy_out_year_start = 2022
    ig.eddy_out_year_end = 2023
    # ensure_empty_dir('output/reddyproc')
    # shutil.copytree('test/reddyproc/test_reddyproc_process/output_sample', 'output/reddyproc', dirs_exist_ok=True)
    import src.cells_mirror.cell_reddyproc_draw  # noqa: F401


