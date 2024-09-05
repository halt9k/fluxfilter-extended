import io
from pathlib import Path
from typing import List, Union

from IPython.core.display import Markdown
from IPython.display import display
from PIL import Image
from ipywidgets import HBox, widgets

import glob
import src.helpers.os_helpers  # noqa: F401
from src.helpers.image_tools import crop_borders, split_image_vertical


RAW_EDDY_DIR = 'output/REddyProc'


def get_tag_paths(tags: Union[str, List[str]], dir = RAW_EDDY_DIR, ext ='.png'):
    # tags are same as unique file name endings
    # file must exist

    tags_arr = [tags] if type(tags) is str else tags
    all_img_paths = Path(dir).glob('*' + ext)

    result = []
    for tag in tags_arr:
        fname_end = tag + ext
        matches = [path for path in all_img_paths if str(path).endswith(fname_end)]
        assert matches == 1, f"Expected 1 file: {fname_end} found {matches}"
        result += (tag, matches[0])

    return result[0] if type(tags) is str else result


def replace_fname_end(fname, tag, new_tag):
    return fname.replace(tag + '.', new_tag + '.')


def extract_legends(img_tags, in_dir, out_dir, legend_postfix):

    pass



def prepare_images(tags_crop: List[str], crop_postfix,
                   remove_legends: List[str], removed_legend_postfix):

    tp = get_tag_paths(tags_crop)
    for tag, path in tp:
        new_path = replace_fname_end(path, tag, tag + crop_postfix)

        img = Image.open(path)
        cropped = crop_borders(img)
        cropped.save(new_path)

    tp = get_tag_paths(remove_legends)
    for tag, path in tp:
        new_path = replace_fname_end(path, tag, tag + removed_legend_postfix)

        img = Image.open(path)
        cropped = crop_borders(img)
        left, _ = split_image_vertical(cropped)
        left.save(new_path)


def display_image_row(paths):
    img_widgets = []
    for path in paths:
        byte_arr = io.BytesIO()
        Image.open(path).save(byte_arr, format='PNG')
        img_widgets += [widgets.Image(value=byte_arr.getvalue(), format="PNG")]

    hbox = HBox(img_widgets)
    display(hbox)


def display_images(output_order):
    for output_step in output_order:
        if type(output_step) is str:
            title_text = output_step
            display(Markdown("## " + title_text))
        elif type(output_step) is list:
            paths = [get_tag_paths(tag) for tag in output_step]
            display_image_row(paths)
        else:
            raise Exception("Wrong OUTPUT_HEADERS contents")
