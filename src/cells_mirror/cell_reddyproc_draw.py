# Full list of outputs (not all are included in OUTPUT_ORDER):
# 'DC_H_f', 'DC_LE_f', 'DC_NEE_uStar_f', 'DC_Rg_f', 'DC_rH_f', 'DC_Tair_f', 'DC_VPD_f',
# 'DSum_Rg_f', 'DSum_rH_f', 'DSum_Tair_f', 'DSum_VPD_f', 'DSumU_H_f', 'DSumU_LE_f', 'DSumU_NEE_uStar_f',
# 'Flux_H', 'Flux_H_f', 'Flux_LE', 'Flux_LE_f', 'Flux_NEE', 'Flux_NEE_uStar_f', 'Flux_Rg', 
# 'Flux_Rg_f', 'Flux_rH', 'Flux_rH_f', 'Flux_Tair','Flux_Tair_f', 'Flux_VPD','Flux_VPD_f',
# 'FP_GPP_DT_uStar', 'FP_GPP_uStar_f', 'FP_H', 'FP_H_f', 'FP_LE', 'FP_LE_f', 'FP_NEE', 
# 'FP_NEE_uStar_f', 'FP_Reco_DT_uStar', 'FP_Reco_uStar',
# 'FP_Rg', 'FP_Rg_f', 'FP_rH', 'FP_rH_f', 'FP_Tair', 'FP_Tair_f', 'FP_VPD', 'FP_VPD_f'

CROP_POSTFIX = '_crop'
CROP = ['FP_NEE', 'FP_NEE_uStar_f',
        'FP_LE', 'FP_LE_f',
        'FP_H', 'FP_H_f',]

REMOVED_LEGEND_POSTFIX = '_bare'
REMOVE_LEGENDS = ['FP_NEE_crop',
                  'FP_LE_crop',
                  'FP_H_crop']


# just for the record: unicode in code is mediocre practice
OUTPUT_ORDER = (
    "Тепловые карты", 
    ['FP_NEE_crop_bare', 'FP_NEE_uStar_f_crop'],
    ['FP_LE_crop_bare', 'FP_LE_f_crop'],
    ['FP_H_crop_bare', 'FP_H_f_crop'],
    "Суточный ход", 
    ['DC_NEE_uStar_f'], 
    ['DC_LE_f'], 
    ['DC_H_f'],
    "30-минутные потоки", 
    ['Flux_NEE', 'Flux_NEE_uStar_f'],
    ['Flux_LE', 'Flux_LE_f'],
    ['Flux_H', 'Flux_H_f']
)

from src.reddyproc.postprocess_draw_graphs import prepare_images, display_images
prepare_images(CROP, CROP_POSTFIX,  REMOVE_LEGENDS, REMOVED_LEGEND_POSTFIX)
display_images(OUTPUT_ORDER)
