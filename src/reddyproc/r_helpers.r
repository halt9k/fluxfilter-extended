# common R routines, all in one file for now

library(dplyr)


.combine_cols_alternating <- function(df, df_merge, expected_col_dupes){
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
    # example:
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


first_and_last <- function(vec){
    ret <- vec
    if (length(vec) > 2)
        ret <- c(vec[1], vec[length(vec)])
    return(ret)
}


str_right = function(string, n) {
    substr(string, nchar(string) - (n - 1), nchar(string))
}


str_left = function(string, n) {
    substr(string, 1, n)
}


add_file_prefix <- function(fpath, prefix){
    dir <- dirname(fpath)
    base <- basename(fpath)
    stopifnot(str_right(prefix, 1) != '_' && str_left(base, 1) != '_')
    return(file.path(dir, paste0(prefix, '_', base)))
}


nna_ratio <- function(x) {
    # 0 if all NA, 1 if all exist

    return(mean(!is.na(x)))
}


mean_nna <- function(x, nna_threshold = NULL){
    # mean skipping NA values,
    # if enough values exist above threshold ratio

    nna_mean <- mean(x, na.rm = TRUE)
    if (is.null(nna_threshold)) {
        return(nna_mean)
    } else {
        stopifnot(between(nna_threshold, 0, 1))
        if (nna_ratio(x) > nna_threshold)
            return(nna_mean)
        else
            return(NA)
    }
}


fmt_hm <- function(fp_hour){
    # formats time
    # 6.5 -> 06:30
    return(sprintf("%02i:%02i", trunc(fp_hour), trunc(fp_hour %% 1 * 60)))
}
