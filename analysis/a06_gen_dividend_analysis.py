#%%
import pandas as pd
import os

pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .. 
df_krx_path = os.path.join(pd_, 'data_collection/data/df_krx.feather')
price_DB_path = os.path.join(pd_, 'data_collection/data/price_DB.feather')

# build div_DB to do the analysis first, using dc15_DividendDB.py
div_DB_path = os.path.join(pd_, 'data_collection/data/div_DB_20241014.feather')

df_krx = pd.read_feather(df_krx_path)
price_DB = pd.read_feather(price_DB_path)
div_DB = pd.read_feather(div_DB_path)

#%% -------------------------------------------------------------
# Find highest dividend yield companies in the designated year with yield over threshold
# Face value normalize is done and reflected to div_DB already (in get_div() of dc15_DividendDB.py) 
# Removal logic is necessary to be implemented of some financial vehicle companies: reducing face-value after dividend.
# ---------------------------------------------------------------

from trader.analysis.analysis_tools import *
from trader.analysis.broker import Broker

year = 2024
threshold = 7 # dividend yield rate to filter larger ones
broker = Broker()

temp = {}
temp['div'] = div_DB.loc[year]
temp['price'] = price_DB.loc[price_DB.index[price_DB.index.year == year].max()] # calculates year end closing price
temp['rate'] = temp['div']/temp['price']*100

div_year = pd.DataFrame(temp).sort_values(by = 'rate', ascending=False)
div_year = div_year.replace([float('inf'), -float('inf')], float('nan')).dropna()
div_year = div_year.loc[div_year['rate']>threshold]

div_year = pd.DataFrame(div_year).sort_values(by = 'rate', ascending=False)
div_year = div_year.loc[div_year['rate']>threshold]
div_year['name'] = div_year.index.map(lambda x: df_krx.loc[x, 'Name'] if x in df_krx.index else None)
div_year = div_year.dropna()

#%% 

import seaborn as sns
import matplotlib.pyplot as plt
from trader.tools.tools import set_KoreanFonts

set_KoreanFonts()

plt.figure(figsize=(8, 6))
sns.barplot(x=div_year['rate'], y=div_year['name'], palette='rocket', hue=div_year['name'], legend=False)

ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('white')
ax.spines['left'].set_color('white')
ax.tick_params(colors='white', labelsize=12)  
plt.ylabel('Top Companies', color='white', fontsize=12)
plt.xlabel(f'Dividend/Stock Price(%, {year})', color='white', fontsize=12) 
    
# Set the background to be transparent
plt.gcf().set_facecolor('none')  # For figure background
ax.set_facecolor('none')         # For axes background

# Adjust layout
plt.tight_layout()
plt.show()



