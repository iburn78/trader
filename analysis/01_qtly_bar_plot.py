#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc05_CompanyHealth import single_company_data_collect
from tools.tools import set_KoreaFonts
from analysis_tools import *
import matplotlib.pyplot as plt
import pandas as pd

code = '005930'
# fh = single_company_data_collect(code, 'CFS')
fh = pd.read_feather('data/temp.feather')

#%%
import importlib
import analysis_tools
importlib.reload(analysis_tools)
from analysis_tools import *

target_account = 'revenue'
num_qts = 6
unit = 1000 
unit_base = 8 
increment_FT= (4, 0) # from ith before to jth before 
lim_scale_factor = 0.7  # determine axis starting point
output_file = f'plots/plot_{target_account[:4]}.png'

bar_drawer = Drawer(
    figsize = (16, 9), 
    tick_text_size = 20,
    text_size = 20,
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