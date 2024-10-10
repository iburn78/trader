#%%
from analysis_tools import *
from drawer import Drawer

code = '005930'
qts_back = 32  # Define how many quarters back you want to start from

pr = get_last_N_quarter_price(code, qts_back)

line_drawer = Drawer(
    figsize = (20, 9), 
    tick_text_size = 15,
    text_size = 20,
    lang = 'E', 
    eng_name = None
)
output_file = f'plots/{code}_price_quarterly.png'
line_drawer.save_line_plot(pr, 'price', 'quarterly', output_file)

output_file = f'plots/{code}_price_average.png'
line_drawer.save_line_plot(pr, 'price', 'average', output_file)
