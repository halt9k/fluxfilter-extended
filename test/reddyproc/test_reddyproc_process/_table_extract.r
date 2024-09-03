# two_years
inputDataBkp <- inputData
inputData <- aggregate_all_by(inputDataBkp, 'DoY', mean)[-1,2:12]
bind_rows(inputData[1,], inputData[,])
inputData[1,]$DoY  = 1
inputData$Hour = 1
df_y = inputData[200:365, ]
df_y$Year = 2022
df = bind_rows( df_y, inputData[1:200, ])
write.table(df, file = 'test.txt', sep = ' ', row.names = FALSE, quote=FALSE, na='-9999.0')