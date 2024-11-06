#%%
from analysis_tools import *
from drawer import Drawer

#%%
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

#%% 
y_close = fdr.StockListing('KRX', '20241101')
display(y_close)
t_close = fdr.StockListing('KRX')
display(t_close)

#%% 
y_close_KOSPI = y_close.loc[y_close['Market']=='KOSPI']
t_close_KOSPI = t_close.loc[t_close['Market']=='KOSPI']

y_close_KOSDAQ = y_close.loc[y_close['Market']=='KOSDAQ']
t_close_KOSDAQ = t_close.loc[t_close['Market']=='KOSDAQ']

res_KOSPI = t_close_KOSPI.merge(y_close_KOSPI[['Code', 'Close', 'Volume', 'Marcap']], on='Code', how='inner', suffixes=('_t', '_y'))
res_KOSPI = res_KOSPI[['Code', 'Marcap_y', 'Marcap_t', 'Close_y', 'Close_t', 'Volume_y', 'Volume_t']]
res_KOSDAQ = t_close_KOSDAQ.merge(y_close_KOSDAQ[['Code', 'Close', 'Volume', 'Marcap']], on='Code', how='inner', suffixes=('_t', '_y'))
res_KOSDAQ = res_KOSDAQ[['Code', 'Marcap_y', 'Marcap_t', 'Close_y', 'Close_t', 'Volume_y', 'Volume_t']]
res_KOSPI = res_KOSPI.sort_values(by='Marcap_y', ascending=False).reset_index(drop=True)
res_KOSDAQ = res_KOSDAQ.sort_values(by='Marcap_y', ascending=False).reset_index(drop=True)
print(len(res_KOSPI))
print(len(res_KOSDAQ))

#%% 

res_KOSPI['Group'] = res_KOSPI.index // 50
res_KOSDAQ['Group'] = res_KOSDAQ.index // 100

res_KOSPI_MC = res_KOSPI.groupby('Group').apply(
    lambda group: (group['Marcap_t'].sum()-group['Marcap_y'].sum())/group['Marcap_y'].sum()*100
).reset_index(name='Measure')
res_KOSPI_MC.columns=['Group', 'Measure']

res_KOSDAQ_MC = res_KOSDAQ.groupby('Group').apply(
    lambda group: (group['Marcap_t'].sum()-group['Marcap_y'].sum())/group['Marcap_y'].sum()*100
).reset_index(name='Measure')
res_KOSDAQ_MC.columns=['Group', 'Measure']

res_KOSPI_V = res_KOSPI.groupby('Group').apply(
    lambda group: (group['Volume_t'].sum()-group['Volume_y'].sum())/group['Volume_y'].sum()*100
).reset_index(name='Measure')
res_KOSPI_V.columns=['Group', 'Measure']

res_KOSDAQ_V = res_KOSDAQ.groupby('Group').apply(
    lambda group: (group['Volume_t'].sum()-group['Volume_y'].sum())/group['Volume_y'].sum()*100
).reset_index(name='Measure')
res_KOSDAQ_V.columns=['Group', 'Measure']
#%% 
res = res_KOSPI_MC
# res = res_KOSDAQ_MC
# res = res_KOSPI_V
# res = res_KOSDAQ_V

bar_drawer = Drawer(
    figsize = (6, 10), 
    tick_text_size = 10,
    text_size = 20,
    lang = 'E',
    )

bar_drawer.free_plot()
x = []
for i in range(len(res)): 
    x.append(f'Group {i+1}')
x.reverse()
print(x)
bars = bar_drawer.ax.barh(x, res['Measure'].iloc[::-1])
bars[-1].set_color('orange')
bars[-2].set_color('orange')
bars[-3].set_color('orange')