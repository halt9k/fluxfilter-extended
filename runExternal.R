rm(list = ls())


eddyProcConfiguration <- list(
    siteId = 'yourSiteID',
    
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

dir.create(OUTPUT_DIR, showWarnings = FALSE)
unlink(file.path(OUTPUT_DIR, "*.png"))
unlink(file.path(OUTPUT_DIR, "output.txt"))


install_if_missing <- function(package, repos) {
    if (!require(package, character.only = TRUE)) {
        install.packages(package, dependencies = TRUE, repos=repos)
        library(package, character.only = TRUE)
    }
}


# 1.3.2 vs 1.3.3 have different outputs
# to test,
# install.packages('https://cran.r-project.org/bin/windows/contrib/4.1/REddyProc_1.3.2.zip', repos = NULL, type = "binary")

install_if_missing("REddyProc", repos='http://cran.rstudio.com/')
library(REddyProc)
source("src/runEddyProcFunctions.R", chdir = T)

options(max.print = 50)
# fix of stderr output spammed under rpy2.ipython
sink(stdout(), type = "message")

processEddyData(eddyProcConfiguration, dataFileName = INPUT_FILE, figureFormat = "png")
