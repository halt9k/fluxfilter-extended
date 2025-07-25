# common R routines, all in one file for now

library(dplyr)


RE <- 'REddyProc Extended: '
RM <- 'REddyProc Means: '
RU <- 'uStar patch: '


is.not.null <- function(x) !is.null(x)
`%ni%` <- Negate(`%in%`)


assert <- function(x, msg){
    if (x != TRUE)
        stop('Assertion failure: ', msg)
}


insert_row <- function(df, row, r) {
    nrows <- nrow(df)

    if (is.null(nrows)) {
        warning('\n', RE, 'Attempt to insert a row in the empty df cancelled')
        return()
    }
    if (r > nrows) {
        warning('\n', RE, 'Attempt to insert a row outside of df, inserting as last')
        r <- nrows
    }

    res <- df
    res[seq(r + 1, nrow(df) + 1), ] <- df[seq(r, nrow(df)), ]
    res[r,] <- row
    res
}


.combine_cols_alternating <- function(df, df_add, expected_col_dupes){
    # not tested

    stopifnot(all(df[expected_col_dupes] == df_add[expected_col_dupes]))
    stopifnot(nrows(df) == nrows(df_add))

    df_ma <- df %>% select(-any_of(expected_col_dupes))
    df_mb <- df_add %>% select(-any_of(expected_col_dupes))

    neworder <- order(c(2 * (seq_along(df_ma) - 1) + 1,
                        2 * seq_along(df_mb)))

    merged_alternating <- cbind(df_ma, df_mb)[,neworder]
    cbind(df[expected_col_dupes], merged_alternating)
}


merge_cols_aligning <- function(df, df_add, expected_col_dupes, f_align_rule){
    # f_align_rule:
    #     function to propose best column insert position:
    #     function(<df_add_col_name>) -> <df_col_name>
    #     if returns NULL or df_column is missing, just adds df_add column to the right of df
    #
    #     for example, if f_align_rule is: function(cn) sub('_f$', '_sqc', cn)
    #     merge will be: H_f LE_f H_sqc LE_sqc -> H_f H_sqc U_f U_sqc LE_f LE_sqc

    stopifnot(df[expected_col_dupes] == df_add[expected_col_dupes])
    df_unique_add <- df_add %>% select(-matches(expected_col_dupes))

    colnames_df <- colnames(df)
    colnames_df_add <- colnames(df_unique_add)
    align_target <- f_align_rule(colnames_df_add)
    align_target[!align_target %in% colnames_df] <- NULL

    colnames_df_add_unpaired <- colnames_df_add[is.null(align_target)]

    col_or_paired <- function(cn) c(cn, colnames_df_add[align_target == cn])
    tgt_col_order <- c(unlist(Map(col_or_paired, colnames_df)), colnames_df_add_unpaired)

    df_res <- cbind(df, df_unique_add)

    stopifnot(ncol(tgt_col_order) == ncol(df_res))
    stopifnot(tgt_col_order %in% colnames(df_res) %>% all)

    return(df_res[tgt_col_order])
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


anyNAN <- function(df) {
    if (is.list(df))
        df <- as.matrix(df)
    is.nan(df) %>% any
}


nna_ratio <- function(x) {
    # 0 if all NA or NaN, 1 if all exist

    return(mean(!is.na(x)))
}


get_default_arg_value <- function(fun, arg) {
    # example:
    # mean_nna <- function(x, nna_threshold = NULL){
    # NULL <- get_default_arg_value(mean_nna, nna_threshold)
    formals(fun)[[arg]]
}


mean_nna <- function(x, nna_threshold = NULL){
    # fixes:
    # mean(c(), na.rm = TRUE) = NA
    # mean(c(NA), na.rm = TRUE) = NaN ?
    # to:
    # mean_nna(c()) = NA
    # mean_nna(c(NA, NA)) = NA
    #
    # also examples:
    # mean_nna(c(1, NA, 3)) = 2
    # mean_nna(c(NaN, ...)) = undefined
    # if enough values exist above threshold ratio

    res <- mean(x, na.rm = TRUE)

    if (is.nan(res) && length((x) > 0))
        res <- NA

    if (is.null(nna_threshold)) {
        return(res)
    } else {
        stopifnot(between(nna_threshold, 0, 1))
        if (nna_ratio(x) > nna_threshold)
            return(res)
        else
            return(NA)
    }
}


interactive_plot_columns <- function(col1, col2) {
    library(plotly)
    x <- c(1:length(col1))
    df <- data.frame(x, col1, col2)
    fig <- plot_ly(df, x = ~x, y = ~col1, type = 'scatter', mode = 'lines', name = 'col1')
    fig <- fig %>% add_trace(y = ~col2, name = 'col2', mode = 'lines')
    fig
}


fmt_hm <- function(fp_hour){
    # formats time
    # 6.5 -> 06:30
    return(sprintf("%02i:%02i", trunc(fp_hour), trunc(fp_hour %% 1 * 60)))
}


all_duplicated <- function(x) {
    # for example, to see cols with the same name in df:
    # df[all_duplicated(colnames(df))]

    duplicated(x) | duplicated(x, fromLast = TRUE)
}


df_to_text <- function(df)
    # not trivial, works in edge cases like named rows
    paste(capture.output(df), collapse = '\n')
