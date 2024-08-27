import io
from typing import List

from IPython.core.display import Markdown
from IPython.display import display
from PIL import Image
from ipywidgets import HBox, widgets

import glob
import src.helpers.os_helpers  # noqa: F401
from src.helpers.image_tools import crop_borders, split_image_vertical

all_img_paths = []


def update_img_list(ls):
    ls[:] = glob.glob('output/REddyProc/*.png')


def get_unique_path(fname_end):
    fname_end = fname_end + '.'
    img = [path for path in all_img_paths if fname_end in path]
    found_matches = len(img)
    assert found_matches == 1, f"Expected 1 file: {fname_end} found {found_matches}"
    return img[0]


def display_image_row(paths):
    img_widgets = []
    for path in paths:
        byte_arr = io.BytesIO()
        Image.open(path).save(byte_arr, format='PNG')
        img_widgets += [widgets.Image(value=byte_arr.getvalue(), format="PNG")]

    hbox = HBox(img_widgets)
    display(hbox)


# TODO extract to tests to simplify non-Jupiter run?
def prepare_images(crop: List[str], crop_postfix,  remove_legends: List[str], removed_legend_postfix):
    update_img_list(all_img_paths)
    for tag in crop:
        path = get_unique_path(tag)
        new_path = path.replace('.png', crop_postfix + '.png')

        img = Image.open(path)
        cropped = crop_borders(img)
        cropped.save(new_path)

    update_img_list(all_img_paths)

    for tag in remove_legends:
        path = get_unique_path(tag)
        new_path = path.replace('.png', removed_legend_postfix + '.png')

        img = Image.open(path)
        cropped = crop_borders(img)
        left, _ = split_image_vertical(cropped)
        left.save(new_path)


def display_images(output_order):
    update_img_list(all_img_paths)

    for output_step in output_order:
        if type(output_step) is str:
            title_text = output_step
            display(Markdown("## " + title_text))
        elif type(output_step) is list:
            paths = [get_unique_path(tag) for tag in output_step]
            display_image_row(paths)
        else:
            raise Exception("Wrong OUTPUT_HEADERS contents")
