#%%
from trader.analysis.drawer import Drawer

# ----------------------------------------------------------------
# Quarterly Bar Plot
# ----------------------------------------------------------------

code = '005930'
code = '068270'

target_account = 'revenue'
# target_account = 'operating_income'
# target_account = 'net_income'
num_qts = 5
unit_base = 9 
increment_FT= (4, 0) # from ith before to jth before (0: latest quarter)

drawer = Drawer(
    # spine_color='white', 
    # label_text_color='white',
    spine_color='black', 
    label_text_color='black',
    figsize = (10, 8), 
    text_size = 18,
    tick_text_size = 15,
    )

drawer.quarterly_bar_plot(
    code, target_account, 
    num_qts, 
    unit_base, 
    increment_FT=increment_FT, 
    # highlights=[2, 6, 10, 14, 18], 
    # highlights_gray=[1]
    )

#%% 
# ----------------------------------------------------------------
# General Bar Plot 
# ----------------------------------------------------------------
# if some elements in x are identical, then bar plot overlap. 
# Use different color to make it useful 

x = [2019, 2020, 2021, 2022, 2023, 2024]
y = [114, 166, 227, 280, 444, 333]

drawer = Drawer(
    # spine_color='white', 
    # label_text_color='white',
    figsize = (10, 6), 
    tick_text_size = 14,
    text_size = 14,
    )

drawer.bar_plot(
    x, y, 
    increment_FT=(4,0), 
    highlights=[1],
    # scale=True,
    # scale_factor=0.9, 
    # highlights_gray=[1],
    # highlights_red=[1],
    save=False,
    )


#%% 
# ----------------------------------------------------------------
# Horizontal Bar Plot
# ----------------------------------------------------------------
items = ['a', 'b', 'c', 'd', 'e', 'f']
n_values = [-4.01, -3.23, -2.30, -2.28, -1.98, -1.90]
p_values = [-i for i in n_values]
values = n_values

drawer = Drawer(
    figsize = (7, 7), 
    tick_text_size = 14,
    text_size = 14,
    )
drawer.barh_plot(items, values, 
    increment_FT=(4,0), 
    highlights=[1, 2],
    # scale=True,
    # scale_factor=0.9, 
    display_x_axis=False,
    save=False, 
    )


#%% 
# ----------------------------------------------------------------
# Bar plot using analysis tools
# ----------------------------------------------------------------
from trader.analysis.drawer import Drawer
from trader.analysis.analysis_tools import market_change_analysis, top_movements_in_group
day_from = '20240111'
day_to = '20241213'

res_KOSPI, res_KOSDAQ = market_change_analysis(day_from, day_to)
target_DB = res_KOSPI
ptp, pbp, vtp, vbp = top_movements_in_group(target_DB, select_by_marcap=200)

d = Drawer()
d.barh_plot(ptp['Name'][::-1], ptp['p_increase'][::-1])
d.barh_plot(pbp['Name'], pbp['p_increase'])
d.barh_plot(vtp['Name'][::-1], vtp['v_increase'][::-1])
d.barh_plot(vbp['Name'], vbp['v_increase'])
