# formatR::tidy_rstudio()
library(REddyProc)
message(sprintf("REddyProc version %s", packageVersion('REddyProc')))

source('src/reddyproc/web_tool_sources_adapted.r')
source('src/reddyproc/postprocess_calc_averages.r')


OUTPUT_PLOTS_MASK <- "*.png"

# REddyProc library may rely on these global vars
INPUT_FILE <- NULL
OUTPUT_DIR <- NULL


message("WARNING: web tool uStarSeasoning factor type not verified")
# corresponds 06.2024 run
eddyproc_all_required_options <- list(
    siteId = 'yourSiteID',

    isToApplyUStarFiltering = TRUE,
    
    # TODO "Continuous" level have only 1 level for factor,
    # but not verified for other opts
    uStarSeasoning = factor("Continuous", levels = c("Continuous")),
    uStarMethod = factor("RTw", levels = "RTw"),

    isBootstrapUStar = FALSE,

    isToApplyGapFilling = TRUE,
    isToApplyPartitioning = TRUE,

    # "Reichstein05", "Lasslop10", ...
    partitioningMethods = c("Reichstein05", "Lasslop10"),
    latitude = 56.5,
    longitude = 32.6,
    timezone = +3,

    # there is also $temperatureVarName ?
    temperatureDataVariable = "Tair",

    isCatchingErrorsEnabled = TRUE,

    input_format = "onlinetool",
    output_format = "onlinetool",

    # figureFormat used from processEddyData
    useDevelopLibraryPath = FALSE,
    debugFlags = ""
)


eddyproc_extra_options <- list(
    isCatchingErrorsEnabled = TRUE,

    input_format = "onlinetool",
    output_format = "onlinetool",

    # figureFormat used from processEddyData
    useDevelopLibraryPath = FALSE,
    debugFlags = ""
)


merge_options <- function(eddyproc_user_options, eddyproc_extra_options){
    eddyproc_config <- list()

    eddyproc_config$siteId <- eddyproc_user_options$site_id

    eddyproc_config$isToApplyUStarFiltering <- eddyproc_user_options$is_to_apply_u_star_filtering
    eddyproc_config$uStarSeasoning <- factor(eddyproc_user_options$u_star_seasoning)
    eddyproc_config$uStarMethod <- factor(eddyproc_user_options$u_star_method)

    eddyproc_config$isBootstrapUStar <- eddyproc_user_options$is_bootstrap_u_star

    eddyproc_config$isToApplyGapFilling <- eddyproc_user_options$is_to_apply_gap_filling
    eddyproc_config$isToApplyPartitioning <- eddyproc_user_options$is_to_apply_partitioning

    eddyproc_config$partitioningMethods <- eddyproc_user_options$partitioning_methods
    eddyproc_config$latitude <- eddyproc_user_options$latitude
    eddyproc_config$longitude <- eddyproc_user_options$longitude
    eddyproc_config$timezone <- eddyproc_user_options$timezone

    eddyproc_config$temperatureDataVariable <- eddyproc_user_options$temperature_data_variable
    
    return(c(eddyproc_config, eddyproc_extra_options))
}


run_web_tool_bridge <- function(eddyproc_user_options){
    eddyproc_config = merge_options(eddyproc_user_options, eddyproc_extra_options)
    
    got_types <- sapply(eddyproc_config, class)
    need_types <- sapply(eddyproc_all_required_options, class)

    if (any(got_types != need_types)){
        print(data.frame(got_types, need_types))
        stop("Incorrect options or options types. Check log for comparison.")
    }

    
    INPUT_FILE <<- eddyproc_user_options$input_file
    OUTPUT_DIR <<- eddyproc_user_options$output_dir

    dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)
    unlink(file.path(OUTPUT_DIR, "*.png"))
    unlink(file.path(OUTPUT_DIR, "*.csv"))
    unlink(file.path(OUTPUT_DIR, "output.txt"))
    
    # necessary and used only in Colab cell
    # options(max.print = 50)    
    

    ext = tools::file_ext(OUTPUT_PLOTS_MASK)
    output_file = file.path(OUTPUT_DIR, "output.txt")
    df_output <- processEddyData(eddyproc_config, dataFileName = INPUT_FILE,
                                 outputFileName = output_file, figureFormat = ext)

    # TODO what if days or months are entierly missing?
    calc_averages(df_output, OUTPUT_DIR, eddyproc_config$siteId)
}
