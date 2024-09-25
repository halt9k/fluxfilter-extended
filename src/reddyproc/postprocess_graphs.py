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
from src.helpers.image_tools import crop_monocolor_borders, Direction, grid_images, remove_strip, \
    ungrid_image

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
        final_print = '\nUnused and ' + '[used]' + ' tags in output_sequence: '
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
    def __init__(self, total_years):
        self.total_years = total_years
        self.raw_img_duplicates: List[Path] = []

    def ungrid_heatmap(self, img):
        tile_count = self.total_years + 1
        row_count = (tile_count - 1) // 3 + 1
        tiles_2d = ungrid_image(img, nx=3, ny=row_count)
        assert len(tiles_2d) == row_count and len(tiles_2d[0]) == 3

        tiles_ordered = [elem for row in tiles_2d for elem in row]
        legend_tile = tiles_ordered[tile_count - 1]

        year_tiles_stacked_vertically = grid_images(tiles_ordered[0: tile_count - 1], max_horiz=1)
        # just a copy of same legend
        legend_tiles_stacked_vertically = grid_images([legend_tile] * (tile_count - 1), max_horiz=1)
        return year_tiles_stacked_vertically, legend_tiles_stacked_vertically

    def compact_title_row(self, img, row_count):
        rows = ungrid_image(img, ny=row_count, flatten=True)
        title = remove_strip(rows[0], Direction.HORIZONTAL, 0.5)
        c_title = crop_monocolor_borders(title, sides='TB')
        fixed = grid_images([c_title] + rows[1: row_count], 1)
        return fixed

    def process_heatmap(self, tag, path, map_postfix: str, legend_postfix: str):
        img = Image.open(path)

        maps, legends = self.ungrid_heatmap(img)
        cmap = crop_monocolor_borders(maps, sides='LR')
        clegend = crop_monocolor_borders(legends, sides='LR')

        fname = replace_fname_end(path, tag, tag + map_postfix)
        cmap.save(fname)

        fname = replace_fname_end(path, tag, tag + legend_postfix)
        clegend.save(fname)

        self.raw_img_duplicates += [path]

    def merge_heatmap(self, tag_paths, del_postfix, postfix):
        if len(tag_paths) != 3:
            warn(f"Cannot merge {tag_paths.values()}, files missing")
            return

        paths = tag_paths.values()
        imgs = [Image.open(path) for path in paths]
        merged = grid_images(imgs, 3)

        tag = list(tag_paths)[1]
        path = tag_paths[tag]
        fname = replace_fname_end(path, tag, tag.replace(del_postfix, '') + postfix)
        merged.save(fname)

        self.raw_img_duplicates += paths

    def process_flux(self, tag, path, postfix):
        img = Image.open(path)
        fixed = self.compact_title_row(img, self.total_years + 1)
        fname = replace_fname_end(path, tag, tag + postfix)
        fixed.save(fname)

        self.raw_img_duplicates += [path]

    def process_diurnal_cycle(self, tag, path, postfix):
        img = Image.open(path)
        fixed = self.compact_title_row(img, 5)
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

    def __init__(self, output_sequence, tag_handler, out_info):
        self.output_sequence = output_sequence
        self.tag_handler = tag_handler

        total_years = out_info.end_year - out_info.start_year + 1
        assert total_years > 0
        self.img_proc = EddyImgPostProcess(total_years)

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
            assert all(tag.startswith(EddyPrefixes.HEAT_MAP) for tag in merge), \
                'Heatmap row does not contain 3 heatmaps'

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
