import textwrap
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

POSTPROC_SUFFIXES = SimpleNamespace(legend='_legend', map='_map', compact='_compact')
EDDY_PREFIXES = SimpleNamespace(heat_map='FP_', flux='Flux_', diurnal='DC_', daily_sum='DSum')


class EddyImgTagHandler:
    def __init__(self, main_path, eddy_loc_prefix, img_ext='.png'):
        self.main_path = Path(main_path)
        self.loc_prefix = eddy_loc_prefix
        self.img_ext = img_ext

    def tag_to_img_fname(self, tag):
        return tag_to_fname(self.main_path, self.loc_prefix, tag, self.img_ext)

    def tags_to_img_fnames(self, tags, exclude_missing=True, warn_if_missing=True):
        return tags_to_files(self.main_path, self.loc_prefix, tags, self.img_ext,
                             exclude_missing, warn_if_missing)

    def extract_raw_img_tags(self, extended_tags):
        suffixes_list = list(vars(POSTPROC_SUFFIXES).values())

        def remove_suffixes(s, suffixes):
            for sub in suffixes:
                 s = s.removesuffix(sub)
            return s

        raw_with_dupes = [remove_suffixes(ex_tag, suffixes_list) for ex_tag in extended_tags]
        raw_tags = list(set(raw_with_dupes))

        raw_heatmaps = [tag for tag in raw_tags if tag.startswith(EDDY_PREFIXES.heat_map)]
        raw_fluxes = [tag for tag in raw_tags if tag.startswith(EDDY_PREFIXES.flux)]
        raw_diurnal = [tag for tag in raw_tags if tag.startswith(EDDY_PREFIXES.diurnal)]
        raw_daily = [tag for tag in raw_tags if tag.startswith(EDDY_PREFIXES.daily_sum)]
        return raw_heatmaps, raw_fluxes, raw_diurnal, raw_daily

    def display_tag_info(self, extended_tags):
        img_names = [Path(path).name for path in Path(self.main_path).glob(self.loc_prefix + '_*' + self.img_ext)]
        possible_tags = [name.removeprefix(self.loc_prefix + '_').removesuffix(self.img_ext) for name in img_names]

        def detect_pefix(s, prefixes):
            for p in prefixes:
                 if s.startswith(p):
                    return p
            warn('Unexpected file name start: ' + s)
            return s

        def bold(s):
            class PyPrint:
                BOLD = '\033[1m'
                END = '\033[0m'
            return PyPrint.BOLD + s + PyPrint.END

        prefixes_list = list(vars(EDDY_PREFIXES).values())
        final_print = '\nUnused and ' + bold('used') + ' tags: '
        last_prefix = ''
        for tag in sorted(possible_tags):
            prefix = detect_pefix(tag, prefixes_list)
            if last_prefix != prefix:
                final_print += '\n'
            final_print += bold(tag) if tag in extended_tags else tag
            final_print += ' '
            last_prefix = prefix

        print(textwrap.wrap(final_print + '\n'))


class EddyImgPostProcess:
    def __init__(self):
        self.raw_img_duplicates: List[Path] = []

    def process_heatmap(self, tag, path, map_postfix: str, legend_postfix: str):
        img = Image.open(path)

        map, legend, _ = split_image(img, Direction.HORIZONTAL, 3)
        map = crop_monocolor_borders(map, sides='LR')
        legend = crop_monocolor_borders(legend, sides='LR')

        fname = replace_fname_end(path, tag, tag + map_postfix)
        map.save(fname)

        fname = replace_fname_end(path, tag, tag + legend_postfix)
        legend.save(fname)

        self.raw_img_duplicates += [path]

    def merge_heatmap(self, tag_paths, del_postfix, postfix):
        if len(tag_paths) != 3:
            warn(f"Cannot merge {tag_paths.values()}, files missing")
            return

        paths = tag_paths.values()
        imgs = [Image.open(path) for path in paths]
        merged = grid_images(imgs, 3)

        tag = list(tag_paths)[0]
        path = tag_paths[tag]
        fname = replace_fname_end(path, tag, tag.replace(del_postfix, '') + postfix)
        merged.save(fname)

        self.raw_img_duplicates += paths

    def process_flux(self, tag, path, postfix):
        img = Image.open(path)

        title, graph = split_image(img, Direction.VERTICAL, 2)
        c_title, c_graph = crop_monocolor_borders(title, sides='TB'), crop_monocolor_borders(graph, sides='TB')
        fixed = grid_images([c_title, c_graph], 1)

        fname = replace_fname_end(path, tag, tag + postfix)
        fixed.save(fname)

        self.raw_img_duplicates += [path]

    def process_diurnal_cycle(self, tag, path, postfix):
            img = Image.open(path)

            title, g1, g2, g3, g4 = split_image(img, Direction.VERTICAL, 5)
            c_title = remove_strip(title, Direction.HORIZONTAL, 0.5)
            c_title = crop_monocolor_borders(c_title, sides='TB')
            fixed = grid_images([c_title, g1, g2, g3, g4], 1)

            fname = replace_fname_end(path, tag, tag + postfix)
            fixed.save(fname)

            self.raw_img_duplicates += [path]


class EddyOutput:
    # output is declared as auto generated on each run list of image tags
    # tags mean unique suffixes of image file names,
    # i.e. for 'tv_fy4_22-14_21-24_FP_Rg_f.png' tag is 'FP_Rg_f'
    # this allows both default auto-detected order of cell output by this class
    # or custom order if to declare output list manually in the notebook cell
    # auto generation is nessesary because order depends on reddyproc options

    def __init__(self, output_sequence, tag_handler):
        self.output_sequence = output_sequence
        self.tag_handler = tag_handler
        self.img_proc = EddyImgPostProcess()

    @staticmethod
    def default_sequence(is_ustar):
        # list: row of images, specified by image tag
        # text: Markdown

        def hmap_compare_row(col_name, suffix):
            hm, cn, sf = EDDY_PREFIXES.heat_map, col_name, suffix
            return [f'FP_{cn}_map', f'FP_{cn}_{sf}_map', f'FP_{cn}_{sf}_legend']

        def diurnal_cycle_row(col_name, suffix):
            # for example, 'DC_NEE_uStar_f_compact'
            cn, sf = col_name, suffix
            return [f'DC_{cn}_{sf}_compact']

        def flux_compare_row(col_name, suffix):
            # for example, ['Flux_NEE_compact', 'Flux_NEE_uStar_f_compact'],
            cn, sf = col_name, suffix
            return [f'Flux_{cn}_compact', f'Flux_{cn}_{sf}_compact']

        return (
            "## Тепловые карты",
            hmap_compare_row('NEE', 'uStar_f' if is_ustar else 'f'),
            hmap_compare_row('LE', 'f'),
            hmap_compare_row('H', 'f'),
            "## Суточный ход",
            diurnal_cycle_row('NEE', 'uStar_f' if is_ustar else 'f'),
            diurnal_cycle_row('LE', 'f'),
            diurnal_cycle_row('H', 'f'),
            "## 30-минутные потоки",
            flux_compare_row('NEE', 'uStar_f' if is_ustar else 'f'),
            flux_compare_row('LE', 'f'),
            flux_compare_row('H', 'f')
        )

    def extended_tags(self):
        # in one list, exclude markdown text
        return [tag for tag_list in self.output_sequence if type(tag_list) is list for tag in tag_list]

    def prepare_images(self):
        heatmaps, fluxes, diurnal, daily = self.tag_handler.extract_raw_img_tags(self.extended_tags())

        tp = self.tag_handler.tags_to_img_fnames(heatmaps)
        for tag, path in tp.items():
            self.img_proc.process_heatmap(tag, path, map_postfix='_map', legend_postfix='_legend')

        img_rows = [tag_list for tag_list in self.output_sequence if type(tag_list) is list]
        merges = [row for row in img_rows if row[0].startswith(EDDY_PREFIXES.heat_map) ]
        for merge in merges:
            tp = self.tag_handler.tags_to_img_fnames(merge)
            self.img_proc.merge_heatmap(tp, del_postfix='_map', postfix='_all')

        tp = self.tag_handler.tags_to_img_fnames(fluxes)
        for tag, path in tp.items():
            self.img_proc.process_flux(tag, path, postfix='_compact')

        tp = self.tag_handler.tags_to_img_fnames(diurnal)
        for tag, path in tp.items():
            self.img_proc.process_diurnal_cycle(tag, path, postfix='_compact')
