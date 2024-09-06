import shutil
from pathlib import Path
import os, sys
import pytest

import src.helpers.os_helpers  # noqa: F401


@pytest.fixture
def use_r_from_python_env():
    env_folder = os.path.dirname(sys.executable)
    r_folder = str(Path(env_folder) / "Lib/R")
    assert Path(r_folder).exists()
    os.environ['R_HOME'] = r_folder


import src.colab_routines as cr
cr.workaround_stop_scroll = lambda: None


def test_process(use_r_from_python_env):
    import src.global_mocks as mocks
    mocks.ias_output_prefix = 'tv_fy4'

    import src.cells_mirror.cell_reddyproc_process  # noqa: F401


def test_draw():
    shutil.copytree('test/reddyproc/test_reddyproc_process/output_sample', 'output/REddyProc', dirs_exist_ok=True)
    import src.cells_mirror.cell_reddyproc_draw  # noqa: F401


if __name__ == '__main__':
    test_draw()