# for averaging
# code is to run on calc_averages entry
inputDataBkp <- inputData
inputData <- aggregate_all_by(inputDataBkp, 'DoY', mean)[-1,2:12]
bind_rows(inputData[1,], inputData[,])
inputData[1,]$DoY  = 1
inputData$Hour = 1
df_y = inputData[200:365, ]
df_y$Year = 2022
df = bind_rows( df_y, inputData[1:200, ])
write.csv(df, file = 'test.txt', row.names = FALSE, quote=FALSE)

test_set[test_set$Year == 2022,]$H_f = 13
test_set[test_set$Year == 2022,]$LE_f = NA
test_set[test_set$Year == 2022,]$LE_f[4]
test_set[test_set$Year == 2022,]$LE_f[4] = 17