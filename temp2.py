# %% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *
import pandas as pd

# db1 = pd.read_feather('data_collection/data/financial_reports_upto_2023-10-06_part1.feather')
# db2 = pd.read_feather('data_collection/data/financial_reports_upto_2023-10-07_part2.feather')
# db3 = pd.read_feather('data_collection/data/financial_reports_upto_2023-10-07_part3.feather')
# db4 = pd.read_feather('data_collection/data/financial_reports_upto_2023-10-07_part4.feather')
# db5 = pd.read_feather('data_collection/data/financial_reports_upto_2023-10-09_part5.feather')
# db6 = pd.read_feather('data_collection/data/financial_reports_upto_2023-10-09_part6.feather')

# code = '373220'
# path = 'data_collection/plots/'+code+'.png'
# plot_company_financial_summary(db1, code, path)

# %%
# db_ = pd.concat([db1, db2, db3, db4, db5, db6], ignore_index=True)
# display(db_)

# db_.insert(5, 'date_updated', ['2023-10-05']*len(db_.index))

# %% 
# db_.to_feather('data_collection/data/financial_reports_main.feather')

# %%

# %%