#%% 
from analysis_tools import *
from drawer import *

a = Drawer(
    figsize = (6, 5), 
    tick_text_size = 15,
    text_size = 20,
    lang = 'E'
)

a.free_plot()
x = ['2020', '2021', '2022', '2023', '2024.10']
y = [1.94, 1.16, 1.78, 3.5, 4.36]
bars = a.ax.bar(x, y)
bars[-1].set_color('orange')
for bar in bars:
    yval = bar.get_height()
    if yval < 100:
        yval = round(yval, 1)
    else:
        yval = int(yval)
    a.ax.text(bar.get_x() + bar.get_width()/2, yval, f'{format(yval, ",")}', ha='center', va='bottom', fontsize = a.tick_text_size )
plt.show()
