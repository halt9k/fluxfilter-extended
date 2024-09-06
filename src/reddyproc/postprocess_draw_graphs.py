import io
from pathlib import Path
from typing import List

from IPython.core.display import Markdown
from IPython.display import display
from PIL import Image
from ipywidgets import HBox, widgets

import src.helpers.os_helpers  # noqa: F401
from src.helpers.image_tools import crop_borders, split_image, Direction


def get_tag_paths(tags: List[str], dir, ext='.png', warn_if_missing=True):
    # tags are same as unique file name endings
    # file must exist

    all_img_paths = list(Path(dir).glob('*' + ext))

    result = {}
    for tag in tags:
        fname_end = tag + ext
        matches = [path for path in all_img_paths if str(path).endswith(fname_end)]

        if len(matches) > 1:
            raise Exception(f"Unexpected file duplicate: {matches}")
        elif len(matches) == 0 and warn_if_missing:
            print(f"WARNING: image is missing: {fname_end}")
            result[tag] = None
        else:
            result[tag] = Path(matches[0])

    return result


def get_tag_path(tag, dir, ext='.png', warn_if_missing=True):
    paths = get_tag_paths([tag], dir, ext, warn_if_missing)
    return paths[0] if len(paths) == 1 else None


def replace_fname_end(fname: Path, tag: str, new_tag: str):
    return Path(str(fname).replace(tag + '.', new_tag + '.'))


class PolishImages():
    def __init__(self, main_path, bkp_path):
        self.bkp_path = Path(bkp_path)
        self.main_path = Path(main_path)

        for path in self.bkp_path.iterdir():
            path.unlink()
        self.bkp_path.mkdir(exist_ok=True)

    def extract_heatmap_legends(self, img_tags: [str], tags_omit_legend: [str], legend_fname_postfix: str):
        hmaps = get_tag_paths(img_tags + tags_omit_legend, self.main_path)

        for tag, path in hmaps.items():
            img = Image.open(path)

            # cropped = crop_borders(img)
            map, legend, _ = split_image(img, Direction.HORIZONTAL, 3)

            fname_legend = replace_fname_end(path, tag, tag + legend_fname_postfix)
            path.replace(self.bkp_path / path.name)
            map.save(path)

            legend_fname = replace_fname_end(path.name, tag, tag + legend_fname_postfix)
            legend_dir = self.bkp_path if not tag in tags_omit_legend else self.main_path
            legend.save(legend_dir / legend_fname)


    def prepare_images(self, tags_crop: List[str], crop_postfix,
                       remove_legends: List[str], removed_legend_postfix):
        tp = get_tag_paths(tags_crop, self.main_path)
        for tag, path in tp:
            new_path = replace_fname_end(path, tag, tag + crop_postfix)

            img = Image.open(path)
            cropped = crop_borders(img)
            cropped.save(new_path)

        tp = get_tag_paths(remove_legends, self.main_path)
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
            paths = [get_tag_paths(tag, MAIN_IMG_DIR) for tag in output_step]
            display_image_row(paths)
        else:
            raise Exception("Wrong OUTPUT_HEADERS contents")
