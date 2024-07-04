#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *
import pandas as pd

price_db_file = 'data/price_DB.feather'
pr_db = pd.read_feather(price_db_file)

def _calc_change(cur_date, prev_date):
    cp = pr_db.loc[pr_db.index >= cur_date].iloc[0]
    pp = pr_db.loc[pr_db.index >= prev_date].iloc[0]
    return cp/pp - 1

pr_changes = pd.DataFrame(columns = pr_db.columns)

cur_day = pr_db.index[-1]
last_day = pr_db.index[-2]
last_week = last_day - pd.Timedelta(weeks=1)
last_month = last_day - pd.DateOffset(months=1)
last_quarter = last_day - pd.DateOffset(months=3)
last_year = last_day - pd.DateOffset(months=12)
pr_changes.loc['cur_price'] = pr_db.iloc[-1]
pr_changes.loc['last_day'] = _calc_change(cur_day, last_day)
pr_changes.loc['last_week'] = _calc_change(cur_day, last_week)
pr_changes.loc['last_month'] = _calc_change(cur_day, last_month)
pr_changes.loc['last_quarter'] = _calc_change(cur_day, last_quarter)
pr_changes.loc['last_year'] = _calc_change(cur_day, last_year)

pr_changes = pr_changes.transpose()
pr_changes.index.name = 'Code'

listed = get_listed()
listed = pd.merge(listed, pr_changes, on='Code', how='left')

#%% 
category_mean = listed.groupby('Category')[['last_day', 'last_week', 'last_month', 'last_quarter', 'last_year']].mean()

def _weighted_avg(df, rate):
    weights = df['SharesOuts']*df['cur_price']/10**8
    values = df[rate]
    return (weights*values).sum()/weights.sum()

for p in ['last_day', 'last_week', 'last_month', 'last_quarter', 'last_year']:
    wg = listed.groupby('Category').apply(_weighted_avg, rate = p)
    wg.name = 'wg_'+p
    category_mean = pd.merge(category_mean, wg, on='Category', how='left')

#%%
display(category_mean)
