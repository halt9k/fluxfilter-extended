# formatR::tidy_rstudio()
library(REddyProc)
cat('REddyProc version: ', paste(packageVersion('REddyProc')), '\n')

source('src/reddyproc/web_tool_sources_adapted.r')
source('src/reddyproc/postprocess_calc_averages.r')


EDDY_IMAGES_EXT <- '.png'
STATS_FNAME_EXT <- '.csv'
LOG_FNAME_END <- 'eddy_log.txt'
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


first_and_last <- function(vec){
    ret <- vec
    if (length(vec) > 2)
        ret <- c(vec[1], vec[length(vec)])

    return(ret)
}


right = function (string, char) {
    substr(string,nchar(string)-(char-1),nchar(string))
}


left = function (string,char) {
    substr(string,1,char)
}


add_file_prefix <- function(fpath, prefix){
    dir <- dirname(fpath)
    base <- basename(fpath)
    stopifnot(right(prefix, 1) != '_' && left(base, 1) != '_')
    return(file.path(dir, paste0(prefix, '_', base)))
}


run_web_tool_bridge <- function(eddyproc_user_options){
    eddyproc_config = merge_options(eddyproc_user_options, eddyproc_extra_options)

    got_types <- sapply(eddyproc_config, class)
    need_types <- sapply(eddyproc_all_required_options, class)

    if (any(got_types != need_types)) {
        df_cmp = data.frame(got_types, need_types)
        cmp_str = paste(capture.output(df_cmp), collapse = '\n')
        stop("Incorrect options or options types: ", cmp_str)
    }

    INPUT_FILE <<- eddyproc_user_options$input_file
    OUTPUT_DIR <<- eddyproc_user_options$output_dir

    dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)
    clean_out_files <- function(fname_end)
        unlink(file.path(OUTPUT_DIR, paste0('*', fname_end)))

    clean_out_files(EDDY_IMAGES_EXT)
    clean_out_files(STATS_FNAME_EXT)
    clean_out_files(LOG_FNAME_END)
    clean_out_files(DATA_FNAME_END)

    # necessary and used only in Colab cell
    # options(max.print = 50)

    output_file <- file.path(OUTPUT_DIR, DATA_FNAME_END)
    res <- processEddyData(eddyproc_config, dataFileName = INPUT_FILE,
                           outputFileName = output_file,
                           figureFormat = tools::file_ext(EDDY_IMAGES_EXT))

    df_output <- res[[1]]
    years_str <- res[[2]]

    # workaround, what if real name form?
    # years_num <- first_and_last(df_output$Year - c(1, length(df_output)))
    # years_str <- paste(sprintf("%02d", years_num %% 100), collapse = '-')

    out_prefix <- paste0(eddyproc_config$siteId, '_' , years_str)

    file.rename(output_file, add_file_prefix(output_file, out_prefix))

    # processEddyData guaranteed to output equi-time-distant series
    dfs = calc_averages(df_output)
    save_averages(dfs, OUTPUT_DIR, out_prefix, STATS_FNAME_EXT)

	return(out_prefix)
}


run_web_tool_bridge_logged <- function(eddyproc_user_options){
    result <- NULL

    f <- function(out_result)
        out_result <- run_web_tool_bridge(eddyproc_user_options)

    captured_log <- capture.output(f(result))

    years_str <- result[[2]]
    dir <<- eddyproc_user_options$output_dir
    base <- paste0(years_str, '_', 'eddy_log.txt')
    write(captured_log, file.path(dir, base))

    return(result)
}
