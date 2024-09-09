from os import chdir
from pathlib import Path
from sys import path

"""
 This module is intended to be imported before all other user modules.
 Allows to keep imports consistent both when command line start, tests start, etc
  For example, if sources are organized with working dir . as root:
 ./README.md
 ./run.bat
 ./src/*.py
 ./test/test_main.py
 ./src/helpers/os_helpers.py
 ./data/*

 Import without warning:
 from src.helpers import os_helpers  # noqa: F401
"""


def ch_project_root_dir():
    this_file_path = Path(__file__).parent
    assert this_file_path.name == 'helpers'

    src_dir = this_file_path.parent
    assert src_dir.name == 'src'

    project_dir = str(src_dir.parent)
    src_dir = str(src_dir)

    if src_dir in path:
        # ambigious imports can be broken
        path.remove(src_dir)
    if src_dir in path:
        # ambigious imports can be broken, dupe remove is nessesary somethimes
        path.remove(src_dir)
    assert src_dir not in path

    if project_dir not in path:
        path.append(project_dir)

    # Shortfix for R scripts consistency, consider removing later for dynamic tests
    chdir(project_dir)
    print(f'Working path is changed to {project_dir} \n')


# autorun to make imports more readable
ch_project_root_dir()


