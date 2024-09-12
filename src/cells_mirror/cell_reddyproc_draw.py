
from src.ipynb_globals import *
from src.reddyproc.postprocess import create_archive
from src.reddyproc.postprocess_graphs import EddyImgPostProcess
from src.colab_routines import add_download_button, no_scroll
from src.ipynb_helpers import display_images

# Ipynb is not true code, that's excuse for unicode
OUTPUT_ORDER = (
    "## Тепловые карты",
    ['FP_NEE_map', 'FP_NEE_uStar_f_map', 'FP_NEE_uStar_f_legend'],
    ['FP_LE_map', 'FP_LE_f_map', 'FP_LE_f_legend'],
    ['FP_H_map', 'FP_H_f_map', 'FP_H_f_legend'],
    "## Суточный ход",
    ['DC_NEE_uStar_f_compact'],
    ['DC_LE_f_compact'],
    ['DC_H_f_compact'],
    "## 30-минутные потоки",
    ['Flux_NEE_compact', 'Flux_NEE_uStar_f_compact'],
    ['Flux_LE_compact', 'Flux_LE_f_compact'],
    ['Flux_H_compact', 'Flux_H_f_compact']
)

eipp = EddyImgPostProcess('output/reddyproc', eddy_out_prefix)
eipp.extract_img_tags(OUTPUT_ORDER)

eipp.display_tag_info()

eipp.prepare_images()
eipp.merge_heatmaps([['FP_NEE_map', 'FP_NEE_uStar_f_map', 'FP_NEE_uStar_f_legend'],
                     ['FP_LE_map', 'FP_LE_f_map', 'FP_LE_f_legend'],
                     ['FP_H_map', 'FP_H_f_map', 'FP_H_f_legend']],
                    del_postfix='_map', postfix='_all')

no_scroll()
display_images(OUTPUT_ORDER, main_path='output/reddyproc', prefix=eddy_out_prefix)

arc_path = create_archive(dir='output/reddyproc', arc_fname=eddy_out_prefix + '.zip',
                          include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=eipp.imgs_before_postprocess)
add_download_button(arc_path, 'Download all images')