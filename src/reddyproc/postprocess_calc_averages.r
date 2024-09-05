library(dplyr)
library(lubridate)
library(tibble)

percent_nna <- function(vals){
    if (length(vals) > 0)
        1.0 - sum(is.na(vals)) / length(vals)
    else
        0.0
}


combine_cols_alternating <- function(df_a, df_b, col_expected_dupes){
    stopifnot(all(df_a[col_expected_dupes] == df_b[col_expected_dupes]))

    df_ma <- df_a %>% select(!any_of(col_expected_dupes))
    df_mb <- df_b %>% select(!any_of(col_expected_dupes))

    neworder <- order(c(2 * (seq_along(df_ma) - 1) + 1,
                        2 * seq_along(df_mb)))

    merged_alternating <- cbind(df_ma, df_mb)[,neworder]
    cbind(df_a[col_expected_dupes], merged_alternating)
}


aggregate_df <- function(data, by_col, agg_FUN) {
    # there must be better way than rev + swap
    stopifnot(ncol(by_col) < 3)

    # applies agg_FUN to unique sets of values in by_col
    # usually original dataframe is simply df = cbind(by_col, data)

    res = aggregate(data, by = rev(by_col), agg_FUN)
    if (length(by_col) == 2)
        res <- res[, c(2, 1, 3:ncol(res))]
    return(res)
}


calc_averages <- function(df_full){
    # write.csv(df_full, file = '_test.txt', row.names = FALSE, quote=FALSE)

    df_full$Month <- month(df_full$DateTime)

    df_to_mean <- df_full %>% select(ends_with("_f") | "Reco")
    df_to_mean_d = cbind(Month = df_full$Month, df_to_mean)
    cat('Columns picked for averaging: \n', names(df_to_mean), '\n')

    # i.e. mean and NA percent will be calculated between rows
    # for which unique_cols values are matching
    unique_cols_d = c('Year', 'DoY')
    unique_cols_m = c('Year', 'Month')
    unique_cols_y = c('Year')

    f_mean_any <- function(x) mean(x, na.rm = TRUE)

    df_means_d <- aggregate_df(df_to_mean_d, by_col = df_full[unique_cols_d],
                               agg_FUN = f_mean_any)
    df_means_m <- aggregate_df(df_to_mean, by_col = df_full[unique_cols_m],
                               agg_FUN = f_mean_any)
    df_means_y <- aggregate_df(df_to_mean, by_col = df_full[unique_cols_y],
                               agg_FUN = f_mean_any)

    df_to_nna <- df_full %>% select(ends_with("_f") & !starts_with(c("GPP", "Reco")))
    df_to_nna_d = cbind(Month = df_full$Month, df_to_nna)
    cat('Columns picked for NA counts: \n', names(df_to_nna), '\n')

    # H_f -> H_sqc, ...
    names(df_to_nna) <- names(df_to_nna) %>% gsub('_f', '_sqc', .)

    df_nna_d <- aggregate_df(df_to_nna_d, by_col = df_full[unique_cols_d],
                               agg_FUN = percent_nna)
    df_nna_m <- aggregate_df(df_to_nna, by_col = df_full[unique_cols_m],
                               agg_FUN = percent_nna)
    df_nna_y <- aggregate_df(df_to_nna, by_col = df_full[unique_cols_y],
                               agg_FUN = percent_nna)

    df_nna_d$Month <- df_means_d$Month

    f_combine <- function(means, nna, col_by)
        combine_cols_alternating(means, nna, col_by)
    df_combined <- mapply(f_combine,
                          list(df_means_d, df_means_m, df_means_y),
                          list(df_nna_d, df_nna_m, df_nna_y),
                          list(c(unique_cols_d, 'Month'), unique_cols_m, unique_cols_y))

    return(df_combined)
}


save_averages <- function(dfs, output_dir, output_prefix) {
    prename = file.path(output_dir, output_prefix)
    write.csv(dfs[[1]], file = paste0(prename, "_daily.csv"), row.names = FALSE)
    write.csv(dfs[[2]], file = paste0(prename, "_monthly.csv"), row.names = FALSE)
    write.csv(dfs[[3]], file = paste0(prename, "_yearly.csv"), row.names = FALSE)
}
