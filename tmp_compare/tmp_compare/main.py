import pandas as pd
import matplotlib.pyplot as plt

df1 = pd.read_csv('/mnt/data/new 1.txt', sep='\t', comment='#')
df2 = pd.read_csv('/mnt/data/2.txt', sep='\t', comment='#')

plt.figure(figsize=(10, 5))
plt.plot(df1.iloc[:, -1], label='File 1 Last Column')
plt.plot(df2.iloc[:, -1], label='File 2 Last Column')
plt.legend()
plt.title('Last Columns of File 1 and File 2')
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(df1.iloc[:, -2], label='File 1 Second Last Column')
plt.plot(df2.iloc[:, -2], label='File 2 Second Last Column')
plt.legend()
plt.title('Second Last Columns of File 1 and File 2')
plt.show()