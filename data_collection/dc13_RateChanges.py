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

category_mean = listed.groupby('Category')[['last_day', 'last_week', 'last_month', 'last_quarter', 'last_year']].mean()

def _weighted_avg(df, rate):
    weights = df['SharesOuts']*df['cur_price']/10**8
    values = df[rate]
    return (weights*values).sum()/weights.sum()

for p in ['last_day', 'last_week', 'last_month', 'last_quarter', 'last_year']:
    wg = listed.groupby('Category').apply(_weighted_avg, rate = p)
    wg.name = 'wg_'+p
    category_mean = pd.merge(category_mean, wg, on='Category', how='left')

import matplotlib.pyplot as plt
import seaborn as sns
plt.rcParams['font.family'] = 'Arial Unicode MS'

f, ax = plt.subplots(2, 1, figsize=(10, 12), constrained_layout=True, gridspec_kw={'height_ratios': [1, 1]})

target_db = category_mean.iloc[:, 0:5]*100  
target_db = target_db.rename(columns={n: n[5:] for n in target_db.columns})

sns.heatmap(target_db, ax = ax[0], vmin=-9, vmax=9, cmap='Blues', annot=True)
ax[0].set_title('분야별 평균 주가변동폭 (%, '+cur_day.strftime('%Y-%m-%d')+')')
ax[0].set_xlabel('')
ax[0].set_ylabel('')

target_db = category_mean.iloc[:, 5:]*100  
target_db = target_db.rename(columns={n: n[8:] for n in target_db.columns})

sns.heatmap(target_db, ax = ax[1], vmin=-9, vmax=9, cmap='Reds', annot=True)
ax[1].set_title('분야별 시총 가중평균 주가변동폭 (%, '+cur_day.strftime('%Y-%m-%d')+')')
ax[1].set_xlabel('')
ax[1].set_ylabel('')

f.savefig('plots/rate_changes.png')
plt.close('all')
