from pathlib import Path
import os, sys

import src.helpers.os_helpers  # noqa: F401
import src.global_mocks as mocks

env_folder = os.path.dirname(sys.executable)
r_folder = str(Path(env_folder) / "Lib/R")
assert Path(r_folder).exists()
os.environ['R_HOME'] = r_folder


def test():
    mocks.ias_output_prefix = 'tv_fy4'
    import src.cells_mirror.cell_eddyproc_process  # noqa: F401
    import src.cells_mirror.cell_eddyproc_draw  # noqa: F401