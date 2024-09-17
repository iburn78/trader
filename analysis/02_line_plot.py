#%%
from analysis_tools import *

code = '005930'
qts_back = 6  # Define how many quarters back you want to start from

pr = get_last_N_quarter_price(code, qts_back)

output_file = f'plots/plot_price1.png'
save_line_plot(pr, 'price', 'quarterly', output_file)

output_file = f'plots/plot_price2.png'
save_line_plot(pr, 'price', 'average', output_file)
