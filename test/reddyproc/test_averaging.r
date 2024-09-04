# just some tests

rm(list = ls())
rm(list = ls(environment(), all.names = TRUE))
gc()

# clear RStudio output
cat("\014")


options(error = browser)
options(max.print = 100)
# interactive() ?
# on_debug = function() {	cat("\014")	browser()}
# options(debugger = on_debug)


cur_dir <- dirname(rstudioapi::getSourceEditorContext()$path)
project_dir <- dirname(dirname(cur_dir))
setwd(project_dir)
cat("Working dir is set to: ", project_dir, '\n')

test_averaging <- function(){
	debugSource('src/reddyproc/postprocess_calc_averages.r')

	df = read.csv('test/reddyproc/test_averaging/3_months_long.txt', quote = NULL,  row.names = NULL)
	df$Reco = NA

	# ensure years are processed separately
	df[df$Year == 2022 & df$DoY == 354 & df$Hour > 10,]$Year = 2023
	df[df$Year == 2022 & df$DoY == 354,]$LE_f = 17
	df[df$Year == 2023 & df$DoY == 354,]$LE_f = 11

	# ensure NA calculated correctly
	df[df$Year == 2023 & between(df$DoY, 1, 31),]$H_f = NA

	dfs <- calc_averages(df)
	dd <- df_daily <- dfs[[1]]
	dm <- df_monthly <- dfs[[2]]
	dy <- df_yearly <- dfs[[3]]

	# ensure years are processed separately
	stopifnot(dd[dd$Year == 2022 & dd$DoY == 354,]$LE_f == 17)
	stopifnot(dd[dd$Year == 2023 & dd$DoY == 354,]$LE_f == 11)

	# ensure NA calculated correctly
	stopifnot(is.na.data.frame(dm[dm$Year == 2023 & dm$Month == 1,]$H_f))
	stopifnot(dm[dm$Year == 2023 & dm$Month == 1,]$H_sqc == 0.0)
	stopifnot(dm[dm$Year == 2022 & dm$Month == 12,]$H_sqc == 1.0)

	cat('Test ok \n')
}

test_averaging()
