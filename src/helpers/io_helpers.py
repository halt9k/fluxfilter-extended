from pathlib import Path
from typing import List, Union
import warnings


def tag_to_fname(dir: Path, prefix, tag, ext):
    return dir / (prefix + '_' + tag + ext)


def tags_to_files(dir, prefix, tags, ext, exclude_missing=True, warn_if_missing=True):
    res = {}
    for tag in tags:
        fname = Path(tag_to_fname(dir, prefix, tag, ext))
        if not fname.exists():
            if warn_if_missing:
                warnings.warn(f"Image is missing: {fname}")
            if exclude_missing:
                continue
        res[tag] = fname
    return res


def replace_fname_end(path: Path, tag: str, new_tag: str):
    return path.parent / path.name.replace(tag + '.', new_tag + '.')


def ensure_empty_dir(folder: Union[str, Path]):
    if type(folder) is str:
        folder = Path(folder)
    folder.mkdir(exist_ok=True)
    for path in folder.iterdir():
        if path.is_file():
            path.unlink()