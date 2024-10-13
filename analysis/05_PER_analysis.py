#%%
import pandas as pd

fr_main_path = '../data_collection/data/financial_reports_main.feather'
df_krx_path = '../data_collection/data/df_krx.feather'
price_DB_path = '../data_collection/data/price_DB.feather'
volume_DB_path = '../data_collection/data/volume_DB.feather'
outshare_DB_path = '../data_collection/data/outshare_DB.feather'

fr_main = pd.read_feather(fr_main_path)
df_krx = pd.read_feather(df_krx_path)
price_DB = pd.read_feather(price_DB_path)
volume_DB = pd.read_feather(volume_DB_path)
outshare_DB = pd.read_feather(outshare_DB_path)

display(fr_main)
display(df_krx)
display(price_DB)
display(volume_DB)
display(outshare_DB)



