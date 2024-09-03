library(dplyr)
library(lubridate)
library(tibble)


percent_non_na <- function(vals){
    if (length(vals) > 0)
        1.0 - sum(is.na(vals)) / length(vals)
    else
        0.0
}


aggregate_all_by <- function(df, col_name, FUN, ...){
    res <- aggregate(x = df, by = list(df[[col_name]]), FUN, ...)
    res[[col_name]] <- res$'Group.1'
    res$'Group.1' <- NULL
    return(res)
}


combine_alternating <- function(df_a, df_b, col_expected_dupe){
    neworder <- order(c(2*(seq_along(df_a) - 1) + 1,
                        2*seq_along(df_b)))

    stopifnot(df_a$col_expected_dupe == df_b$col_expected_dupe)
    neworder = neworder[-1]

    cbind(df_a, df_b)[,neworder]
}


calc_averages <- function(df_full){
    # write.csv(df_full, file = '_test.txt', row.names = FALSE, quote=FALSE)

    df_to_average <- df_full %>%  select(ends_with("_f") | "Reco")
    df_full$Month <- month(df_full$DateTime)

    cat('Columns picked for averaging: \n', names(df_to_average), '\n')

    # merge into one func or keep readable?
    df_daily <- cbind(DoY = df_full$DoY, df_to_average)
    df_monthly <- cbind(Month = df_full$Month, df_to_average)
    df_yearly <- cbind(Year = df_full$Year, df_to_average)

    df_daily_means <- aggregate_all_by(df_daily, 'DoY', mean, na.rm = TRUE)
    df_monthly_means <- aggregate_all_by(df_monthly, 'Month', mean, na.rm = TRUE)
    df_yearly_means <- aggregate_all_by(df_yearly, 'Year', mean, na.rm = TRUE)

    unfilled_columns <- gsub("_f", "", colnames(df_to_average))
    unfilled_columns <- setdiff(unfilled_columns, c("GPP", "Reco"))
    df_for_gaps <- df_full %>%  select(unfilled_columns)

    cat('Columns picked for NA counts: \n', names(df_for_gaps), '\n')
    names(df_for_gaps) <- paste0(names(df_for_gaps), '_sqc')

    df_daily <- cbind(DoY = df_full$DoY, df_for_gaps)
    df_monthly <- cbind(Month = df_full$Month, df_for_gaps)
    df_yearly <- cbind(Year = df_full$Year, df_for_gaps)

    df_daily_na <- aggregate_all_by(df_daily, 'DoY', percent_non_na)
    df_monthly_na <- aggregate_all_by(df_monthly, 'Month', percent_non_na)
    df_yearly_na <- aggregate_all_by(df_yearly, 'Year', percent_non_na)

    df_daily <- combine_alternating(df_daily_means, df_daily_na, 'DoY')
    df_monthly <- combine_alternating(df_monthly_means, df_monthly_na, 'Month')
    df_yearly <- combine_alternating(df_yearly_means, df_yearly_na, 'Year')

    return(list(df_daily, df_monthly, df_yearly))
}


save_averages <- function(dfs, output_dir, output_prefix) {
    prename = file.path(output_dir, output_prefix)
    write.csv(dfs[[1]], file = paste0(prename, "_daily.csv"), row.names = FALSE)
    write.csv(dfs[[2]], file = paste0(prename, "_monthly.csv"), row.names = FALSE)
    write.csv(dfs[[3]], file = paste0(prename, "_yearly.csv"), row.names = FALSE)
}
