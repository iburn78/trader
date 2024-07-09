#%% 
import FinanceDataReader as fdr

s = fdr.DataReader('005930')
k = fdr.StockListing('KRX-DESC')
print(s)
print(k)
#%% 
r = fdr.StockListing('KRX')
print(r)

#%% 
import pandas as pd 

df_krx = pd.read_feather('data/df_krx.feather')
print(df_krx.columns)
