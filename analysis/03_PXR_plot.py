#%% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc05_CompanyHealth import single_company_data_collect
from analysis_tools import *
from drawer import Drawer

# code = '005930'
# code = '003230' #삼양식품
# code = '000660' # 하이닉스
code = '207940' #삼성바이오로직스
# code = '005380' #현대차 
kwargs = {'code': code, 'fs_div': 'CFS'}
data_file = f'data/finhealth_{code}.feather'
fh = read_or_regen(data_file, single_company_data_collect, **kwargs)

# Samsung
# rev = fh.loc[fh['account']=='revenue', '2024_2Q']*1.0666
# opi = fh.loc[fh['account']=='operating_income', '2024_2Q']*(1-0.1284)
# ni = fh.loc[fh['account']=='net_income', '2024_2Q']*(1-0.1284)  # approx
# fh.loc[fh['account'] == 'revenue', '2024_3Q'] = rev
# fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = opi
# fh.loc[fh['account'] == 'net_income', '2024_3Q'] = ni
# fh.loc[fh['account'] == 'equity', '2024_3Q'] = fh.loc[fh['account'] == 'equity', '2024_2Q']

# Hyundai Motors
# fh.loc[fh['account'] == 'revenue', '2024_3Q'] = 429283*10^8
# fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = 35809*10^8

# Samsung biologics
# fh.loc[fh['account'] == 'revenue', '2024_3Q'] = 11871*(10**8)
# fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = 3386*(10**8)
# fh.loc[fh['account'] == 'net_income', '2024_3Q'] = 2645*(10**8)

# Define how many quarters back you want to start from
qts_back = 4

fhr = L4_addition(fh, 'net_income') # last 4 quarters data addition, i.e., quarterly rolling
PER = get_PER_rolling(code, fhr, qts_back)
# fhr = L4_addition(fh, 'operating_income') # last 4 quarters data addition, i.e., quarterly rolling
# PER = get_PER_rolling(code, fhr, qts_back, target_account='operating_income')*2

PER_Drawer = Drawer(
    spine_color='black', 
    label_text_color='black',
    figsize = (6, 6), 
    tick_text_size = 15,
    text_size = 20,
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