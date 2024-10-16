#%%
import pandas as pd

fr_main_path = '../data_collection/data/financial_reports_main.feather'
df_krx_path = '../data_collection/data/df_krx.feather'
price_DB_path = '../data_collection/data/price_DB.feather'
volume_DB_path = '../data_collection/data/volume_DB.feather'
outshare_DB_path = '../data_collection/data/outshare_DB.feather'
div_DB_path = '../data_collection/data/div_DB_20241014.feather'

fr_main = pd.read_feather(fr_main_path)
df_krx = pd.read_feather(df_krx_path)
price_DB = pd.read_feather(price_DB_path)
volume_DB = pd.read_feather(volume_DB_path)
outshare_DB = pd.read_feather(outshare_DB_path)
div_DB = pd.read_feather(div_DB_path)

display(fr_main)
display(df_krx)
display(price_DB)
display(volume_DB)
display(outshare_DB)
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
#%% 

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

print(temp9)

#%%  
import seaborn as sns
import matplotlib.pyplot as plt

# Plotting
for i in range(len(temp9.columns)):
    print('-----------------')
    print(temp9.columns[i])
    plt.figure(figsize=(8, 6))
    
    # Create the barplot
    sns.barplot(x=temp9.index, y=temp9[temp9.columns[i]], palette='viridis')
    
    # Add labels with white text color and set fontsize to 20 (adjustable)
    plt.ylabel('KRW/Stock', color='white', fontsize=14)
    plt.xlabel(temp9.index.name, color='white', fontsize=14)  # Adjust if there's an index name, or use '' for no label
    
    # Remove the top and right spines (axes)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Set the bottom and left spines (axes) to white
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    
    # Set tick parameters to make them white and adjust the font size
    ax.tick_params(colors='white', labelsize=16)  # Adjust tick label size here
    
    # Set the background to be transparent
    plt.gcf().set_facecolor('none')  # For figure background
    ax.set_facecolor('none')         # For axes background
    
    # Adjust layout
    plt.tight_layout()
    
    # Show the plot
    plt.show()

#%% 
display(temp9)
#%%
last_available_date_2023 = price_DB[price_DB.index.year == 2023].index.max()
for col in temp8.columns:
    pr =  price_DB.loc[last_available_date_2023, col]
    print(pr) 
    # print(temp8[col].values[-1])
    print((temp8[col].values[-1])/pr*100)


