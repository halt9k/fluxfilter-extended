# Fluxfilter extended

Support repository for a set of cells which introduced R library wrapper into Google Colab notebook.

Possible points of interest:

- ***src/cells_mirror.py***, ***tools/***, ***test/***, ***src/ipynb_globals.py***:  
  General setup which allows to run specific Jupiter cells almost without modification and without running all the previous cells. Handy when it's necessary to work on notebook which takes long time to run.  
  Essentially, this is solved with `from global_mock import *` or simply global notebook namespace.


- ***src/ipynb_helpers.py***:  
  Some routines for IPython, also safe to be called from pure Python:  
  `display_image_row`:  Also fixes missing scrollbars with `output.no_vertical_scroll()`.   
  `register_ipython_callback_once`:  Cell with attached callback can be runned multiple times.  
  `enable_word_wrap`:  Enable word wrap in cell.


- ***src/colab_routines.py***:  
  Some routines for Google Colab, also safe to be called from pure Python:  
  `colab_only_cell`: Works like `return`, but for cells.  
  `colab_no_scroll`: Expand cell height to fit contents.   
  `colab_add_download_button`: Simple download button, but changes progress bar position from the very bottom to the very top of cell.
