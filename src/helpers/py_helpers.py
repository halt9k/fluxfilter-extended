import contextlib


@contextlib.contextmanager
def catch(on_exception=None, err_types=Exception):
    try:
        yield
    except err_types as e:
        if on_exception:
            on_exception(e)
