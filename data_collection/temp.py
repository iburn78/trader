
#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *
import pandas as pd

main_db_file = 'data/financial_reports_main.feather'
main_db = pd.read_feather(main_db_file)

price_db_file = 'data/price_DB.feather'
price_DB = pd.read_feather(price_db_file)
code = '005930'
path = None
plot_company_financial_summary(main_db, code, path)
