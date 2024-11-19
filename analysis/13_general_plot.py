#%%
from drawer import Drawer
import matplotlib.pyplot as plt

dr = Drawer(
    figsize=(12,10), 
    lang='E', 
)
dr.free_plot()

x = ['11/11', '11/12', '11/13', '11/14', '11/15']
nd = [19298.76, 19281.40, 19230.72,	19107.65, 18680.12]
#%% 
dr.fig.show()