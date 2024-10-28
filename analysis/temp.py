#%% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc05_CompanyHealth import single_company_data_collect
from analysis_tools import *
from drawer import Drawer


code = '373220' # LG에너지솔루션

kwargs = {'code': code, 'fs_div': 'CFS'}
data_file = f'data/finhealth_{code}.feather'
fh = read_or_regen(data_file, single_company_data_collect, **kwargs)

fh.loc[fh['account'] == 'revenue', '2024_3Q'] = 68778*(10**8)
fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = 4483*(10**8)

target_account = 'revenue'
# target_account = 'operating_income'
increment_FT= (0, 0) # from ith before to jth before 

x = [1, 2]
y = [3, 4]

bar_drawer = Drawer(
    figsize = (12, 10), 
    tick_text_size = 8,
    text_size = 12,
    lang = 'E',
    )

bar_drawer.bar_plot(
    x, y, 
    increment_FT, 
    bar_highlights=[2], 
    bar_highlights_gray=[1]
    )
