# formatR::tidy_rstudio()
library(REddyProc)
cat('REddyProc version: ', paste(packageVersion('REddyProc')), '\n')

source('src/reddyproc/web_tool_sources_adapted.r')
source('src/reddyproc/postprocess_calc_averages.r')


EDDY_IMAGES_EXT <- '.png'
STATS_FNAME_EXT <- '.csv'
DATA_FNAME_END <- 'filled.txt'

# REddyProc library may rely on these global vars
INPUT_FILE <- NULL
OUTPUT_DIR <- NULL


warning("\nWeb tool uStarSeasoning factor type not verified \n\n")
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


merge_options <- function(user_opts, extra_opts){
    merge <- list()

    merge$siteId <- user_opts$site_id

    merge$isToApplyUStarFiltering <- user_opts$is_to_apply_u_star_filtering
    merge$uStarSeasoning <- factor(user_opts$u_star_seasoning)
    merge$uStarMethod <- factor(user_opts$u_star_method)

    merge$isBootstrapUStar <- user_opts$is_bootstrap_u_star

    merge$isToApplyGapFilling <- user_opts$is_to_apply_gap_filling
    merge$isToApplyPartitioning <- user_opts$is_to_apply_partitioning

    merge$partitioningMethods <- user_opts$partitioning_methods
    merge$latitude <- user_opts$latitude
    merge$longitude <- user_opts$longitude
    merge$timezone <- user_opts$timezone

    merge$temperatureDataVariable <- user_opts$temperature_data_variable

    return(c(merge, extra_opts))
}


first_and_last <- function(vec){
    ret <- vec
    if (length(vec) > 2)
        ret <- c(vec[1], vec[length(vec)])

    return(ret)
}


right = function(string, char) {
    substr(string,nchar(string)-(char-1),nchar(string))
}


left = function(string,char) {
    substr(string,1,char)
}


add_file_prefix <- function(fpath, prefix){
    dir <- dirname(fpath)
    base <- basename(fpath)
    stopifnot(right(prefix, 1) != '_' && left(base, 1) != '_')
    return(file.path(dir, paste0(prefix, '_', base)))
}


reddyproc_tool_wrapper <- function(eddyproc_config){
    # more specifically, still calls processEddyData wrapper from web tool,
    # which finally calls REddyProc library
    # returns: [df_output, years_str, out_prefix]

    dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

    clean_out_files <- function(fname_end)
        unlink(file.path(OUTPUT_DIR, paste0('*', fname_end)))
    clean_out_files(EDDY_IMAGES_EXT)
    clean_out_files(STATS_FNAME_EXT)
    clean_out_files(DATA_FNAME_END)

    output_file <- file.path(OUTPUT_DIR, DATA_FNAME_END)
    res <- processEddyData(eddyproc_config, dataFileName = INPUT_FILE,
                           outputFileName = output_file,
                           figureFormat = tools::file_ext(EDDY_IMAGES_EXT))

    # res: [df_output, years_str]
    out_prefix <<- paste0(eddyproc_config$siteId, '_' , res[[2]])
    file.rename(output_file, add_file_prefix(output_file, out_prefix))

	return(append(res, out_prefix))
}


reddyproc_and_postprocess <- function(user_options){
    # combined function to avoid converting output or using global env

    # helps under iptyb or Colab cell
    options(max.print = 80)
    sink(stdout(), type = "message")
    message("Info: output of R is redirected to stdout and truncated.")

    INPUT_FILE <<- user_options$input_file
    OUTPUT_DIR <<- user_options$output_dir
    eddyproc_config <- merge_options(user_options, eddyproc_extra_options)

    got_types <- sapply(eddyproc_config, class)
    need_types <- sapply(eddyproc_all_required_options, class)

    if (any(got_types != need_types)) {
        df_cmp = data.frame(got_types, need_types)
        cmp_str = paste(capture.output(df_cmp), collapse = '\n')
        stop("Incorrect options or options types: ", cmp_str)
    }


    res <- reddyproc_tool_wrapper(eddyproc_config)
    # res: [df_output, years_str, out_prefix]
    out_prefix <- res[[3]]

    # processEddyData guaranteed to output equi-time-distant series
    dfs = calc_averages(res[[1]])
    save_averages(dfs, OUTPUT_DIR, out_prefix, STATS_FNAME_EXT)

    return(out_prefix)
}
