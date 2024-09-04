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


aggregate_df <- function(df_data, df_by, FUN) {
    # usually simply df = cbind(df_data, df_by)
    aggregate(df_data, df_by, FUN)
}


calc_averages <- function(df_full){
    # write.csv(df_full, file = '_test.txt', row.names = FALSE, quote=FALSE)

    df_full$Month <- month(df_full$DateTime)

    df_to_mean <- df_full %>% select(ends_with("_f") | "Reco")
    cat('Columns picked for averaging: \n', names(df_to_mean), '\n')

    # i.e. mean will be calculated between rows for which unique_cols are unique
    unique_cols_sets = list(c('Year', 'Month', 'DoY'), c('Year', 'Month'), c('Year'))
    df_aggregate_by = df_full[c('Year', 'Month', 'DoY')]

    f_mean_any <- function(x) mean(x, na.rm = TRUE)
    aggregate_df_bind <- function(cols_pick)
        aggregate_df(df_to_mean, df_aggregate_by[cols_pick], FUN = f_mean_any)
    df_means <- lapply(unique_cols_sets, aggregate_df_bind)
    # TODO lappy supports d=d?


    df_to_nna <- df_full %>% select(ends_with("_f") & !starts_with(c("GPP", "Reco")))
    cat('Columns picked for NA counts: \n', names(df_to_nna), '\n')

    names(df_to_nna) <- names(df_to_nna) %>% gsub('_f', '_sqc', .)

    aggregate_df_bind <- function(cols_pick)
        aggregate_df(df_to_nna, df_aggregate_by[cols_pick], FUN = percent_nna)
    df_nna <- lapply(unique_cols_sets, aggregate_df_bind)


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
