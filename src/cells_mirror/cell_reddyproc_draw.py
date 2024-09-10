from src.globals import eddy_out_prefix
from src.reddyproc.postprocess import create_archive
from src.reddyproc.postprocess_graphs import EddyImgPostProcess
from src.colab_routines import add_download_button, no_scroll
from src.ipynb_helpers import display_images

# Full list of outputs (not all are included in OUTPUT_ORDER):
# 'DC_H_f', 'DC_LE_f', 'DC_NEE_uStar_f', 'DC_Rg_f', 'DC_rH_f', 'DC_Tair_f', 'DC_VPD_f',
# 'DSum_Rg_f', 'DSum_rH_f', 'DSum_Tair_f', 'DSum_VPD_f', 'DSumU_H_f', 'DSumU_LE_f', 'DSumU_NEE_uStar_f',
# 'Flux_H', 'Flux_H_f', 'Flux_LE', 'Flux_LE_f', 'Flux_NEE', 'Flux_NEE_uStar_f', 'Flux_Rg',
# 'Flux_Rg_f', 'Flux_rH', 'Flux_rH_f', 'Flux_Tair','Flux_Tair_f', 'Flux_VPD','Flux_VPD_f',
# 'FP_GPP_DT_uStar', 'FP_GPP_uStar_f', 'FP_H', 'FP_H_f', 'FP_LE', 'FP_LE_f', 'FP_NEE',
# 'FP_NEE_uStar_f', 'FP_Reco_DT_uStar', 'FP_Reco_uStar',
# 'FP_Rg', 'FP_Rg_f', 'FP_rH', 'FP_rH_f', 'FP_Tair', 'FP_Tair_f', 'FP_VPD', 'FP_VPD_f'

eipp = EddyImgPostProcess(main_path='output/reddyproc', out_prefix=eddy_out_prefix)

eipp.process_heatmaps(img_tags=['FP_NEE', 'FP_NEE_uStar_f', 'FP_LE', 'FP_LE_f', 'FP_H', 'FP_H_f'],
                      tags_skip_legend=['FP_NEE', 'FP_LE', 'FP_H'],
                      map_postfix='_map', legend_postfix='_legend')
eipp.merge_heatmaps([['FP_NEE_map', 'FP_NEE_uStar_f_map', 'FP_NEE_uStar_f_legend'],
                    ['FP_LE_map', 'FP_LE_f_map', 'FP_LE_f_legend'],
                    ['FP_H_map', 'FP_H_f_map', 'FP_H_f_legend']],
                    del_postfix='_map', postfix='_all')
eipp.process_fluxes(img_tags=['Flux_NEE', 'Flux_NEE_uStar_f', 'Flux_LE', 'Flux_LE_f', 'Flux_H', 'Flux_H_f'],
                    postfix='_compact')
eipp.process_diurnal_cycles(img_tags=['DC_NEE_uStar_f', 'DC_LE_f', 'DC_H_f'],
                            postfix='_compact')

arc_path = create_archive(dir='output/reddyproc', arc_fname=f'{eddy_out_prefix}.zip',
                          include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=eipp.paths_exclude_from_arc)

# just for the record: unicode in code is mediocre practice
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

no_scroll()
display_images(OUTPUT_ORDER, main_path='output/reddyproc', prefix=eddy_out_prefix)
add_download_button(arc_path, 'Download all images')
