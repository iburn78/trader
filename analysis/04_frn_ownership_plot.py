#%% 
from analysis_tools import *
from drawer import Drawer
from broker import Broker

broker = Broker()
fod = Drawer(
    figsize = (12,9), 
    tick_text_size = 15,
    text_size = 20,
    lang = 'K', 
    eng_name = 'Samyang Foods'
)
code = '005930'
code = '003230' #삼양식품
period = 'D'
output_file = f'plots/{code}_corr_{period}.png'
fo, cr = broker.fetch_foreign_ownership(code, period)
fod.plot_fownership(fo, cr, period, output_file)

#%% 
num_to_plot = 20
figsize = (10,9)
period = 'D' 
output_file = 'plots/plot_corr_comparison.png'
fod.corr_comparison_plot(broker, code, period, figsize, num_to_plot, False, output_file)

