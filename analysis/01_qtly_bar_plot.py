#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc05_CompanyHealth import single_company_data_collect
from analysis_tools import *
from drawer import Drawer

code = '005930'
kwargs = {'code': code, 'fs_div': 'CFS'}
data_file = f'data/finhealth_{code}.feather'
fh = read_or_regen(data_file, single_company_data_collect, **kwargs)

#%% 
# adjustment part 
# rev = fh.loc[fh['account']=='revenue', '2024_2Q']*1.0666
# opi = fh.loc[fh['account']=='operating_income', '2024_2Q']*(1-0.1284)
# fh.loc[fh['account'] == 'revenue', '2024_3Q'] = rev
# fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = opi

#%% 
target_account = 'revenue'
target_account = 'operating_income'
num_qts = 10
unit = 10
unit_base = 8 
increment_FT= (0, 0) # from ith before to jth before 
lim_scale_factor = 0.7  # determine axis starting point
figure_num = 4
output_file = f'plots/{code}_fh_{target_account[:6]}_{fig_num(figure_num)}.png'

bar_drawer = Drawer(
    figsize = (16, 9), 
    tick_text_size = 15,
    text_size = 20,
    lang = 'E',
    eng_name = "Samsung Electronics"
    )

bar_drawer.save_bar_plot(
    fh, target_account, 
    num_qts, 
    unit, 
    unit_base, 
    increment_FT, 
    lim_scale_factor, 
    output_file
    )