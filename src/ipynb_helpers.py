"""
Unlike colab_routines.py, this file is expected to be used under local runs too.
However, output may be auto replaced with text.
"""
import io
from warnings import warn

from IPython import get_ipython
from IPython.display import HTML, display, display_png
from IPython.display import Image as IImage
from PIL import Image
from ipywidgets import widgets, HBox

from src.helpers.image_tools import grid_images


def display_image_row(paths):
    imgs = [Image.open(path) for path in paths]
    img_combined = grid_images(imgs, 3)

    byte_arr = io.BytesIO()
    img_combined.save(byte_arr, format='PNG')

    img = IImage(data=byte_arr.getvalue(), width=img_combined.width, height=img_combined.height, unconfined=True)
    display(img)


def ipython_only(func):
    def wrapper(*args, **kwargs):
        if get_ipython():
            return func(*args, **kwargs)
        else:
            print(f"IPython env not detected. {func.__name__} is skipped by design.")
            return None

    return wrapper


def css_enable_word_wrap(*args, **kwargs):
    display(HTML('''
    <style>
        pre {
            white-space: pre-wrap;
        }
    </style>
    '''))


def register_ipython_callback_once(event_name, cb):
    ev = get_ipython().events
    cb_unregs = [cb_old for cb_old in ev.callbacks[event_name] if cb_old.__name__ == cb.__name__]
    if len(cb_unregs) == 1 and cb.__code__ == cb_unregs[0].__code__:
        return

    for cb_old in cb_unregs:
        warn(f'Removing unexpected callback {cb_old}.')
        ev.unregister(event_name, cb_old)

    ev.register(event_name, cb)


@ipython_only
def enable_word_wrap():
    register_ipython_callback_once('pre_run_cell', css_enable_word_wrap)
    print("Word wrap in output is enabled.")