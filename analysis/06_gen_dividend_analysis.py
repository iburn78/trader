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

#%% 

# display(fr_main)
# display(df_krx)
# display(price_DB)
# display(volume_DB)
# display(outshare_DB)
# display(div_DB)

#%% 
from analysis_tools import *

def get_modifier_div(broker, code): 
    face_val_from_div = get_div_single_company(broker, code)['face_val'][0]
    latest_face_val = get_latest_face_value(broker, code)
    try:  
        modifier = float(latest_face_val)/float(face_val_from_div)
    except: 
        modifier = 0
    return modifier 

year = 2021
threshold = 8.5
broker = gen_broker()

temp = {}
temp['div'] = div_DB.loc[year]
temp['price'] = price_DB.loc[price_DB.index[price_DB.index.year == year].max()]
temp['rate'] = temp['div']/temp['price']*100
div_year = pd.DataFrame(temp).sort_values(by = 'rate', ascending=False)
div_year = div_year.loc[div_year['rate']>threshold]

div_year['modifier'] = div_year.index.map(lambda x: get_modifier_div(broker, x))
div_year['new_rate'] = div_year['rate']*div_year['modifier']
div_year = pd.DataFrame(div_year).sort_values(by = 'new_rate', ascending=False)
div_year = div_year.loc[div_year['new_rate']>threshold]
div_year['name'] = div_year.index.map(lambda x: df_krx.loc[x]['Name'])

display(div_year)


import seaborn as sns
import matplotlib.pyplot as plt
from tools.tools import set_KoreanFonts

set_KoreanFonts()

plt.figure(figsize=(8, 8))
    
# Create the barplot
sns.barplot(y=div_year['name'], x=div_year['new_rate'], palette='viridis')
    
# Add labels with white text color and set fontsize to 20 (adjustable)
plt.ylabel('Top Companies', color='white', fontsize=12)
plt.xlabel(f'Dividend/Stock Price(%, {year})', color='white', fontsize=12)  # Adjust if there's an index name, or use '' for no label
    
# Remove the top and right spines (axes)
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
    
# Set the bottom and left spines (axes) to white
ax.spines['bottom'].set_color('white')
ax.spines['left'].set_color('white')
    
# Set tick parameters to make them white and adjust the font size
ax.tick_params(colors='white', labelsize=15)  # Adjust tick label size here
    
# Set the background to be transparent
plt.gcf().set_facecolor('none')  # For figure background
ax.set_facecolor('none')         # For axes background
    
# Adjust layout
plt.tight_layout()
    
# Show the plot
plt.show()


#%% 
div_DB['100840']