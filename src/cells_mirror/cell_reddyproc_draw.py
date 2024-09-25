import src.ipynb_globals as ig
from src.reddyproc.postprocess import create_archive
from src.reddyproc.postprocess_graphs import EddyOutput, EddyImgTagHandler
from src.colab_routines import add_download_button, no_scroll

is_ustar = ig.eddyproc.options.is_to_apply_u_star_filtering
usuffix = 'uStar_f' if is_ustar else 'f'
output_sequence = (
    "## Тепловые карты",
    EddyOutput.hmap_compare_row('NEE', usuffix),
    EddyOutput.hmap_compare_row('LE', 'f'),
    EddyOutput.hmap_compare_row('H', 'f'),
    "## Суточный ход",
    EddyOutput.diurnal_cycle_row('NEE', usuffix),
    EddyOutput.diurnal_cycle_row('LE', 'f'),
    EddyOutput.diurnal_cycle_row('H', 'f'),
    "## 30-минутные потоки",
    EddyOutput.flux_compare_row('NEE', usuffix),
    EddyOutput.flux_compare_row('LE', 'f'),
    EddyOutput.flux_compare_row('H', 'f')
)

tag_handler = EddyImgTagHandler(main_path='output/reddyproc',
                                eddy_loc_prefix=ig.eddyproc.out_info.fnames_prefix, img_ext='.png')
eio = EddyOutput(output_sequence=output_sequence, tag_handler=tag_handler, out_info=ig.eddyproc.out_info)
eio.prepare_images()

arc_path = create_archive(dir='output/reddyproc', arc_fname=ig.eddyproc.out_info.fnames_prefix + '.zip',
                          include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=eio.img_proc.raw_img_duplicates)
add_download_button(arc_path, 'Download all images')

no_scroll()
eio.display_images()

tag_handler.display_tag_info(eio.extended_tags())
