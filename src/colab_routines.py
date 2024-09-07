# all functions here are to be mocked or cancelled during non-colab runs
from enum import Enum, auto
from decorator import decorator


class RunMode(Enum):
    LOCAL, COLAB = auto(), auto()

try:
    import google.colab
except ImportError:
    RUN_MODE = RunMode.LOCAL
else:
    RUN_MODE = RunMode.COLAB


def colab_only(func):
    def wrapper(*args, **kwargs):
        if RUN_MODE == RunMode.COLAB:
            return func(*args, **kwargs)
        else:
            print(f"Skipping {func.__name__}, not in Colab mode.")
            return None
    return wrapper


class StopExecution(Exception):
    def _render_traceback_(self):
        return ['Colab env not detected. Current cell is only for Colab.']


def colab_only_cell():
    # reminder: cannot be used before this file is downloaded
    try:
        import google.colab
    except ImportError:
        raise StopExecution()


@colab_only
def no_scroll():
    from google.colab import output
    output.no_vertical_scroll()


@colab_only
def add_download(fname, caption):
    def clicked(arg):
        from google.colab import files
        files.download(fname)

    from IPython.display import display
    import ipywidgets as widgets

    button_download = widgets.Button(description=caption)
    button_download.on_click(clicked)
    display(button_download)


""" examples:
from google.colab.output import eval_js
eval_js('''
let sh = google.colab.output.getActiveOutputArea().scrollHeight;
google.colab.output.setIframeHeight(sh);
''')

from IPython.display import HTML, display, Javascript, display_javascript
js1 = Javascript('''
async function resize_output() {
    google.colab.output.setIframeHeight(document.documentElement.scrollHeight, true);
    google.colab.output.getActiveOutputArea().scrollTo(2000, 0);
}
''')
get_ipython().events.register('post_run_cell', resize_output)
"""
