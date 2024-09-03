# just some tests

rm(list = ls())
rm(list = ls(environment(), all.names = TRUE))
gc()

# clear RStudio output
cat("\014")

# interactive() ?
options(error = browser)
options(max.print = 100)


cur_dir <- dirname(rstudioapi::getSourceEditorContext()$path)
project_dir <- dirname(dirname(cur_dir))
setwd(project_dir)
cat("Working dir is set to: ", project_dir, '\n')

test_averages <- function(){
	debugSource('src/reddyproc/postprocess_calc_averages.r')

	df = read.csv('test/reddyproc/test_averaging/3_months_long.txt', quote = NULL,  row.names = NULL)
	df$Reco = NA

	# ensure years are processed separately
	df[df$Year == 2022 & df$DoY == 354 & df$Hour > 10,]$Year = 2023
	df[df$Year == 2022 & df$DoY == 354,]$LE_f = 17
	df[df$Year == 2023 & df$DoY == 354,]$LE_f = 11

	dfs <- calc_averages(df)
	df_daily = dfs[[1]]
	df_monthly = dfs[[2]]
	df_yearly = dfs[[3]]

	# ensure years are processed separately
	stopifnot(df_daily[df_daily$DoY == 354,]$LE_f == 17)
	stopifnot(df_daily[df_daily$DoY == 354,]$LE_f == 11)

	cat('Test ok \n')
}

test_averages()
