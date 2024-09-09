
from pathlib import Path
from typing import List
from warnings import warn

from PIL import Image

import src.helpers.os_helpers  # noqa: F401
from src.helpers.io_helpers import replace_fname_end
from src.helpers.io_helpers import tags_to_files, tag_to_fname
from src.helpers.image_tools import crop_monocolor_borders, split_image, Direction, grid_images, remove_strip


class EddyImgPostProcess():
    def __init__(self, main_path, out_prefix, img_ext='.png'):
        self.main_path = Path(main_path)
        self.out_prefix = out_prefix
        self.img_ext = img_ext

        self.paths_exclude_from_arc: List[Path] = []

    def tag_to_img_fname(self, tag):
        return tag_to_fname(self.main_path, self.out_prefix, tag, self.img_ext)

    def tags_to_img_fnames(self, tags, exclude_missing=True, warn_if_missing=True):
        return tags_to_files(self.main_path, self.out_prefix, tags, self.img_ext,
                             exclude_missing, warn_if_missing)

    def process_heatmaps(self, img_tags: List[str], tags_skip_legend: List[str],
                         map_postfix: str, legend_postfix: str):
        tp = self.tags_to_img_fnames(img_tags)

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

            self.paths_exclude_from_arc += [path]

    def merge_heatmaps(self, merges, del_postfix, postfix):
        for merge in merges:
            tp = self.tags_to_img_fnames(merge)
            if len(tp) != 3:
                warn(f"Cannot merge {merge}, files missing")
                continue

            imgs = [Image.open(path) for path in list(tp.values())]
            merged = grid_images(imgs, 3)

            path = tp[merge[1]]
            tag = merge[1]
            fname = replace_fname_end(path, tag, tag.replace(del_postfix, '') + postfix)
            merged.save(fname)

            self.paths_exclude_from_arc += list(tp.values())

    def process_fluxes(self, img_tags: List[str], postfix):
        tp = self.tags_to_img_fnames(img_tags)
        for tag, path in tp.items():
            img = Image.open(path)

            title, graph = split_image(img, Direction.VERTICAL, 2)
            c_title, c_graph = crop_monocolor_borders(title, sides='TB'), crop_monocolor_borders(graph, sides='TB')
            fixed = grid_images([c_title, c_graph], 1)

            fname = replace_fname_end(path, tag, tag + postfix)
            fixed.save(fname)

            self.paths_exclude_from_arc += [path]

    def process_diurnal_cycles(self, img_tags: List[str], postfix):
        tp = self.tags_to_img_fnames(img_tags)
        for tag, path in tp.items():
            img = Image.open(path)

            title, g1, g2, g3, g4 = split_image(img, Direction.VERTICAL, 5)
            c_title = remove_strip(title, Direction.HORIZONTAL, 0.5)
            c_title = crop_monocolor_borders(c_title, sides='TB')
            fixed = grid_images([c_title, g1, g2, g3, g4], 1)

            fname = replace_fname_end(path, tag, tag + postfix)
            fixed.save(fname)

            self.paths_exclude_from_arc += [path]


