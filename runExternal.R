rm(list = ls())

# formatR::tidy_rstudio()
INPUT_FILE = "REddyProc.txt"


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


install_if_missing <- function(package, repos) {
    if (!require(package, character.only = TRUE)) {
        install.packages(package, dependencies = TRUE, repos=repos)
        library(package, character.only = TRUE)
    }
}

install_if_missing("REddyProc", repos='http://cran.rstudio.com/')

options(max.print = 50)

library(REddyProc)
source("src/runEddyProcFunctions.R", chdir = T)
dir.create("output", showWarnings = FALSE)

# 1.3.2 vs 1.3.3 have different outputs
# to test,
# install.packages('https://cran.r-project.org/bin/windows/contrib/4.1/REddyProc_1.3.2.zip', repos = NULL, type = "binary")


# very complicated fix of cat function
original_cat <- function(..., file = "", sep = " ", fill = FALSE, labels = NULL, 
                          append = FALSE) 
{
    if (is.character(file)) 
        if (file == "") 
            file <- stdout()
    else if (startsWith(file, "|")) {
        file <- pipe(substring(file, 2L), "w")
        on.exit(close(file))
    }
    else {
        file <- file(file, ifelse(append, "a", "w"))
        on.exit(close(file))
    }
    .Internal(cat(list(...), file, sep, fill, labels, append))
}


cat_ex <- function(...){
    args <- list(...)
    if (!is.null(args[["file"]]))
        args[["file"]] <- NULL
    do.call(original_cat, args)
}


sink(stdout(), type = "message")
print("using print")
cat("using cat\n")
message("using message")
warning("using warning")
sink(NULL, type="message")
warning("after ending sink")
q("no")


processEddyData(eddyProcConfiguration, dataFileName=INPUT_FILE)

