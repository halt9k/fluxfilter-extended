def test():
    REMOVED_LEGEND_POSTFIX = '_bare'
    REMOVE_LEGENDS = ['FP_NEE']

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


    from src.reddyproc.draw_reddyproc_graphs import draw_reddyproc
    draw_reddyproc(REMOVE_LEGENDS, REMOVED_LEGEND_POSTFIX, OUTPUT_ORDER)
