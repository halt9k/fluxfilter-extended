def test():
    CROP_POSTFIX = '_crop'
    CROP = ['FP_NEE', 'FP_NEE_uStar_f']

    REMOVED_LEGEND_POSTFIX = '_bare'
    REMOVE_LEGENDS = ['FP_NEE', 'FP_NEE_crop']

    OUTPUT_ORDER = (
        "Тепловые карты",
        ['FP_NEE_bare', 'FP_NEE_uStar_f'],
        ['FP_NEE_uStar_f', 'FP_LE', 'FP_H'],
        "Суточный ход",
        ['DC_NEE_uStar_f'],
        ['DC_LE_f'],
        ['DC_H_f'],
        "30-минутные потоки",
        ['Flux_NEE_uStar_f', 'Flux_LE', 'Flux_H']
    )

    from src.reddyproc.draw_reddyproc_graphs import prepare_images, display_images
    prepare_images(CROP, CROP_POSTFIX, REMOVE_LEGENDS, REMOVED_LEGEND_POSTFIX)
    display_images(OUTPUT_ORDER)