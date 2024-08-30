library(REddyProc)

source("src/reddyproc/eddyproc_web_tool_copy.r", chdir = T)
source("src/reddyproc/calc_averages.r", chdir = T)


eddyproc_config_default <- list(
    # siteId = 'yourSiteID',
    siteId = ias_output_prefix,

    isToApplyUStarFiltering = TRUE,
    # uStarSeasoning = "WithinYear", "Continuous" , ...

    # could be more levels somewhere around
    uStarSeasoning =  factor("Continuous", levels = "Continuous"),
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


# formatR::tidy_rstudio()
# REddyProc requires global vars
INPUT_FILE = "REddyProc.txt"
OUTPUT_DIR = "./output/REddyProc"
OUTPUT_PLOTS_MASK = "*.png"

dir.create(OUTPUT_DIR, showWarnings = FALSE)
unlink(file.path(OUTPUT_DIR, "*.png"))
unlink(file.path(OUTPUT_DIR, "*.csv"))
unlink(file.path(OUTPUT_DIR, "output.txt"))


# options(max.print = 50)

ext = tools::file_ext(OUTPUT_PLOTS_MASK)
df_output <- processEddyData(eddyproc_config_default, dataFileName = INPUT_FILE, figureFormat = ext)
calc_averages(df_output, OUTPUT_DIR, eddyproc_config_default$siteId)