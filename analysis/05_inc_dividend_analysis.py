#%%
# -------------------------------------------------------
# Dividend analysis example
# -------------------------------------------------------
import pandas as pd

df_krx_path = '../data_collection/data/df_krx.feather'
price_DB_path = '../data_collection/data/price_DB.feather'
# build div_DB to do the analysis first, using dc15_DividendDB.py
div_DB_path = '../data_collection/data/div_DB_20241014.feather'

df_krx = pd.read_feather(df_krx_path)
price_DB = pd.read_feather(price_DB_path)
div_DB = pd.read_feather(div_DB_path)

display(df_krx)
display(price_DB)
display(div_DB)

#%% 
# selected companies that have ever increasing dividend
pos_code = []
for col in div_DB.columns:
    if all(div_DB[col][:-1].diff().dropna()>0): 
        pos_code.append(col)
print(pos_code)

#%% 
temp1 = div_DB[pos_code]
temp2 = temp1.drop(columns=temp1.columns[temp1.loc[2023].isna()])
temp3 = temp2.drop(columns=temp2.columns[temp2.loc[2022].isna()])
temp4 = temp3.drop(columns=temp3.columns[temp3.loc[2021].isna()])
temp5 = temp4.drop(columns=temp4.columns[temp4.loc[2020].isna()])
temp6 = temp5.drop(columns=temp5.columns[temp5.loc[2019].isna()])
temp7 = temp6.iloc[:-1]
temp8 = temp7.loc[:, temp7.loc[2023].sort_values(ascending=False).index]

#%% 
name_dict = {}
for col in temp8.columns:
    name = df_krx.loc[col]['Name']
    name_dict[col] = name
temp9 = temp8.rename(columns = name_dict)
display(temp9)

#%%  
# -------------------------------------------------------
# Bar plots using seaborn
# -------------------------------------------------------
import seaborn as sns
import matplotlib.pyplot as plt

# Plotting
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

#%%
last_available_date_2023 = price_DB[price_DB.index.year == 2023].index.max()
for col in temp8.columns:
    pr =  price_DB.loc[last_available_date_2023, col]
    div_rate = (temp8[col].values[-1])/pr*100
    print(div_rate)
