from pathlib import Path
import os, sys
import src.helpers.os_helpers  # noqa: F401

env_folder = os.path.dirname(sys.executable)
r_folder = str(Path(env_folder) / "Lib/R")
assert Path(r_folder).exists()
os.environ['R_HOME'] = r_folder

ias_output_prefix = 'tv_fy4'


def test():
    pass