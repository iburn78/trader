#%%
from trader.tools.tools import *

listed = get_listed()
cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
price_db_file = os.path.join(cd_, 'data/price_DB.feather')
output_fig_file = os.path.join(cd_, 'plots/rate_changes.png')

pr_changes, cur_day = get_pr_changes(price_db_file)
listed = pd.merge(listed, pr_changes, on='Code', how='left')

category_mean = listed.groupby('Category')[['last_day', 'last_week', 'last_month', 'last_quarter', 'last_year']].mean()

def _weighted_avg(df, rate):
    weights = df['SharesOuts']*df['cur_price']/10**8
    values = df[rate]
    return (weights*values).sum()/weights.sum()

for p in ['last_day', 'last_week', 'last_month', 'last_quarter', 'last_year']:
    wg = listed.groupby('Category', group_keys=False).apply(_weighted_avg, rate=p, include_groups=False)
    wg.name = 'wg_'+p
    category_mean = pd.merge(category_mean, wg, on='Category', how='left')

set_KoreanFonts()

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

f.savefig(output_fig_file)
plt.close('all')
