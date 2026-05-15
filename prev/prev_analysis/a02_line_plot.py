#%%
from trader.analysis.drawer import Drawer

#%%
# ----------------------------------------------------------------
# PRICE, PER, PBR plots
# ----------------------------------------------------------------

code = '005930'
qtrs_back = 20  # Define how many quarters back you want to start from

drawer = Drawer(
    figsize = (10, 10), 
    tick_text_size = 15,
    text_size = 20,
)
drawer.quarterly_line_plot(code, qtrs_back, 'price', 'quarterly')
drawer.quarterly_line_plot(code, qtrs_back, 'price', 'average')
drawer.quarterly_line_plot(code, qtrs_back, 'PER', 'quarterly')
drawer.quarterly_line_plot(code, qtrs_back, 'PER', 'average')
drawer.quarterly_line_plot(code, qtrs_back, 'PBR', 'quarterly')
drawer.quarterly_line_plot(code, qtrs_back, 'PBR', 'average')


#%% 
# ----------------------------------------------------------------
# Line plot
# ----------------------------------------------------------------
x = ['11/11', '11/12', '11/13', '11/14', '11/15']
y = [1929, 1928, 1923,1965, 1868]

d = Drawer(
    figsize = (12, 4), 
    tick_text_size = 16,
    text_size = 20,
    )

d.line_plot(x, y, '-o')
# d.line_plot(x1, y1, '-o', x2, y2, type=':^')
