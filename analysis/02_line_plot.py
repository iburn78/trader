#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from analysis_tools import *

code = '005930'
qts_back = 6  # Define how many quarters back you want to start from
output_file = f'plots/plot_price.png'

pr = get_last_N_quarter_price(code, qts_back)
save_line_plot(pr, 'price', output_file)
