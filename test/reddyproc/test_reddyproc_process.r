# this file allows running cell_reddyproc_process directly without rpy2
# which enables RStudio interactive debug

rm(list = ls())
rm(list = ls(), envir = .GlobalEnv)
gc()

# clear RStudio output
cat("\014")

# break into debug on error
options(error = browser)

cur_dir <- dirname(rstudioapi::getSourceEditorContext()$path)
project_dir <- dirname(dirname(cur_dir))
setwd(project_dir)
cat("Working dir is set to: ", project_dir)



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
    
    input_file = "REddyProc.txt",
    output_dir = "./output/REddyProc"
)

options(max.print = 50)


debugSource('src/reddyproc/postprocess_calc_averages.r')
debugSource('src/reddyproc/web_tool_sources_adapted.r')
debugSource('src/reddyproc/web_tool_bridge.r')
run_web_tool_bridge(eddyproc_user_options)
