#%% 
# -------------------------------------------------------
# Foreign Ownership plots
# -------------------------------------------------------

from drawer import Drawer
from broker import Broker

code = '005930'
broker = Broker()
fod = Drawer(
    figsize = (10,10),  
    tick_text_size = 12,
    text_size = 15,
    lang = 'E', 
    # eng_name = 'Samsung Electronics'
)

period = 'W'
fo, cr = broker.fetch_foreign_ownership(code, period)
fod.plot_fownership(fo, cr, period) 

#%% 
period = 'D' 
num_to_plot = 40
fod.corr_comparison_plot(broker, code, period, num_to_plot)



