#%% 

import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime 
#%% 

df_krx_desc = fdr.StockListing('KRX-DESC')

#%%
search_str = '동양생명'
search_res = df_krx_desc.loc[df_krx_desc['Name'].str.contains(search_str)][['Code','Name']]

display(search_res)
if len(search_res) == 1: 
    code = search_res['Code'].values[0]
    print(code)

#%%
codes = ['032830', '088350', '085620', '082640']
names = []
for code in codes: 
    name = df_krx_desc.loc[df_krx_desc['Code']==code]['Name'].values[0]
    names.append(name)
# print(names)

#%%
price_data = pd.DataFrame()
period = '2024'
basedate = '2024-05-17'

for code in codes: 
    df = fdr.DataReader(code, period)
    price_data[code] = df['Close']

basedate = datetime.strptime(basedate, '%Y-%m-%d')
price_data = price_data.loc[price_data.index <= basedate]

price_data.index = price_data.index.strftime('%Y-%m-%d')
price_data.columns = names
print(price_data)
#%% 

meta_data = pd.DataFrame(columns = names)
meta_data.loc[len(meta_data)] = price_data.mean()

#%% 
price_data.to_excel('price_data.xlsx')