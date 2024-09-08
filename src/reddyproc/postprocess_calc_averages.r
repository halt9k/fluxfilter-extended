library(dplyr)
library(lubridate)
library(tibble)

nna_percent <- function(vals){
    if (length(vals) > 0)
        1.0 - sum(is.na(vals)) / length(vals)
    else
        0.0
}


combine_cols_alternating <- function(df_a, df_b, col_expected_dupes){
    stopifnot(all(df_a[col_expected_dupes] == df_b[col_expected_dupes]))
    stopifnot(length(df_a) == length(df_b))

    df_ma <- df_a %>% select(!any_of(col_expected_dupes))
    df_mb <- df_b %>% select(!any_of(col_expected_dupes))

    neworder <- order(c(2 * (seq_along(df_ma) - 1) + 1,
                        2 * seq_along(df_mb)))

    merged_alternating <- cbind(df_ma, df_mb)[,neworder]
    cbind(df_a[col_expected_dupes], merged_alternating)
}


merge_cols_aligning <- function(df_a, df_b, col_expected_dupes, align_pair){
    # H_f LE_f U_f , H_sqc LE_sqc U_sqc -> H_f H_sqc U_f U_sqc LE_f LE_sqc
    # only WARNING on missing columns

    stopifnot(all(df_a[col_expected_dupes] == df_b[col_expected_dupes]))

    mask_a <- align_pair[[1]]
    mask_b <- align_pair[[2]]

    names = colnames(df_a)
    insert_names = setdiff(colnames(df_a), col_expected_dupes)
    #for (cname in insert_names) {
        #if (mask_b is not regex of col)
        #    df = cbind(df, col)
        #else if (not can find mask_a in df)
        #    df = cbind(df, col)
        #else
        #    df = append(df, col, after = found_mask_col)
    #}


    stopifnot(length(neworder) != ncols(df_unordered) || any(duplicated(neworder)))
    df_merged <- cbind(df_a, df_b %>% select(!any_of(col_expected_dupes)))[, neworder]
}


aggregate_df <- function(data, by_col, FUN) {
    # TODO there must be better way than rev + swap
    stopifnot(ncol(by_col) < 3)

    # applies agg_FUN to unique sets of values in by_col
    # usually original dataframe is simply df = cbind(by_col, data)

    res = aggregate(data, by = rev(by_col), FUN=FUN)
    if (length(by_col) == 2)
        res <- res[, c(2, 1, 3:ncol(res))]
    return(res)
}


calc_averages <- function(df_full){
    # write.csv(df_full, file = '_test.txt', row.names = FALSE, quote=FALSE)

    df_full$Month <- month(df_full$DateTime)

    # indeed, R have no default list(str) better than %>% select
    cols_f <- colnames(df_full %>% select(ends_with("_f")))
    cols_to_mean <- c(cols_f, 'Reco')
    cat('Columns picked for averaging (Reco added): \n', names(cols_to_mean), '\n')

    cols_nna_sqc <- gsub("_f", "_sqc", setdiff(cols_f, 'GPP_f'))
    cols_to_nna <- gsub("_sqc", "", cols_nna_sqc)
    stopifnot(length(cols_nna_sqc) == length(cols_to_nna))
    cat('Columns picked for NA counts (GPP_f omitted): \n', names(cols_to_nna), '\n')

    df_to_mean <- df_full[cols_to_mean]
    df_to_mean_mon = cbind(Month = df_full$Month, df_to_mean)

    df_to_nna <- df_full[cols_to_nna]
    df_to_nna_mon = cbind(Month = df_full$Month, df_to_nna)

    # i.e. mean and NA percent will be calculated between rows
    # for which unique_cols values are matching
    unique_cols_d = c('Year', 'DoY')
    unique_cols_m = c('Year', 'Month')
    unique_cols_y = c('Year')

    mean_nna <- function(x) mean(x, na.rm = TRUE)
    df_means_d <- aggregate_df(df_to_mean_mon, by_col = df_full[unique_cols_d], mean_nna)
    df_means_m <- aggregate_df(df_to_mean, by_col = df_full[unique_cols_m], mean_nna)
    df_means_y <- aggregate_df(df_to_mean, by_col = df_full[unique_cols_y], mean_nna)

    # renaming is easier before the actual calc
    stopifnot(ncol(df_to_nna) == length(cols_nna_sqc))
    names(df_to_nna) <- cols_nna_sqc
    df_nna_d <- aggregate_df(df_to_nna_mon, by_col = df_full[unique_cols_d], nna_percent)
    df_nna_m <- aggregate_df(df_to_nna, by_col = df_full[unique_cols_m], nna_percent)
    df_nna_y <- aggregate_df(df_to_nna, by_col = df_full[unique_cols_y], nna_percent)

    # TODO why
    # df_nna_d$Month <- df_means_d$Month

    df_combined <- mapply(combine_cols_alternating,
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
