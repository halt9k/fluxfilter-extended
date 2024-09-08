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

debugSource('src/reddyproc/postprocess_calc_averages.r')


test_model_3_month <- function(){
	df = read.csv('test/reddyproc/test_averaging/3_months_long.txt', quote = NULL,  row.names = NULL)
	df$Reco = NA

	# ensure order and years are processed separately
	df[df$Year == 2022 & df$DoY == 354 & df$Hour > 10,]$Year = 2023
	df[df$Year == 2022 & df$DoY == 354,]$LE_f = 17
	df[df$Year == 2023 & df$DoY == 354,]$LE_f = 11

	# TODO missing columns ?

	# ensure average
	row_mask = df$Year == 2022 & between(df$DoY, 325, 365)
	df[row_mask,]$VPD_f = df[row_mask,]$DoY

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

	# ensure order
	stopifnot(dm$Year[1] == 2022 & dm$Year[length(dm$Year)] == 2023)

	#  ensure average
	stopifnot(between(dm[dm$Year == 2022 & dm$Month == 12,]$VPD_f, 31*11, 31*12))

	# no dupe cols or cols with .1 in name
	names_dd = names(dd)
	names_dm = names(dm)
	names_dy = names(dy)
	stopifnot(!any(c(duplicated(names_dd), duplicated(names_dm), duplicated(names_dy))))
	stopifnot(!any(contains(match = '.1', vars = c(names_dd, names_dm, names_dy))))

	cat('Test test_model_3_month ok \n')
}


test_real_year <- function(){
	df = read.csv('test/reddyproc/test_averaging/real_data_test_05.09.24.txt', quote = NULL,  row.names = NULL)

	# ensure order and years are processed separately
	df[df$Year == 2023 & df$DoY == 354 & df$Hour > 10,]$Year = 2022
	df[df$Year == 2023 & df$DoY == 354,]$LE_f = 17
	df[df$Year == 2022 & df$DoY == 354,]$LE_f = 11

	# TODO missing columns ?

	# ensure average
	row_mask = df$Year == 2023 & between(df$DoY, 325, 365)
	df[row_mask,]$VPD_f = df[row_mask,]$DoY

	# ensure NA calculated correctly
	df[df$Year == 2023 & between(df$DoY, 1, 31),]$H_f = NA

	dfs <- calc_averages(df)
	dd <- df_daily <- dfs[[1]]
	dm <- df_monthly <- dfs[[2]]
	dy <- df_yearly <- dfs[[3]]

	# ensure years are processed separately
	stopifnot(dd[dd$Year == 2023 & dd$DoY == 354,]$LE_f == 17)
	stopifnot(dd[dd$Year == 2022 & dd$DoY == 354,]$LE_f == 11)

	# ensure NA calculated correctly
	stopifnot(is.na.data.frame(dm[dm$Year == 2023 & dm$Month == 1,]$H_f))
	stopifnot(dm[dm$Year == 2022 & dm$Month == 1,]$H_sqc == 0.0)
	stopifnot(dm[dm$Year == 2023 & dm$Month == 12,]$H_sqc == 1.0)

	# ensure order
	stopifnot(dm$Year[1] == 2023 & dm$Year[length(dm$Year)] == 2022)

	#  ensure average
	stopifnot(between(dm[dm$Year == 2022 & dm$Month == 12,]$VPD_f, 31*11, 31*12))

	# no dupe cols or cols with .1 in name
	names_dd = names(dd)
	names_dm = names(dm)
	names_dy = names(dy)
	stopifnot(!any(c(duplicated(names_dd), duplicated(names_dm), duplicated(names_dy))))
	stopifnot(!any(contains(match = '.1', vars = c(names_dd, names_dm, names_dy))))

	cat('Test test_real_year ok \n')
}


test_real_year()
test_model_3_month()
