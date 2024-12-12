#%% 
###########################################
###########################################
###########################################
###########################################
###########################################
###########################################
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc05_CompanyHealth import single_company_data_collect
from analysis_tools import *
from drawer import Drawer

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

code = '005930'
# code = '003230' #삼양식품
kwargs = {'code': code, 'fs_div': 'CFS'}
data_file = f'data/finhealth_{code}.feather'
fh = read_or_regen(data_file, single_company_data_collect, **kwargs)

rev = fh.loc[fh['account']=='revenue', '2024_2Q']*1.0666
opi = fh.loc[fh['account']=='operating_income', '2024_2Q']*(1-0.1284)
ni = fh.loc[fh['account']=='net_income', '2024_2Q']*(1-0.1284)  # approx
fh.loc[fh['account'] == 'revenue', '2024_3Q'] = rev
fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = opi
fh.loc[fh['account'] == 'net_income', '2024_3Q'] = ni
fh.loc[fh['account'] == 'equity', '2024_3Q'] = fh.loc[fh['account'] == 'equity', '2024_2Q']

# Define how many quarters back you want to start from
qts_back = 16

fhr = L4_addition(fh, 'net_income') # last 4 quarters data addition, i.e., quarterly rolling
PER = get_PER_rolling(code, fhr, qts_back)

PER_Drawer = Drawer(
    figsize = (7, 9), 
    tick_text_size = 20,
    text_size = 25,
    lang = 'E'
)
output_file = f'plots/{code}_PER_quarterly.png'
PER_Drawer.save_line_plot(PER, 'PER', 'quarterly', output_file)

output_file = f'plots/{code}_PER_average.png'
PER_Drawer.save_line_plot(PER, 'PER', 'average', output_file)

#%% 

qts_back = 8
PBR = get_PBR(code, fh, qts_back)

PBR_Drawer = Drawer(
    figsize = (16, 9), 
    tick_text_size = 15,
    text_size = 20,
    lang = 'E'
)
output_file = f'plots/{code}_PBR_quarterly.png'
PBR_Drawer.save_line_plot(PBR, 'PBR', 'quarterly', output_file)

output_file = f'plots/{code}_PBR_average.png'
PBR_Drawer.save_line_plot(PBR, 'PBR', 'average', output_file)