import io
from pathlib import Path

from IPython.display import Markdown, display
from PIL import Image
from ipywidgets import widgets, HBox

from src.helpers.io_helpers import tags_to_files


def display_images(output_order, main_path, prefix):
    main_path = Path(main_path)

    for output_step in output_order:
        if type(output_step) is str:
            title_text = output_step
            display(Markdown(title_text))
        elif type(output_step) is list:
            paths = tags_to_files(main_path, prefix, output_step, '.png')
            display_image_row(list(paths.values()))
        else:
            raise Exception("Wrong OUTPUT_HEADERS contents")


def display_image_row(paths):
    img_widgets = []
    for path in paths:
        byte_arr = io.BytesIO()
        Image.open(path).save(byte_arr, format='PNG')
        img_widgets += [widgets.Image(value=byte_arr.getvalue(), format="PNG")]

    hbox = HBox(img_widgets)
    display(hbox)
