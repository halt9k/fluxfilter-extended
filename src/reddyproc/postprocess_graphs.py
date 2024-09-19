import textwrap
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import List
from warnings import warn

from IPython.core.display import Markdown
from IPython.display import display

from PIL import Image

import src.helpers.os_helpers  # noqa: F401
from src.ipynb_helpers import display_image_row
from src.helpers.io_helpers import replace_fname_end
from src.helpers.io_helpers import tags_to_files, tag_to_fname
from src.helpers.image_tools import crop_monocolor_borders, split_image, Direction, grid_images, remove_strip

PostProcSuffixes = SimpleNamespace(LEGEND='_legend', MAP='_map', COMPACT='_compact')
EddyPrefixes = SimpleNamespace(HEAT_MAP='FP', FLUX='Flux', DIURNAL='DC', DAILY_SUM='DSum', DAILY_SUMU='DSumU')


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
        suffixes_list = list(vars(PostProcSuffixes).values())

        def remove_suffixes(s, suffixes):
            for sub in suffixes:
                s = s.removesuffix(sub)
            return s

        raw_with_dupes = [remove_suffixes(ex_tag, suffixes_list) for ex_tag in extended_tags]
        raw_tags = list(set(raw_with_dupes))

        raw_heatmaps = [tag for tag in raw_tags if tag.startswith(EddyPrefixes.HEAT_MAP + '_')]
        raw_fluxes = [tag for tag in raw_tags if tag.startswith(EddyPrefixes.FLUX + '_')]
        raw_diurnal = [tag for tag in raw_tags if tag.startswith(EddyPrefixes.DIURNAL + '_')]
        raw_daily = [tag for tag in raw_tags if tag.startswith(EddyPrefixes.DAILY_SUM + '_')]
        return raw_heatmaps, raw_fluxes, raw_diurnal, raw_daily

    def display_tag_info(self, extended_tags):
        img_names = [Path(path).name for path in Path(self.main_path).glob(self.loc_prefix + '_*' + self.img_ext)]
        possible_tags = [name.removeprefix(self.loc_prefix + '_').removesuffix(self.img_ext) for name in img_names]

        def detect_prefix(s, prefixes):
            s = tag.partition('_')[0]
            if s not in prefixes:
                warn('Unexpected file name start: ' + s)
            return s

        prefixes_list = list(vars(EddyPrefixes).values())
        final_print = '\nUnused and ' + '[used]' + ' tags: '
        last_prefix = ''
        for tag in sorted(possible_tags):
            prefix = detect_prefix(tag, prefixes_list)
            if last_prefix != prefix:
                final_print += '\n\n'
            final_print += f'[{tag}]' if tag in extended_tags else tag
            final_print += ' '
            last_prefix = prefix

        lines = textwrap.wrap(final_print + '\n', replace_whitespace=False,
                              break_long_words=False)

        class PyPrint:
            BOLD = '\033[1m'
            END = '\033[0m'

        for line in lines:
            repl = line.replace('[', PyPrint.BOLD).replace(']', PyPrint.END)
            print(repl)


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
    def hmap_compare_row(col_name, suffix):
        fp, cn, sf = EddyPrefixes.HEAT_MAP, col_name, suffix
        return [f'{fp}_{cn}_map', f'{fp}_{cn}_{sf}_map', f'{fp}_{cn}_{sf}_legend']

    @staticmethod
    def diurnal_cycle_row(col_name, suffix):
        # for example, 'DC_NEE_uStar_f_compact'
        dc, cn, sf = EddyPrefixes.DIURNAL, col_name, suffix
        return [f'{dc}_{cn}_{sf}_compact']

    @staticmethod
    def flux_compare_row(col_name, suffix):
        # for example, ['Flux_NEE_compact', 'Flux_NEE_uStar_f_compact'],
        fl, cn, sf = EddyPrefixes.FLUX, col_name, suffix
        return [f'{fl}_{cn}_compact', f'{fl}_{cn}_{sf}_compact']

    def extended_tags(self):
        # in one list, exclude markdown text
        return [tag for tag_list in self.output_sequence if type(tag_list) is list for tag in tag_list]

    def prepare_images(self):
        heatmaps, fluxes, diurnal, daily = self.tag_handler.extract_raw_img_tags(self.extended_tags())

        tp = self.tag_handler.tags_to_img_fnames(heatmaps)
        for tag, path in tp.items():
            self.img_proc.process_heatmap(tag, path, map_postfix='_map', legend_postfix='_legend')

        img_rows = [tag_list for tag_list in self.output_sequence if type(tag_list) is list]
        merges = [row for row in img_rows if row[0].startswith(EddyPrefixes.HEAT_MAP)]
        for merge in merges:
            tp = self.tag_handler.tags_to_img_fnames(merge)
            self.img_proc.merge_heatmap(tp, del_postfix='_map', postfix='_all')

        tp = self.tag_handler.tags_to_img_fnames(fluxes)
        for tag, path in tp.items():
            self.img_proc.process_flux(tag, path, postfix='_compact')

        tp = self.tag_handler.tags_to_img_fnames(diurnal)
        for tag, path in tp.items():
            self.img_proc.process_diurnal_cycle(tag, path, postfix='_compact')

    def display_images(self):
        for output_step in self.output_sequence:
            if type(output_step) is str:
                title_text = output_step
                display(Markdown(title_text))
            elif type(output_step) is list:
                paths = self.tag_handler.tags_to_img_fnames(output_step)
                display_image_row(list(paths.values()))
            else:
                raise Exception("Wrong OUTPUT_HEADERS contents")
