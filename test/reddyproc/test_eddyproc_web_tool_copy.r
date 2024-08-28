rm(list = ls())
ias_output_prefix = 'tv_fy4'


eddyproc_config <- list(
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
# REddyProc global vars
INPUT_FILE = "REddyProc.txt"
OUTPUT_DIR = "./output/REddyProc"
OUTPUT_PLOTS_MASK = "*.png"

dir.create(OUTPUT_DIR, showWarnings = FALSE)
unlink(file.path(OUTPUT_DIR, "*.png"))
unlink(file.path(OUTPUT_DIR, "output.txt"))


# 1.3.2 vs 1.3.3 have different outputs
# to test,
# install.packages('https://cran.r-project.org/bin/windows/contrib/4.1/REddyProc_1.3.2.zip', repos = NULL, type = "binary")
install_if_missing <- function(package, repos) {
    if (!require(package, character.only = TRUE)) {
        install.packages(package, dependencies = TRUE, repos=repos)
        library(package, character.only = TRUE)
    }
}
install_if_missing("REddyProc", repos='http://cran.rstudio.com/')


library(REddyProc)
source("src/reddyproc/eddyproc_web_tool_copy.r", chdir = T)


options(max.print = 50)
# fix of stderr output spammed under rpy2.ipython
sink(stdout(), type = "message")

ext = tools::file_ext(OUTPUT_PLOTS_MASK)
df_output <- processEddyData(eddyproc_config, dataFileName = INPUT_FILE, figureFormat = ext)

source("src/reddyproc/calc_averages.r", chdir = T)
calc_averages(df_output, eddyproc_config$siteId)
