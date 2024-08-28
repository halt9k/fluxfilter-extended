library(dplyr)
library(lubridate)
library(tibble)


percent_na <- function(vals){
    sum(is.na(vals)) / length(vals)
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


calc_averages <- function(df_full, site_name){
    df_to_average <- df_full %>%  select(ends_with("_f") | "Reco")
    df_full$Month <- month(df_full$DateTime)
    
    # TODO merge into one func or readable?
    df_daily <- cbind(DoY = df_full$DoY, df_to_average)
    df_monthly <- cbind(Month = df_full$Month, df_to_average)
    df_yearly <- cbind(Year = df_full$Year, df_to_average)
    
    df_daily_means <- aggregate_all_by(df_daily, 'DoY', mean, na.rm = TRUE)
    df_monthly_means <- aggregate_all_by(df_monthly, 'Month', mean, na.rm = TRUE)
    df_yearly_means <- aggregate_all_by(df_yearly, 'Year', mean, na.rm = TRUE)

    
    unfilled_columns <- gsub("_f", "", colnames(df_to_average))
    print("WARNING: GPP column is missing for NA count")
    unfilled_columns <- setdiff(unfilled_columns, c("GPP", "Reco"))
    df_for_gaps <- df_full %>%  select(unfilled_columns)
    names(df_for_gaps) <- paste(names(df_for_gaps), '_sqc')
    
    df_daily <- cbind(DoY = df_full$DoY, df_for_gaps)
    df_monthly <- cbind(Month = df_full$Month, df_for_gaps)
    df_yearly <- cbind(Year = df_full$Year, df_for_gaps)
        
    df_daily_na <- aggregate_all_by(df_daily, 'DoY', percent_na)
    df_monthly_na <- aggregate_all_by(df_monthly, 'Month', percent_na)
    df_yearly_na <- aggregate_all_by(df_yearly, 'Year', percent_na)
    
    df_daily <- combine_alternating(df_daily_means, df_daily_na, 'DoY')
    df_monthly <- combine_alternating(df_monthly_means, df_monthly_na, 'Month')
    df_yearly <- combine_alternating(df_yearly_means, df_yearly_na, 'Year')
    
    
    prefix = site_name + year
    write.csv(df_daily, file = prefix +"daily.csv", row.names = FALSE)
    write.csv(df_monthly, file = prefix + "monthly.csv", row.names = FALSE)
    write.csv(df_yearly, file = prefix + "yearly.csv", row.names = FALSE)
}
