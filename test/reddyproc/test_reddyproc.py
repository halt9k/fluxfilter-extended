import shutil
from pathlib import Path
import os, sys
import pytest

import src.helpers.os_helpers  # noqa: F401
from src.helpers.io_helpers import ensure_empty_dir
import src.global_mocks as mocks


@pytest.fixture
def use_r_from_python_env():
    env_folder = os.path.dirname(sys.executable)
    r_folder = str(Path(env_folder) / "Lib/R")
    assert Path(r_folder).exists()
    os.environ['R_HOME'] = r_folder


import src.colab_routines as cr
cr.workaround_stop_scroll = lambda: None


def test_process(use_r_from_python_env):
    mocks.ias_output_prefix = 'tv_fy4'

    # do not omit stderr
    from rpy2 import robjects, rinterface_lib
    rinterface_lib.callbacks.consolewrite_print = lambda msg: print(msg, end='')
    rinterface_lib.callbacks.consolewrite_warnerror = lambda msg: print(msg, end='')
    rinterface_lib.callbacks.showmessage = lambda msg: print(msg, end='')

    import src.cells_mirror.cell_reddyproc_process  # noqa: F401


def test_draw():
    mocks.out_prefix = 'TestSiteID_2023-2024_'
    ensure_empty_dir('output/REddyProc')
    shutil.copytree('test/reddyproc/test_reddyproc_process/output_sample', 'output/REddyProc', dirs_exist_ok=True)
    import src.cells_mirror.cell_reddyproc_draw  # noqa: F401


if __name__ == '__main__':
    test_draw()