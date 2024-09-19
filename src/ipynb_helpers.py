"""
Unlike colab_routines.py, this file is expected to be used under local runs too.
However, output may be auto replaced with text.
"""
import io
from pathlib import Path

from IPython.display import Markdown, display
from PIL import Image
from ipywidgets import widgets, HBox


def display_image_row(paths):
    img_widgets = []
    for path in paths:
        byte_arr = io.BytesIO()
        Image.open(path).save(byte_arr, format='PNG')
        img_widgets += [widgets.Image(value=byte_arr.getvalue(), format="PNG")]

    hbox = HBox(img_widgets)
    display(hbox)
