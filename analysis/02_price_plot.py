#%%
from analysis_tools import *
from drawer import Drawer

code = '005930'
# code = '003230' #삼양식품
code = '000660' # 하이닉스
code = '207940' #삼성바이오로직스
# code = '005380' #현대차 
# code = '373220' # LG에너지솔루션
qts_back = 4  # Define how many quarters back you want to start from

pr = get_last_N_quarter_price(code, qts_back)

line_drawer = Drawer(
    spine_color='black', 
    label_text_color='black',
    figsize = (7, 7), 
    tick_text_size = 15,
    text_size = 20,
    lang = 'E', 
    eng_name = None
)
output_file = f'plots/{code}_price_quarterly.png'
line_drawer.save_line_plot(pr, 'price', 'quarterly', output_file)

output_file = f'plots/{code}_price_average.png'
line_drawer.save_line_plot(pr, 'price', 'average', output_file)
