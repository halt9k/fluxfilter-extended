library(dplyr)
library(lubridate)
library(tibble)

nna_percent <- function(vals){
    if (length(vals) > 0)
        1.0 - sum(is.na(vals)) / length(vals)
    else
        0.0
}


combine_cols_alternating <- function(df, df_merge, expected_col_dupes){
    # not tested

    stopifnot(all(df[expected_col_dupes] == df_merge[expected_col_dupes]))
    stopifnot(length(df) == length(df_merge))

    df_ma <- df %>% select(-any_of(expected_col_dupes))
    df_mb <- df_merge %>% select(-any_of(expected_col_dupes))

    neworder <- order(c(2 * (seq_along(df_ma) - 1) + 1,
                        2 * seq_along(df_mb)))

    merged_alternating <- cbind(df_ma, df_mb)[,neworder]
    cbind(df[expected_col_dupes], merged_alternating)
}


merge_cols_aligning <- function(df, df_merge, expected_col_dupes, align_pair){
    # H_f LE_f U_f , H_sqc LE_sqc U_sqc -> H_f H_sqc U_f U_sqc LE_f LE_sqc
    # supports regex for align_pair '*_f$', '*_sqc$'
    # supports missing align_pair[[2]] columns

    stopifnot(df[expected_col_dupes] == df_merge[expected_col_dupes])
    df_unique_merge = df_merge %>% select(-matches(expected_col_dupes))

    mask_a <- align_pair[[1]]
    mask_b <- align_pair[[2]]
    df_unmasks <- sub(mask_a, '', colnames(df))
    merge_unmasks <- sub(mask_b, '', colnames(df_unique_merge))

    if (anyDuplicated(merge_unmasks) || anyDuplicated(df_unmasks))
        stop('\n Cannot merge columns due to duplicate names for align patterns \n')

    names = c(colnames(df), colnames(df_unique_merge))
    unmasks = c(df_unmasks, merge_unmasks)

    unique_unmasks = unique(unmasks)
    reordered_cols = unlist(Map(function(.) {names[unmasks == .]}, unique_unmasks))
    stopifnot(length(reordered_cols) == ncol(merge))
    stopifnot(!duplicated(reordered_cols))

    return(cbind(df, df_unique_merge)[reordered_cols])
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
    cols_to_mean <- c(cols_f)
    if ('Reco' %in% colnames(df_full))
        cols_to_mean <- c(cols_to_mean, 'Reco')
    cat('Columns picked for averaging (Reco added if possible): \n', cols_to_mean, '\n')

    cols_nna_sqc <- gsub("_f", "_sqc", setdiff(cols_f, 'GPP_f'))
    cols_to_nna <- gsub("_sqc", "", cols_nna_sqc)
    stopifnot(length(cols_nna_sqc) == length(cols_to_nna))
    cat('Columns picked for NA counts (GPP_f omitted): \n',cols_to_nna, '\n')

    missing = setdiff(cols_to_nna, colnames(df_full))
    if (length(missing) > 0)
        stop(msg = paste('Expected columns are missing: \n', missing, '\n'))

    df_to_mean <- df_full[cols_to_mean]
    df_to_mean_mon = cbind(Month = df_full$Month, df_to_mean)

    df_to_nna <- df_full[cols_to_nna]

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
    stopifnot(ncol(df_to_nna) == length(cols_nna_sqc) - length(missing))
    names(df_to_nna) <- cols_nna_sqc
    df_nna_d <- aggregate_df(df_to_nna, by_col = df_full[unique_cols_d], nna_percent)
    df_nna_m <- aggregate_df(df_to_nna, by_col = df_full[unique_cols_m], nna_percent)
    df_nna_y <- aggregate_df(df_to_nna, by_col = df_full[unique_cols_y], nna_percent)

    df_combined <- mapply(merge_cols_aligning,
                          df = list(df_means_d, df_means_m, df_means_y),
                          df_merge = list(df_nna_d, df_nna_m, df_nna_y),
                          list(unique_cols_d, unique_cols_m, unique_cols_y),
                          MoreArgs = list(align_pair = c('*_f$', '*_sqc$')))

    return(df_combined)
}


save_averages <- function(dfs, output_dir, output_unmask, ext){
    prename = file.path(output_dir, output_unmask)
    d_name <- paste0(prename, '_daily', ext)
    m_name <- paste0(prename, '_monthly', ext)
    y_name <- paste0(prename, '_yearly', ext)

    cat(sprintf('Saving summary stats to : \n %s \n %s \n %s \n'),
        d_name, m_name, y_name)

    write.csv(dfs[[1]], file = d_name, row.names = FALSE)
    write.csv(dfs[[2]], file = m_name, row.names = FALSE)
    write.csv(dfs[[3]], file = y_name, row.names = FALSE)
}
