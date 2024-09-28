from typing import List, Tuple, Union

import src.ipynb_globals as ig
from src.reddyproc.postprocess import create_archive
from src.reddyproc.postprocess_graphs import EProcOutputHandler, EProcImgTagHandler, EProcOutputGen
from src.colab_routines import add_download_button, no_scroll

is_ustar = ig.eddyproc.options.is_to_apply_u_star_filtering
f_suffix = 'uStar_f' if is_ustar else 'f'
output_sequence: Tuple[Union[List[str], str], ...] = (
    "## Тепловые карты",
    EProcOutputGen.hmap_compare_row('NEE', f_suffix),
    EProcOutputGen.hmap_compare_row('LE', 'f'),
    EProcOutputGen.hmap_compare_row('H', 'f'),
    "## Суточный ход",
    EProcOutputGen.diurnal_cycle_row('NEE', f_suffix),
    EProcOutputGen.diurnal_cycle_row('LE', 'f'),
    EProcOutputGen.diurnal_cycle_row('H', 'f'),
    "## 30-минутные потоки",
    EProcOutputGen.flux_compare_row('NEE', f_suffix),
    EProcOutputGen.flux_compare_row('LE', 'f'),
    EProcOutputGen.flux_compare_row('H', 'f')
)

tag_handler = EProcImgTagHandler(main_path='output/reddyproc',
                                 eddy_loc_prefix=ig.eddyproc.out_info.fnames_prefix, img_ext='.png')
eio = EProcOutputHandler(output_sequence=output_sequence, tag_handler=tag_handler, out_info=ig.eddyproc.out_info)
eio.prepare_images()

arc_path = create_archive(dir='output/reddyproc', arc_fname=ig.eddyproc.out_info.fnames_prefix + '.zip',
                          include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=eio.img_proc.raw_img_duplicates)
add_download_button(arc_path, 'Download outputs')

no_scroll()
eio.display_images()

tag_handler.display_tag_info(eio.extended_tags())
