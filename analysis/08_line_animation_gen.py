#%% 
from analysis_tools import *
from drawer import *

drawer = Drawer(
    figsize = (16, 16), 
    tick_text_size = 20,
    text_size = 20,
)

# x = ['2020', '2021', '2022', '2023', '2024.10']
# y = [1.94, 1.16, 1.78, 3.5, 4.36]
# drawer.bar_plot(x,y)
# plt.show()

code1 = '373220' #LG에너지솔루션 - yellow
code2 = '006400' #삼성 SDI - red 
code3 = '096770' #SK 이노베이션 - orange

# qts_back = 12  # Define how many quarters back you want to start from
start_date = '2022-01-27'
pr1 = get_last_N_quarter_price(code1, qts_back= None, start_date=start_date)
pr2 = get_last_N_quarter_price(code2, qts_back= None, start_date=start_date)
pr3 = get_last_N_quarter_price(code3, qts_back= None, start_date=start_date)

x1 = pr1.index
y1 = pr1.values
y1 = y1/y1[0]*100
x2 = pr2.index
y2 = pr2.values
y2 = y2/y2[0]*100
x3 = pr3.index
y3 = pr3.values
y3 = y3/y3[0]*100
# drawer.line_animate(x,y, speed=2, output_file='plots/ani.mp4')
# drawer.double_line_animate(x,y, x, y/2, speed=1, output_file='plots/ani_long.mp4')
drawer.triple_line_animate(x1 ,y1, x2, y2, x3, y3, speed=2, output_file='plots/ani.mp4')
print(x1)
print(x2) 
print(x3) 