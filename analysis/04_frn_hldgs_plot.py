#%% 
from analysis_tools import *

broker = Broker()
fhd = Drawer()
code = '005930'
period = 'M'
output_file = f'plots/{code}_corr_{period}.png'
fh, cr = broker.fetch_foreign_holdings(code, period)
fhd.plot_fholdings(fh, cr, period, output_file)

num_to_plot = 20
figsize = (12,10)
period = 'D' 
output_file = 'plots/plot_corr_comparison.png'
fhd.corr_comparison_plot(broker, code, period, figsize, num_to_plot, output_file)
