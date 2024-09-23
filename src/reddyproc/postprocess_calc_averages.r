library(dplyr)
library(lubridate)
library(tibble)

combine_cols_alternating <- function(df, df_merge, expected_col_dupes){
    # not tested

    stopifnot(all(df[expected_col_dupes] == df_merge[expected_col_dupes]))
    stopifnot(nrows(df) == nrows(df_merge))

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
    df_unique_merge <- df_merge %>% select(-matches(expected_col_dupes))

    mask_a <- align_pair[[1]]
    mask_b <- align_pair[[2]]
    df_unmasks <- sub(mask_a, '', colnames(df))
    merge_unmasks <- sub(mask_b, '', colnames(df_unique_merge))

    if (anyDuplicated(merge_unmasks) || anyDuplicated(df_unmasks))
        stop('\n Cannot merge columns due to duplicate names for align patterns \n')

    names <- c(colnames(df), colnames(df_unique_merge))
    unmasks <- c(df_unmasks, merge_unmasks)

    unique_unmasks <- unique(unmasks)
    reordered_colnames <- unlist(Map(function(.) {names[unmasks == .]}, unique_unmasks))
    stopifnot(length(reordered_colnames) == ncol(merge))
    stopifnot(!duplicated(reordered_colnames))

    return(cbind(df, df_unique_merge)[reordered_colnames])
}


aggregate_df <- function(data, by_col, FUN) {
    # forms unique combinations with by_col
    # applies agg_FUN to all rows matching onr of combination
    # usually original dataframe is simply df = cbind(by_col, data)

    # rev(by_col): reverse is nessesary for YMD column order,
    # i.e. correct sort order during aggregate is 1) DoY 2) Month 3) Year
    res <- aggregate(data, by = rev(by_col), FUN = FUN)

    # restore YMD column order
    res <- res[c(colnames(by_col), colnames(data))]
    return(res)
}



remove_too_short_years <- function(df) {
    stopifnot(nrow(df) > 3)

    first <- 1
    last <- nrow(df)

    if (df$Year[1] < df$Year[2]) {
        cat('Averages: first row excluded due to too short year \n')
        first <- 2
    }
    if (df$Year[nrow(df) - 1] < df$Year[nrow(df)]) {
        cat('Averages: last row excluded due to too short year \n')
        last <- nrow(df) - 1
    }

    df[first:last,]
}


calc_averages <- function(df_full){
    # write.csv(df_full, file = '_test.txt', row.names = FALSE, quote=FALSE)
    df <- remove_too_short_years(df_full)
    df$Month <- month(df$DateTime)

    # indeed, R have no default list(str) better than %>% select
    cols_f <- colnames(df %>% select(ends_with("_f")))
    cols_to_mean <- c(cols_f)
    if ('Reco' %in% colnames(df))
        cols_to_mean <- c(cols_to_mean, 'Reco')
    cat('Columns picked for averaging (Reco added if possible): \n', cols_to_mean, '\n')

    cols_nna_sqc <- gsub("_f", "_sqc", setdiff(cols_f, 'GPP_f'))
    cols_to_nna <- gsub("_sqc", "", cols_nna_sqc)
    cat('Columns picked for NA counts (GPP_f omitted): \n',cols_to_nna, '\n')

    missing = setdiff(cols_to_nna, colnames(df))
    if (length(missing) > 0)
        stop(msg = paste('Expected columns are missing: \n', missing, '\n'))

    df_to_mean <- df[cols_to_mean]
    df_to_nna <- df[cols_to_nna]

    # i.e. mean and NA percent will be calculated between rows
    # for which unique_cols values are matching
    unique_cols_d <- c('Year', 'Month', 'DoY')
    unique_cols_m <- c('Year', 'Month')
    unique_cols_y <- c('Year')

    # mapply is less readable here
    mean_nna <- function(x) mean(x, na.rm = TRUE)
    df_means_d <- aggregate_df(df_to_mean, by_col = df[unique_cols_d], mean_nna)
    df_means_m <- aggregate_df(df_to_mean, by_col = df[unique_cols_m], mean_nna)
    df_means_y <- aggregate_df(df_to_mean, by_col = df[unique_cols_y], mean_nna)

    # renaming is easier before the actual calc
    stopifnot(ncol(df_to_nna) == length(cols_nna_sqc) - length(missing))
    names(df_to_nna) <- cols_nna_sqc
    nna_percent <- function(x) return(mean(!is.na(x)))
    df_nna_d <- aggregate_df(df_to_nna, by_col = df[unique_cols_d], nna_percent)
    df_nna_m <- aggregate_df(df_to_nna, by_col = df[unique_cols_m], nna_percent)
    df_nna_y <- aggregate_df(df_to_nna, by_col = df[unique_cols_y], nna_percent)

    df_d <- merge_cols_aligning(df_means_d, df_nna_d, unique_cols_d, align_pair = c('*_f$', '*_sqc$'))
    df_m <- merge_cols_aligning(df_means_m, df_nna_m, unique_cols_m, align_pair = c('*_f$', '*_sqc$'))
    df_y <- merge_cols_aligning(df_means_y, df_nna_y, unique_cols_y, align_pair = c('*_f$', '*_sqc$'))

    return(list(daily = df_d, monthly = df_m, yearly = df_y))
}


save_averages <- function(dfs, output_dir, output_unmask, ext){
    prename = file.path(output_dir, output_unmask)
    d_name <- paste0(prename, '_daily', ext)
    m_name <- paste0(prename, '_monthly', ext)
    y_name <- paste0(prename, '_yearly', ext)

    write.csv(dfs$daily, file = d_name, row.names = FALSE)
    write.csv(dfs$monthly, file = m_name, row.names = FALSE)
    write.csv(dfs$yearly, file = y_name, row.names = FALSE)

    cat(sprintf('Saved summary stats to : \n %s \n %s \n %s \n',
                d_name, m_name, y_name))

}
