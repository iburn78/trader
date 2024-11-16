#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc05_CompanyHealth import single_company_data_collect
from analysis_tools import *
from drawer import Drawer
#%% 
# code = '005930'
# code = '000660' # 하이닉스
# code = '003230' #삼양식품
# code = '207940' #삼성바이오로직스
code = '005380' #현대차 
# code = '373220' # LG에너지솔루션

# kwargs = {'code': code, 'fs_div': 'CFS'}
# data_file = f'data/finhealth_{code}.feather'
# fh = read_or_regen(data_file, single_company_data_collect, **kwargs)

fr_main_path = '../data_collection/data/financial_reports_main.feather'
fr_main = pd.read_feather(fr_main_path)
fh = fr_main.loc[(fr_main['code']==code) & (fr_main['fs_div']=='CFS')].dropna(axis=1, how='all')  # main_DB might have all na columns

# Samsung 
# rev = fh.loc[fh['account']=='revenue', '2024_2Q']*1.0666
# opi = fh.loc[fh['account']=='operating_income', '2024_2Q']*(1-0.1284)
# # ni = fh.loc[fh['account']=='net_income', '2024_2Q']*(1-0.1284)  # approx
# fh.loc[fh['account'] == 'revenue', '2024_3Q'] = rev
# fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = opi
# # fh.loc[fh['account'] == 'net_income', '2024_3Q'] = ni

# Samsung biologics
# fh.loc[fh['account'] == 'revenue', '2024_3Q'] = 11871*(10**8)
# fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = 3386*(10**8)
# fh.loc[fh['account'] == 'net_income', '2024_3Q'] = 2645*(10**8)

# Hynix
# fh.loc[fh['account'] == 'revenue', '2024_3Q'] = 175731*(10**8)
# fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = 70300*(10**8)

# Hyundai Motors
# fh.loc[fh['account'] == 'revenue', '2024_3Q'] = 429283*(10**8)
# fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = 35809*(10**8)

# LG 에너지 솔루션
# fh.loc[fh['account'] == 'revenue', '2024_3Q'] = 68778*(10**8)
# fh.loc[fh['account'] == 'operating_income', '2024_3Q'] = 4483*(10**8)

#%% 
target_account = 'revenue'
target_account = 'operating_income'
# target_account = 'net_income'
num_qts = 5
unit = 1
unit_base = 9 
increment_FT= (0, 0) # from ith before to jth before 
lim_scale_factor = 0.7 # determine axis starting point
figure_num = 1
output_file = f'plots/{code}_fh_{target_account[:6]}_{fig_num(figure_num)}.png'

bar_drawer = Drawer(
    spine_color='black', 
    label_text_color='black',
    figsize = (10, 10), 
    tick_text_size = 20,
    text_size = 20,
    lang = 'E',
    )

bar_drawer.save_bar_plot(
    fh, target_account, 
    num_qts, 
    unit, 
    unit_base, 
    increment_FT, 
    lim_scale_factor, 
    output_file, 
    # bar_highlights=[2, 6, 10, 14, 18], 
    # bar_highlights_gray=[1]
    )

#%% 

x = [2019, 2020, 2021, 2022, 2023, 2024]
y = [114, 166, 227, 280, 444, 399]
bar_drawer = Drawer(
    figsize = (10, 6), 
    tick_text_size = 20,
    text_size = 20,
    lang = 'E',
    )

bar_drawer.bar_plot(
    x, y, 
    bar_highlights=[1],
    # bar_highlights_gray=[1]
)




# %%

qtrs = [
    "24.Q3", 
    "24.Q2",
    "24.Q1",
    "23.Q4",
    "23.Q3",
    "23.Q2",
    "23.Q1",
    "22.Q4",
    "22.Q3",
    "22.Q2",
]
# google
revenue = [
    87863,
    84275,
    79972,
    85503,
    76397,
    74316,
    69415,
    75153,
    68245,
    69117,
]
operating_profit = [
    32803,
    30846,
    28797,
    27594,
    24203,
    23849,
    21928,
    20036,
    18443,
    21031,
]

revenue = [r / 1000 for r in revenue] # in billions
operating_profit = [ r / 1000 for r in operating_profit ] # in billions

qtrs.reverse()
revenue.reverse()
operating_profit.reverse()
rate = [(a / b)*100 for a, b in zip(operating_profit, revenue)]

bar_drawer = Drawer(
    figsize = (10, 3), 
    tick_text_size = 12,
    text_size = 20,
    lang = 'E',
    )

bar_drawer.bar_plot(qtrs, rate, bar_highlights_red=[1])


#%% 
d1 = [-4.01, -3.23, -2.30, -2.28, -1.98, -1.90]
d2 = [-3497, -421, -168, -109, -105, -97]
d3 = [230, 580]

bar_drawer = Drawer(
    figsize = (4, 4), 
    tick_text_size = 16,
    text_size = 20,
    lang = 'E',
    )

x = range(len(d1))
# y = d1
x = ['KOSDAQ', 'KOSPI']
y = [580, 230]
bar_drawer.free_plot()
bars = bar_drawer.ax.barh(x, y)
for index, value in enumerate(y):
    bar_drawer.ax.text(value, index, " "+str(round(value,2)), va='center', fontsize=12, fontdict={'color':'white'})
bars[-1].set_color('red')
bars[-2].set_color('red')
# bars[-3].set_color('orange')
# bars[-4].set_color('orange')
# bars[-5].set_color('gray')
# bars[-6].set_color('gray')

#%% 

x = ['11/11', '11/12', '11/13', '11/14', '11/15']
nd = [19298.76, 19281.40, 19230.72,	19107.65, 18680.12]
kp = [2531.66, 2482.57, 2417.08, 2418.86, 2416.86]
usd_krw = [1396.00, 1406.00, 1407.00, 1408.50, 1401.30]

bar_drawer = Drawer(
    figsize = (12, 4), 
    tick_text_size = 16,
    text_size = 20,
    lang = 'E',
    )
y = nd
# y = kp
ymax = max(max(y)*1.0, max(y)*0.98)
ymin = min(min(y)*1.0, min(y)*0.98)
bar_drawer.free_plot()
bars = bar_drawer.ax.bar(x, y)
bar_drawer.ax.set_ylim(ymin, ymax)  
bars[-1].set_color('orange')
bars[-2].set_color('orange')
#%% 
bar_drawer = Drawer(
    figsize = (12, 4), 
    tick_text_size = 16,
    text_size = 20,
    lang = 'E',
    )
y = usd_krw
ymax = max(max(y)*1.01, max(y)*0.99)
ymin = min(min(y)*1.01, min(y)*0.99)
bar_drawer.free_plot()
bars = bar_drawer.ax.plot(x, y, '-o')
bar_drawer.ax.set_ylim(ymin, ymax)  