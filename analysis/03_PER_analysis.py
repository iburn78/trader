#%% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from analysis_tools import *
from data_collection.dc05_CompanyHealth import single_company_data_collect

code = '005930'
fh = single_company_data_collect(code, 'CFS')

#%%
target_account = 'net_income'
qts_back = 6  # Define how many quarters back you want to start from
output_file = f'plots/plot_PER.png'

fhr = L4_addition(fh, target_account)
PER = get_PER_rolling(code, fhr, qts_back, target_account) # PER should use net_income
save_line_plot(PER, 'PER', output_file)