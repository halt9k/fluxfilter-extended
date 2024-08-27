import io

from IPython.core.display import Markdown
from IPython.display import display
from PIL import Image
from ipywidgets import HBox, widgets

from src.image_tools import split_image
import glob
import src.os_helpers  # noqa: F401

all_img_paths = glob.glob('output/REddyProc/*.png')


def get_unique_path(fname_end):
    fname_end = fname_end + '.'
    img = [path for path in all_img_paths if fname_end in path]
    found_matches = len(img)
    assert found_matches == 1, f"Expected 1 file: {fname_end} found {found_matches}"
    return img[0]


TRUNC_LEGEND_TAGS = ['FP_NEE']
for tag in TRUNC_LEGEND_TAGS: 
    # FP_NEE -> FP_NEE_no_legend
    path = get_unique_path(tag)
    # split_image(path)

# just for the record: unicode in code is not great 
# TODO HEAT_MAPS 'FP_NEE_uStar_f' or 'FP_NEE' ? 
# if OUTPUT_ORDER is None:
OUTPUT_ORDER = [
    "Тепловые карты",
    ['FP_NEE', 'FP_NEE_uStar_f', 'FP_LE', 'FP_H'],
    "Суточный ход",
    ['DC_NEE_uStar_f'],
    ['DC_LE_f'],
    ['DC_H_f'],
    "30-минутные потоки",
    ['Flux_NEE_uStar_f', 'Flux_LE', 'Flux_H']
]


# 'DSum_Rg_f', 'DSum_rH_f', 'DSum_Tair_f', 'DSum_VPD_f', 'DSumU_H_f', 'DSumU_LE_f', 'DSumU_NEE_uStar_f',
# 'FP_GPP_DT_uStar', 'FP_GPP_uStar_f', 'FP_H', 'FP_H_f', 'FP_LE', 'FP_LE_f', 'FP_NEE', 'FP_NEE_uStar_f', 'FP_Reco_DT_uStar', 'FP_Reco_uStar',
# 'FP_Rg', 'FP_Rg_f', 'FP_rH', 'FP_rH_f', 'FP_Tair', 'FP_Tair_f', 'FP_VPD', 'FP_VPD_f']

def display_image_row(paths):
    img_widgets = []
    for path in paths:
        byte_arr = io.BytesIO()
        Image.open(path).save(byte_arr, format='PNG')
        img_widgets += [widgets.Image(value=byte_arr.getvalue(), format="PNG")]

    hbox = HBox(img_widgets)
    display(hbox)


# TODO extract entierly into non-Jupyter tests?
# def draw_reddyproc():
for output_step in OUTPUT_ORDER:
    if type(output_step) is str:
        title_text = output_step
        display(Markdown("## " + title_text))
    elif type(output_step) is list:
        paths = [get_unique_path(tag) for tag in output_step]
        display_image_row(paths)
    else:
        raise Exception("Wrong OUTPUT_HEADERS contents")
