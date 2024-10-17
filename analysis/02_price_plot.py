#%%
from analysis_tools import *
from drawer import Drawer

code = '005930'
# code = '003230' #삼양식품
code = '000660' # 하이닉스
qts_back = 20  # Define how many quarters back you want to start from

pr = get_last_N_quarter_price(code, qts_back)

line_drawer = Drawer(
    figsize = (16, 4), 
    tick_text_size = 15,
    text_size = 20,
    lang = 'E', 
    eng_name = None
)
output_file = f'plots/{code}_price_quarterly.png'
line_drawer.save_line_plot(pr, 'price', 'quarterly', output_file)

output_file = f'plots/{code}_price_average.png'
line_drawer.save_line_plot(pr, 'price', 'average', output_file)
