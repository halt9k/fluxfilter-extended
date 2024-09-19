"""
Unlike colab_routines.py, this file is expected to be used under local runs too.
However, output may be auto replaced with text.
"""
import io
from pathlib import Path

from IPython import get_ipython
from IPython.display import Markdown, HTML, display
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


def ipython_only(func):
    def wrapper(*args, **kwargs):
        if get_ipython():
            return func(*args, **kwargs)
        else:
            print(f"IPython env not detected. {func.__name__} is skipped by design.")
            return None

    return wrapper


@ipython_only
def word_wrap():
    def set_css(*args, **kwargs):
        display(HTML('''
        <style>
            pre {
                white-space: pre-wrap;
            }
        </style>
        '''))

    get_ipython().events.register('pre_run_cell', set_css)
