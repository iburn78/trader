#%% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc05_CompanyHealth import single_company_data_collect
from analysis_tools import *
import pandas as pd

code = '005930'
# fh = single_company_data_collect(code, 'CFS')
# fh.to_feather('data/temp.feather')
fh = pd.read_feather('data/temp.feather')

#%%
import importlib
import analysis_tools
importlib.reload(analysis_tools)
from analysis_tools import *

# Define how many quarters back you want to start from
qts_back = 10

fhr = L4_addition(fh, 'net_income')
PER = get_PER_rolling(code, fhr, qts_back)

PER_Drawer = Drawer()
output_file = f'plots/plot_PER1.png'
PER_Drawer.save_line_plot(PER, 'PER', 'quarterly', output_file)

output_file = f'plots/plot_PER2.png'
PER_Drawer.save_line_plot(PER, 'PER', 'average', output_file)


#%% 
PBR = get_PBR(code, fh, qts_back)

PBR_Drawer = Drawer()
output_file = f'plots/plot_PBR1.png'
PBR_Drawer.save_line_plot(PBR, 'PBR', 'quarterly', output_file)

output_file = f'plots/plot_PBR2.png'
PBR_Drawer.save_line_plot(PBR, 'PBR', 'average', output_file)