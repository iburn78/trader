#%%
import FinanceDataReader as fdr
import os
import pandas as pd

pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
pr_db_file = os.path.join(pd_, 'data_collect/data/price_DB.feather') 
pr_db = pd.read_feather(pr_db_file)
vol_db_file = os.path.join(pd_, 'data_collect/data/volume_DB.feather') 
vol_db = pd.read_feather(vol_db_file)
df_krx_file = os.path.join(pd_, 'data_collect/data/df_krx.feather') 
df_krx = pd.read_feather(df_krx_file)

display(pr_db)
display(vol_db)
display(df_krx)


#%% 
try:  
    fdr.StockListing('KRX', '20260606')
except:
    print('hey')

#%%
market_dates = fdr.DataReader('005930').index
#%% 
print(market_dates[-1].date()==pd.Timestamp('2026-06-10').date())

print(type(market_dates[-1]))