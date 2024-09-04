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
    # applies agg_FUN to unique sets of values in by_col
    # usually original dataframe is simply df = cbind(by_col, data)
    aggregate(data, by_col, agg_FUN)
}


calc_averages <- function(df_full){
    # write.csv(df_full, file = '_test.txt', row.names = FALSE, quote=FALSE)

    df_full$Month <- month(df_full$DateTime)

    df_to_mean <- df_full %>% select(ends_with("_f") | "Reco")
    cat('Columns picked for averaging: \n', names(df_to_mean), '\n')

    # i.e. mean and NA percent will be calculated between rows
    # for which unique_cols values are matching
    unique_cols_sets = list(c('Year', 'Month', 'DoY'), c('Year', 'Month'), c('Year'))
    unique_dfs = lapply(unique_cols_sets, function(set) df_full[set])

    f_mean_any <- function(x) mean(x, na.rm = TRUE)
    df_means <- lapply(unique_dfs, FUN = aggregate_df,
                       data = df_to_mean, agg_FUN = f_mean_any)

    df_to_nna <- df_full %>% select(ends_with("_f") & !starts_with(c("GPP", "Reco")))
    cat('Columns picked for NA counts: \n', names(df_to_nna), '\n')

    df_nna <- lapply(unique_dfs, FUN = aggregate_df,
                     data = df_to_nna, agg_FUN = percent_nna)

    # H_f -> H_sqc, ...
    names(df_nna) <- names(df_nna) %>% gsub('_f', '_sqc', .)

    f_combine <- function(means, nna, col_by)
        combine_cols_alternating(means, nna, col_by)
    df_combined <- mapply(f_combine, df_means, df_nna, unique_cols_sets)

    return(df_combined)
}


save_averages <- function(dfs, output_dir, output_prefix) {
    prename = file.path(output_dir, output_prefix)
    write.csv(dfs[[1]], file = paste0(prename, "_daily.csv"), row.names = FALSE)
    write.csv(dfs[[2]], file = paste0(prename, "_monthly.csv"), row.names = FALSE)
    write.csv(dfs[[3]], file = paste0(prename, "_yearly.csv"), row.names = FALSE)
}
