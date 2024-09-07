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


def replace_fname_end(path: Path, tag: str, new_tag: str):
    return path.parent / path.name.replace(tag + '.', new_tag + '.')


class EddyImgPostProcess():
    def __init__(self, main_path, bkp_path):
        self.main_path = Path(main_path)

    def process_heatmaps(self, img_tags: List[str], tags_skip_legend: List[str],
                         map_postfix: str, legend_postfix: str):
        tp = get_tag_paths(img_tags + tags_skip_legend, self.main_path)

        for tag, path in tp.items():
            img = Image.open(path)

            map, legend, _ = split_image(img, Direction.HORIZONTAL, 3)
            map = crop_monocolor_borders(map, sides='LR')
            legend = crop_monocolor_borders(legend, sides='LR')

            fname = replace_fname_end(path, tag, tag + map_postfix)
            map.save(fname)

            if tag not in tags_skip_legend:
                fname = replace_fname_end(path, tag, tag + legend_postfix)
                legend.save(fname)

    def merge_heatmaps(self, merges, del_postfix, postfix):
        for merge in merges:
            tp = get_tag_paths(merge, self.main_path)
            if len(tp) != 3:
                print(f"WARNING: cannot merge {merge}, files missing")
                continue

            imgs = [Image.open(path) for path in list(tp.values())]
            merged = grid_images(imgs, 3)

            path = tp[merge[1]]
            tag = merge[1]
            fname = replace_fname_end(path, tag, tag.replace(del_postfix, '') + postfix)
            merged.save(fname)

    def process_fluxes(self, img_tags: List[str], postfix):
        tp = get_tag_paths(img_tags, self.main_path)
        for tag, path in tp.items():
            img = Image.open(path)

            title, graph = split_image(img, Direction.VERTICAL, 2)
            c_title, c_graph = crop_monocolor_borders(title, sides='TB'), crop_monocolor_borders(graph, sides='TB')
            fixed = grid_images([c_title, c_graph], 1)

            fname = replace_fname_end(path, tag, tag + postfix)
            fixed.save(fname)


def display_image_row(paths):
    img_widgets = []
    for path in paths:
        byte_arr = io.BytesIO()
        Image.open(path).save(byte_arr, format='PNG')
        img_widgets += [widgets.Image(value=byte_arr.getvalue(), format="PNG")]

    hbox = HBox(img_widgets)
    display(hbox)


def display_images(output_order, main_path):
    for output_step in output_order:
        if type(output_step) is str:
            title_text = output_step
            display(Markdown(title_text))
        elif type(output_step) is list:
            paths = get_tag_paths(output_step, main_path)
            display_image_row(list(paths.values()))
        else:
            raise Exception("Wrong OUTPUT_HEADERS contents")
