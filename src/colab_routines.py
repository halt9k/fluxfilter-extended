# all functions here are to be mocked or cancelled during non-colab runs

def stop_scroll_workaround():
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