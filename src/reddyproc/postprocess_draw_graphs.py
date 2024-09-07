import io
from pathlib import Path
from typing import List

from IPython.core.display import Markdown
from IPython.display import display
from PIL import Image
from ipywidgets import HBox, widgets

import src.helpers.os_helpers  # noqa: F401
from src.helpers.image_tools import crop_monocolor_borders, split_image, Direction, grid_images


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

    def process_heatmaps(self, img_tags: List[str], tags_omit_legend: List[str], legend_fname_postfix: str):
        tp = get_tag_paths(img_tags + tags_omit_legend, self.main_path)

        for tag, path in tp.items():
            img = Image.open(path)

            map, legend, _ = split_image(img, Direction.HORIZONTAL, 3)
            map = crop_monocolor_borders(map, sides='LR')
            legend = crop_monocolor_borders(legend, sides='LR')

            path.replace(self.bkp_path / path.name)
            map.save(path)

            legend_fname = replace_fname_end(path.name, tag, tag + legend_fname_postfix)
            legend_dir = self.bkp_path if tag in tags_omit_legend else self.main_path
            legend.save(legend_dir / legend_fname)

    def process_fluxes(self, img_tags: List[str]):
        tp = get_tag_paths(img_tags, self.main_path)
        for tag, path in tp.items():
            img = Image.open(path)

            title, graph = split_image(img, Direction.VERTICAL, 2)
            c_title, c_graph = crop_monocolor_borders(title, sides='TB'), crop_monocolor_borders(graph, sides='TB')
            fixed = grid_images([c_title, c_graph], 1)

            path.replace(self.bkp_path / path.name)
            fixed.save(path)

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
            display(Markdown(title_text))
        elif type(output_step) is list:
            paths = [get_tag_paths(tag, MAIN_IMG_DIR) for tag in output_step]
            display_image_row(paths)
        else:
            raise Exception("Wrong OUTPUT_HEADERS contents")
