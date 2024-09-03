library(dplyr)
library(lubridate)
library(tibble)


percent_nna <- function(vals){
    if (length(vals) > 0)
        1.0 - sum(is.na(vals)) / length(vals)
    else
        0.0
}


aggregate_df_by_cols <- function(df, cols, del_cols, FUN, ...){
    df_without_cols = df %>% select(-all_of(cols))
    res <- aggregate(x = df_without_cols, by = df[cols], FUN, ...)
    return(res)
}


combine_cols_alternating <- function(df_a, df_b, col_expected_dupe){
    neworder <- order(c(2*(seq_along(df_a) - 1) + 1,
                        2*seq_along(df_b)))

    stopifnot(df_a$col_expected_dupe == df_b$col_expected_dupe)
    neworder = neworder[-1]

    cbind(df_a, df_b)[,neworder]
}


calc_averages <- function(df_full){
    # write.csv(df_full, file = '_test.txt', row.names = FALSE, quote=FALSE)

    df_full$Month <- month(df_full$DateTime)

    doy = c('Year', 'Month', 'DoY')
    df_for_means <- df_full %>% select(matches(doy) | ends_with("_f") | "Reco")

    cat('Columns picked for averaging: \n', setdiff(names(df_for_means), doy), '\n')

    cols_list = list(c('Year', 'Month', 'DoY'), c('Year', 'Month'), c('Year'))
    del_cols_list = list(c(''), c('DoY'), c('Month', 'DoY'))

    aggregate_df_by_cols(df = df_for_means, cols_list[[1]], del_cols_list[[1]], FUN = mean, na.rm = TRUE)
    df_means <- mapply(
        aggregate_df_by_cols(df = df_for_means, cols, del_cols, FUN = mean, na.rm = TRUE),
        cols = cols_list, del_cols = del_cols_list)

    unfilled_columns <- gsub("_f", "", colnames(df_avg))
    unfilled_columns <- setdiff(unfilled_columns, c("GPP", "Reco"))
    df_for_gaps <- df_full %>%  select(unfilled_columns)

    cat('Columns picked for NA counts: \n', names(df_for_gaps), '\n')
    names(df_for_gaps) <- paste0(names(df_for_gaps), '_sqc')

    df <- cbind(Year = df_full$Year,
                DoY = df_full$DoY,
                Month = df_full$Month,
                df_for_gaps)

    df_daily_na <- aggregate_df_by_cols(df_daily, 'DoY', percent_nna)
    df_monthly_na <- aggregate_df_by_cols(df_monthly, 'Month', percent_nna)
    df_yearly_na <- aggregate_df_by_cols(df_yearly, 'Year', percent_nna)

    df_nna <- mapply(
        aggregate_df_by_cols(df = df, col, del_col, FUN = percent_nna, na.rm = TRUE),
        col = cols, del_col = del_cols)

    df_daily <- combine_cols_alternating(df_daily_means, df_daily_na, 'DoY')
    df_monthly <- combine_cols_alternating(df_monthly_means, df_monthly_na, 'Month')
    df_yearly <- combine_cols_alternating(df_yearly_means, df_yearly_na, 'Year')

    return(list(df_daily, df_monthly, df_yearly))
}


save_averages <- function(dfs, output_dir, output_prefix) {
    prename = file.path(output_dir, output_prefix)
    write.csv(dfs[[1]], file = paste0(prename, "_daily.csv"), row.names = FALSE)
    write.csv(dfs[[2]], file = paste0(prename, "_monthly.csv"), row.names = FALSE)
    write.csv(dfs[[3]], file = paste0(prename, "_yearly.csv"), row.names = FALSE)
}
