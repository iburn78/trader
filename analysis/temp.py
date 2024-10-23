#%% 
from analysis_tools import *
from drawer import *

drawer = Drawer(
    figsize = (16, 9), 
    tick_text_size = 15,
    text_size = 20,
)

# x = ['2020', '2021', '2022', '2023', '2024.10']
# y = [1.94, 1.16, 1.78, 3.5, 4.36]
# drawer.bar_plot(x,y)
# plt.show()

code = '207940' #삼성바이오로직스
qts_back = 10  # Define how many quarters back you want to start from
pr = get_last_N_quarter_price(code, qts_back)

x = pr.index
y = pr.values

# drawer.line_animate(x,y, speed=2, output_file='plots/ani.mp4')
drawer.double_line_animate(x,y, x, y/2, speed=1, output_file='plots/ani_long.mp4')