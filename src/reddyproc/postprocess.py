import zipfile
from pathlib import Path
from typing import List
from zipfile import ZipFile


def create_archive(dir, arc_fname, include_fmask, exclude_files: List[str]):
    # move out of draw_graphs later

    folder = Path(dir)
    files = [path for path in folder.glob(include_fmask) if path not in exclude_files]

    arc_path = folder / arc_fname
    with ZipFile(arc_path, 'w', zipfile.ZIP_DEFLATED) as myzip:
        for file in files:
            myzip.write(file, file.name)

    return arc_path
