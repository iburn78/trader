#%% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from analysis_tools import *
from data_collection.dc05_CompanyHealth import single_company_data_collect

code = '005930'
fh = single_company_data_collect(code, 'CFS')

#%%
# import importlib
# import analysis_tools
# importlib.reload(analysis_tools)
# from analysis_tools import *

# Define how many quarters back you want to start from
qts_back = 10 
output_file = f'plots/plot_PER.png'

fhr = L4_addition(fh, 'net_income')
PER = get_PER_rolling(code, fhr, qts_back)
save_line_plot(PER, 'PER', output_file)


#%% 

qts_back = 10 
output_file = f'plots/plot_PBR.png'
PBR = get_PBR(code, fh, qts_back)
save_line_plot(PBR, 'PBR', output_file)