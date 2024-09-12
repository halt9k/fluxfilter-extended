from pathlib import Path
from types import SimpleNamespace
from typing import List
from warnings import warn

from IPython.core.display import Markdown
from IPython.display import display

from PIL import Image

import src.helpers.os_helpers  # noqa: F401
from src.helpers.io_helpers import replace_fname_end
from src.helpers.io_helpers import tags_to_files, tag_to_fname
from src.helpers.image_tools import crop_monocolor_borders, split_image, Direction, grid_images, remove_strip


class EddyImgPostProcess():
    suffixes = SimpleNamespace(legend='_legend', map='_map', compact='_compact')
    prefixes = SimpleNamespace(heat_map='FP_', flux='Flux_', diurnal='DC_', daily_sum='DSum')

    def __init__(self, main_path, out_prefix, img_ext='.png'):
        self.main_path = Path(main_path)
        self.out_prefix = out_prefix
        self.img_ext = img_ext
        self.imgs_before_postprocess: List[Path] = []
        self.requested_extended_tags: List[str] = []
        self.requested_tags: List[str] = []

    def tag_to_img_fname(self, tag):
        return tag_to_fname(self.main_path, self.out_prefix, tag, self.img_ext)

    def tags_to_img_fnames(self, tags, exclude_missing=True, warn_if_missing=True):
        return tags_to_files(self.main_path, self.out_prefix, tags, self.img_ext,
                             exclude_missing, warn_if_missing)

    def process_heatmaps(self, img_tags: List[str], map_postfix: str, legend_postfix: str,
                         tags_skip_legend: List[str] = None):
        tp = self.tags_to_img_fnames(img_tags)

        for tag, path in tp.items():
            img = Image.open(path)

            map, legend, _ = split_image(img, Direction.HORIZONTAL, 3)
            map = crop_monocolor_borders(map, sides='LR')
            legend = crop_monocolor_borders(legend, sides='LR')

            fname = replace_fname_end(path, tag, tag + map_postfix)
            map.save(fname)

            if tags_skip_legend and tag not in tags_skip_legend:
                fname = replace_fname_end(path, tag, tag + legend_postfix)
                legend.save(fname)

            self.imgs_before_postprocess += [path]

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

            self.imgs_before_postprocess += list(tp.values())

    def process_fluxes(self, img_tags: List[str], postfix):
        tp = self.tags_to_img_fnames(img_tags)
        for tag, path in tp.items():
            img = Image.open(path)

            title, graph = split_image(img, Direction.VERTICAL, 2)
            c_title, c_graph = crop_monocolor_borders(title, sides='TB'), crop_monocolor_borders(graph, sides='TB')
            fixed = grid_images([c_title, c_graph], 1)

            fname = replace_fname_end(path, tag, tag + postfix)
            fixed.save(fname)

            self.imgs_before_postprocess += [path]

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

            self.imgs_before_postprocess += [path]

    def display_tag_info(self):
        img_names = [Path(path).name for path in Path(self.main_path).glob(self.out_prefix + '_*' + self.img_ext)]
        possible_tags = [name.removeprefix(self.out_prefix + '_').removesuffix(self.img_ext) for name in img_names]

        def which_pefix(s, prefixes):
            for p in prefixes:
                 if s.startswith(p):
                    return p
            warn('Unexpected file name start: ' + s)
            return s

        prefixes_list = list(vars(self.prefixes).values())
        final_print = 'All possible and **used** tags: <br>'
        last_prefix = ''
        for tag in sorted(possible_tags):
            prefix = which_pefix(tag, prefixes_list)
            if last_prefix != prefix:
                final_print += '<br>'
            final_print += f'**{tag}** ' if tag in self.requested_extended_tags else tag + ' '
            last_prefix = prefix

        display(Markdown(final_print + '<br>'))

    def extended_tags_to_raw_tags(self, ex_tags):
        suffixes_list = list(vars(self.suffixes).values())

        def remove_suffixes(s, suffixes):
            for sub in suffixes:
                 s = s.removesuffix(sub)
            return s

        return [remove_suffixes(ex_tag, suffixes_list) for ex_tag in ex_tags]

    def extract_img_tags(self, output_order):
        self.requested_extended_tags = [tag for tag_list in output_order if type(tag_list) is list for tag in tag_list]

        # may contain duplicates NEE_map NEE_legend
        requested_tags = self.extended_tags_to_raw_tags(self.requested_extended_tags)

        self.requested_tags = list(set(requested_tags))

    def prepare_images(self):
        need_heatmaps = [tag for tag in self.requested_tags if tag.startswith(self.prefixes.heat_map)]
        need_fluxes = [tag for tag in self.requested_tags if tag.startswith(self.prefixes.flux)]
        need_diurnal = [tag for tag in self.requested_tags if tag.startswith(self.prefixes.diurnal)]
        need_daily = [tag for tag in self.requested_tags if tag.startswith(self.prefixes.daily_sum)]

        self.process_heatmaps(img_tags=need_heatmaps, map_postfix='_map', legend_postfix='_legend')
        self.process_fluxes(img_tags=need_fluxes, postfix='_compact')
        self.process_diurnal_cycles(img_tags=need_diurnal, postfix='_compact')

