#%%
# -------------------------------------------------------
# Dividend analysis examples
# -------------------------------------------------------
import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
from trader.tools.dc_tools import set_KoreanFonts

cd_ = os.path.dirname(os.path.abspath(__file__)) # . 
pd_ = os.path.dirname(cd_) # .. 
df_krx_path = os.path.join(pd_, 'data_collect/data/df_krx.feather')
price_db__path = os.path.join(pd_, 'data_collect/data/price_db_.feather')

# created in broker
end_date = pd.to_datetime('now').strftime('%Y%m%d')
div_DB_path = os.path.join(cd_, f'data/div_DB_{end_date}.feather')

df_krx = pd.read_feather(df_krx_path)
price_db_ = pd.read_feather(price_db__path)
div_DB = pd.read_feather(div_DB_path)

# selected companies that have ever increasing dividend
pos_code = []
for col in div_DB.columns:
    if all(div_DB[col][:-1].diff().dropna()>0): 
        pos_code.append(col)

temp1 = div_DB[pos_code]
temp2 = temp1.drop(columns=temp1.columns[temp1.loc[2025].isna()])
temp3 = temp2.drop(columns=temp2.columns[temp2.loc[2024].isna()])
temp4 = temp3.drop(columns=temp3.columns[temp3.loc[2023].isna()])
temp5 = temp4.drop(columns=temp4.columns[temp4.loc[2022].isna()])
temp6 = temp5.drop(columns=temp5.columns[temp5.loc[2021].isna()])
temp7 = temp6.iloc[:-1]
temp8 = temp7.loc[:, temp7.loc[2025].sort_values(ascending=False).index]

name_dict = {}
for col in temp8.columns:
    name = df_krx.loc[col]['Name']
    name_dict[col] = name
temp9 = temp8.rename(columns = name_dict)

# Bar plots using seaborn
for i in range(len(temp9.columns)):
    print(temp9.columns[i])
    plt.figure(figsize=(8, 6))
    sns.barplot(x=temp9.index, y=temp9[temp9.columns[i]], palette='rocket', hue=temp9.index, legend=False)

    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.tick_params(colors='white', labelsize=12)  
    plt.ylabel('KRW/Stock', color='white', fontsize=12)
    plt.xlabel(temp9.index.name, color='white', fontsize=12)  
    
    # Set the background to be transparent
    plt.gcf().set_facecolor('none')  # For figure background
    ax.set_facecolor('none')         # For axes background

    # Adjust layout
    plt.tight_layout()
    plt.show()

# didvidend ratio 
last_available_date_2025 = price_db_[price_db_.index.year == 2025].index.max()
for col in temp8.columns:
    pr =  price_db_.loc[last_available_date_2025, col]
    div_rate = (temp8[col].values[-1])/pr*100
    print(round(div_rate, 2))


#%% -------------------------------------------------------------
# Find highest dividend yield companies in the designated year with yield over threshold
# Removal logic is necessary to be implemented of some financial vehicle companies: reducing face-value after dividend (stock-split).
# ---------------------------------------------------------------
set_KoreanFonts()

year = 2025
threshold = 7 # dividend yield rate to filter larger ones

temp = {}
temp['div'] = div_DB.loc[year]
temp['price'] = price_db_.loc[price_db_.index[price_db_.index.year == year].max()] # calculates year end closing price
temp['rate'] = temp['div']/temp['price']*100
div_year = pd.DataFrame(temp).sort_values(by = 'rate', ascending=False)
div_year = div_year.replace([float('inf'), -float('inf')], float('nan')).dropna()
div_year = div_year.loc[div_year['rate']>threshold]

div_year = pd.DataFrame(div_year).sort_values(by = 'rate', ascending=False)
div_year = div_year.loc[div_year['rate']>threshold]
div_year['name'] = div_year.index.map(lambda x: df_krx.loc[x, 'Name'] if x in df_krx.index else None)
div_year = div_year.dropna()

plt.figure(figsize=(8, 12))
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
