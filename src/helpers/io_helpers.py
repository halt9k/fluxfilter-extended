from pathlib import Path
from typing import List, Union
from warnings import warn


def tag_to_fname(dir: Path, prefix, tag, ext):
    return dir / (prefix + '_' + tag + ext)


def tags_to_files(dir, prefix, tags, ext, exclude_missing=True, warn_if_missing=True):
    # meaning of tags here is unique file name endings
    # Test_site_2024_Hd_f.png -> tag is Hd_f

    res = {}
    for tag in tags:
        fname = Path(tag_to_fname(dir, prefix, tag, ext))
        if not fname.exists():
            if warn_if_missing:
                warn(f"Image is missing: {fname}")
            if exclude_missing:
                continue
        res[tag] = fname
    return res


def replace_fname_end(path: Path, tag: str, new_tag: str):
    return path.parent / path.name.replace(tag + '.', new_tag + '.')


def ensure_empty_dir(folder: Union[str, Path]):
    if type(folder) is str:
        folder = Path(folder)

    folder.mkdir(parents=True, exist_ok=True)
    for path in folder.iterdir():
        if path.is_file():
            path.unlink()
