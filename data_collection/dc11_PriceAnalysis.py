#%%
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *

fr_db = pd.read_feather('data/financial_reports_main.feather')
pr_db = pd.read_feather('data/price_DB.feather')
code = '005930'
path = 'newgraph_temp.png'
plot_company_financial_summary2(fr_db, pr_db, code, path)

