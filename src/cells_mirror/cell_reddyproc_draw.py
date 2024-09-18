from src.ipynb_globals import *
from src.reddyproc.postprocess import create_archive
from src.reddyproc.postprocess_graphs import EddyOutput, EddyImgTagHandler
from src.colab_routines import add_download_button, no_scroll
from src.ipynb_helpers import display_images

output_sequence = EddyOutput.default_sequence(is_ustar=eddyproc_options.is_to_apply_u_star_filtering)
# possible to modify or replace output_sequence for output customization
# output_sequence[3] = []

tag_handler = EddyImgTagHandler(main_path='output/reddyproc',
                                eddy_loc_prefix=eddy_out_prefix, img_ext='.png')
eio = EddyOutput(output_sequence=output_sequence,
                 tag_handler=tag_handler)
eio.prepare_images()

arc_path = create_archive(dir='output/reddyproc', arc_fname=eddy_out_prefix + '.zip',
                          include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=eio.img_proc.raw_img_duplicates)
add_download_button(arc_path, 'Download all images')

no_scroll()
# TODO move to class?
display_images(output_sequence, main_path='output/reddyproc', prefix=eddy_out_prefix)

tag_handler.display_tag_info(eio.extended_tags())
