# tests specifically for calc_averages

setwd(dirname(dirname(dirname(rstudioapi::getSourceEditorContext()$path))))
debugSource('test/reddyproc/helpers/init_test_env.r')
debugSource('src/reddyproc/postprocess_calc_averages.r')


ensure_correct_names <- function(nd, nm, ny){
	stopifnot(!duplicated(nd), !duplicated(nm), !duplicated(ny))
	stopifnot(setdiff(nd, 'DoY') == nm, setdiff(nm, 'Month') == ny)

	# no with .1 in name
	stopifnot(!any(contains(match = '.1', vars = c(nd, nm, ny))))
}


save_reddyproc_df <- function(df, fname) {
	df_save <- df
	df_save$DateTime <- as.character(format(df$DateTime, "%Y-%m-%d %H:%M:%S"))
	write.csv(df_save, file = 'test.txt', row.names = FALSE, quote = FALSE)
}


load_csv_as_reddyproc_df <- function(fname, tz = 'UTC') {
	df <- read.csv(fname, quote = NULL,  row.names = NULL)
	if (!is.null(df$season))
		df$season <- factor(df$season)
	df$DateTime <- as.POSIXct(df$DateTime, tz = tz, format = "%Y-%m-%d %H:%M:%S")

	# all.equal(test, df_full, tolerance = 1e-8)
	# all.equal(test, df_full, tolerance = 1e-8, check.attributes = FALSE)
	return(df)
}


test_model_3_month <- function(){
	df = load_csv_as_reddyproc_df('test/reddyproc/test_averaging_fixtures/3_months_long.txt', tz = 'GMT')

	# ensure order and years are processed separately
	df[df$Year == 2022 & df$DoY == 354 & df$Hour > 10,]$Year = 2023
	df[df$Year == 2022 & df$DoY == 354,]$LE_f = 17
	df[df$Year == 2023 & df$DoY == 354,]$LE_f = 11

	# ensure missing columns won't break
	df$NEE_f = NULL

	# ensure average
	stopifnot(df[df$Year == 2023 & between(df$DoY, 32, 59),]$Rg_f %>%
			  	mean %>% between(46.6980, 46.6981))

	# ensure NA calculated correctly
	df[df$Year == 2023 & between(df$DoY, 1, 31),]$H = NA

	dfs <- calc_averages(df)
	df <- NULL
	dd <- dfs$daily
	dm <- dfs$monthly
	dy <- dfs$yearly

	# ensure years are processed separately
	stopifnot(dd[dd$Year == 2022 & dd$DoY == 354,]$LE_f == 17)
	stopifnot(dd[dd$Year == 2023 & dd$DoY == 354,]$LE_f == 11)

	# ensure order
	stopifnot(dm$Year[1] == 2022 & dm$Year[nrow(dm)] == 2023)

	# ensure missing columns won't break
	stopifnot(!'NEE_f' %in% colnames(dm), !'NEE' %in% colnames(dd))

	#  ensure average
	stopifnot(dm[dm$Year == 2023 & dm$Month == 2,]$Rg_f %>%
			  	between(46.6980, 46.6981))

	# ensure NA calculated correctly
	stopifnot(dm[dm$Year == 2023 & dm$Month == 1,]$H_sqc == 0.0)

	ensure_correct_names(names(dd), names(dm), names(dy))
	cat('Test test_model_3_month ok \n\n')
}


test_real_year <- function(){
	df = load_csv_as_reddyproc_df('test/reddyproc/test_averaging_fixtures/verify_model_2.txt')

	# ensure order and years are processed separately
	df[df$Year == 2023 & df$DoY == 354 & df$Hour > 10,]$Year = 2022
	df[df$Year == 2023 & df$DoY == 354,]$LE_f = 17
	df[df$Year == 2022 & df$DoY == 354,]$LE_f = 11

	# ensure average
	row_mask = df$Year == 2023 & between(df$DoY, 325, 365)
	df[row_mask,]$VPD_f = df[row_mask,]$DoY

	# ensure no interference from similar columns
	df$VPD_ff = df$DoY
	df$VVPD_ff = df$DoY

	# ensure NA calculated correctly
	nna_prc <- df[df$Year == 2022 & df$DoY == 354,]$LE %>% {mean(!is.na(.))}
	df[df$Year == 2023 & between(df$DoY, 1, 31),]$H_f <- NA
	stopifnot(df[df$Year == 2022 & between(df$DoY, 1, 31),]$H %>% is.na)
	df[df$Year == 2023 & between(df$DoY, 335, 365),]$H <- -5

	# ensure single row val
	df[df$Year == 2024,]$VPD = NA
	df[df$Year == 2024,]$VPD_f = NA

	dfs <- calc_averages(df)
	df <- NULL
	dd <- dfs$daily
	dm <- dfs$monthly
	dy <- dfs$yearly

	# ensure years are processed separately
	stopifnot(dd[dd$Year == 2023 & dd$DoY == 354,]$LE_f == 17)
	stopifnot(dd[dd$Year == 2022 & dd$DoY == 354,]$LE_f == 11)

	# ensure NA calculated correctly
	stopifnot(dm[dm$Year == 2022 & dm$Month == 12,]$LE_sqc %>%
			  	between(nna_prc - 0.1, nna_prc + 0.1))
	stopifnot(dm[dm$Year == 2023 & dm$Month == 1,]$H_f %>% is.na)
	stopifnot(dm[dm$Year == 2022 & dm$Month == 1,]$H_sqc == 0.0)
	stopifnot(dm[dm$Year == 2023 & dm$Month == 12,]$H_sqc == 1.0)

	# ensure order
	stopifnot(dm$Year[1] == 2022 & dm$Year[nrow(dm)] == 2023)

	#  ensure average
	stopifnot(dm[dm$Year == 2023 & dm$Month == 12,]$VPD_f %>% between(31*11, 31*12))

	# ensure one val
	stopifnot(dd[dd$Year == 2024,]$VPD_sqc == 0)
	stopifnot(dy[dy$Year == 2024,]$VPD_f %>% is.na)

	ensure_correct_names(names(dd), names(dm), names(dy))
	save_averages(dfs, tempdir(), 'tmp', '.csv')
	cat('Test test_real_year ok \n\n')
}


test_real_year()
test_model_3_month()
