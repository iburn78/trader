#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc05_CompanyHealth import single_company_data_collect
from analysis_tools import *
from drawer import Drawer

# code = '005930'
code = '000660' # 하이닉스
# code = '003230' #삼양식품
code = '207940' #삼성바이오로직스

kwargs = {'code': code, 'fs_div': 'CFS'}
data_file = f'data/finhealth_{code}.feather'
fh = read_or_regen(data_file, single_company_data_collect, **kwargs)

# fr_main_path = '../data_collection/data/financial_reports_main.feather'
# fr_main = pd.read_feather(fr_main_path)
# fh = fr_main.loc[(fr_main['code']==code) & (fr_main['fs_div']=='CFS')].dropna(axis=1, how='all')  # main_DB might have all na columns


# adjustment part for Samsung 
# rev = fh.loc[fh['account']=='revenue', '2024_2Q']*1.0666
# opi = fh.loc[fh['account']=='operating_income', '2024_2Q']*(1-0.1284)
# # ni = fh.loc[fh['account']=='net_income', '2024_2Q']*(1-0.1284)  # approx
# fh.loc[fh['account'] == 'revenue', '2024_3Q'] = rev
# fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = opi
# # fh.loc[fh['account'] == 'net_income', '2024_3Q'] = ni

#%% 
target_account = 'revenue'
# target_account = 'operating_income'
target_account = 'net_income'
num_qts = 17
unit = 1
unit_base = 9 
increment_FT= (0, 0) # from ith before to jth before 
lim_scale_factor = 0.7 # determine axis starting point
figure_num = 1
output_file = f'plots/{code}_fh_{target_account[:6]}_{fig_num(figure_num)}.png'

bar_drawer = Drawer(
    figsize = (12, 9), 
    tick_text_size = 12,
    text_size = 20,
    lang = 'E',
    # eng_name = ""
    )

bar_drawer.save_bar_plot(
    fh, target_account, 
    num_qts, 
    unit, 
    unit_base, 
    increment_FT, 
    lim_scale_factor, 
    output_file, 
    # bar_highlights=[2, 6, 10, 14, 18], 
    # bar_highlights_gray=[1]
    )
# %%
