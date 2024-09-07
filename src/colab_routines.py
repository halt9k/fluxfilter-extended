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


@colab_only
def workaround_stop_scroll():
    from google.colab.output import eval_js
    eval_js('google.colab.output.setIframeHeight("10000")')

    # from IPython.display import HTML, display, Javascript, display_javascript
    # js1 = Javascript('''
    # async function resize_output() {
    #     google.colab.output.setIframeHeight(document.documentElement.scrollHeight, true);
    #     google.colab.output.getActiveOutputArea().scrollTo(2000, 0);
    # }
    # ''')
    # get_ipython().events.register('post_run_cell', resize_output)