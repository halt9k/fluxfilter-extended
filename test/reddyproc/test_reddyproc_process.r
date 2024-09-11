# this file allows running cell_reddyproc_process directly without rpy2
# which enables RStudio interactive debug

setwd(dirname(dirname(dirname(rstudioapi::getSourceEditorContext()$path))))
debugSource('test/reddyproc/helpers/init_test_env.r')
debugSource('src/reddyproc/postprocess_calc_averages.r')
debugSource('src/reddyproc/web_tool_sources_adapted.r')
debugSource('src/reddyproc/reddyproc_wrapper.r')


# possibly copy all used files into temp dir and work only from it
test_dir = tempdir()


# duplicates cell code to run from pure R
# avoiding R dupe here can be too complicated
eddyproc_user_options <- list(
    site_id = 'TestSiteID',

    is_to_apply_u_star_filtering = TRUE,

    u_star_seasoning =  factor("Continuous", levels = c("Continuous", "WithinYear")),
    u_star_method = factor("RTw", levels = "RTw"),

    is_bootstrap_u_star = FALSE,

    is_to_apply_gap_filling = TRUE,
    is_to_apply_partitioning = TRUE,

    partitioning_methods = c("Reichstein05", "Lasslop10"),
    latitude = 56.5,
    longitude = 32.6,
    timezone = +3,

    temperature_data_variable = "Tair",

    input_file = "test/reddyproc/test_reddyproc_process_fixtures/3mon_swap_years.txt",
    # input_file = "REddyProc.txt",
    # output_dir = test_dir
    output_dir = "output/reddyproc"
)


reddyproc_and_postprocess(eddyproc_user_options)
