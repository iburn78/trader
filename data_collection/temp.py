#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *

price_db_file = 'data/price_DB.feather'
price_DB = pd.read_feather(price_db_file)

code = '005930'
path = 'plots/gen_{}.png'.format(code)

plot_last_quarter_prices(price_DB, code, path)