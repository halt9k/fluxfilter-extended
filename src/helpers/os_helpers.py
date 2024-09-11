import logging
import warnings
from os import chdir
from pathlib import Path
from sys import path

"""
 This module is intended to be imported before all other user modules.
 Allows to keep consistent imports root src.* when runnning from different dirs. 
 I.e. cmd */run_main.bat, ./main.py, tests start ./test/test_main.py, etc

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

    chdir(project_dir)
    print(f'Workaround for R lang "source" command: current dir is changed to {project_dir}.\n')


# autorun to make imports more readable
ch_project_root_dir()


def custom_show_warning(message, category, filename, lineno, file=None, line=None):
    # print(f'{filename}: {lineno} \n WARNING: {message}')
    print(f'WARNING: {message}')


# logging.captureWarnings(True)
warnings.showwarning = custom_show_warning