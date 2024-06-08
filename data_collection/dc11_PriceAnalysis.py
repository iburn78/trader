#%%
import pandas as pd
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import seaborn as sns

price_DB = pd.read_feather('data/price_DB.feather')
meta = fdr.StockListing('KRX-DESC')
fr_main = pd.read_feather('data/financial_reports_main.feather')

#%% 
code = '005930'
data = price_DB.iloc[:200]
fig, ax = plt.subplots(figsize=(20, 7.5))
sns.lineplot(x=data.index, y=code, data=data)
ax.set_xlabel('')
ax.set_ylabel('')
plt.show()
#%%
opincome = fr_main.loc[(fr_main.code == code) & (fr_main.fs_div == 'CFS') & (fr_main.account == 'operating_income')]
non_empty_columns = [col for col in opincome.columns if not pd.isnull(opincome[col].values[0])]

print(non_empty_columns)

