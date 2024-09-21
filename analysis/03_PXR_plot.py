#%% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc05_CompanyHealth import single_company_data_collect
from analysis_tools import *

code = '005930'
kwargs = {'code': code, 'fs_div': 'CFS'}
data_file = f'data/finhealth_{code}.feather'
fh = read_or_regen(data_file, single_company_data_collect, **kwargs)

# Define how many quarters back you want to start from
qts_back = 10

fhr = L4_addition(fh, 'net_income') # last 4 quarters data addition, i.e., quarterly rolling
PER = get_PER_rolling(code, fhr, qts_back)

PER_Drawer = Drawer()
output_file = f'plots/{code}_PER_quarterly.png'
PER_Drawer.save_line_plot(PER, 'PER', 'quarterly', output_file)

output_file = f'plots/{code}_PER_average.png'
PER_Drawer.save_line_plot(PER, 'PER', 'average', output_file)

PBR = get_PBR(code, fh, qts_back)

PBR_Drawer = Drawer()
output_file = f'plots/{code}_PBR_quarterly.png'
PBR_Drawer.save_line_plot(PBR, 'PBR', 'quarterly', output_file)

output_file = f'plots/{code}_PBR_average.png'
PBR_Drawer.save_line_plot(PBR, 'PBR', 'average', output_file)