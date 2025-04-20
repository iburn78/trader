#%% 
from trader.tools.tools import get_df_krx
from trader.data_collection.dc18_CC_tools import *

cv_threshold_prime = 0.4
cv_threshold = 1.0
criteria_dict = {
    'revenue_growth': [(15,7), 0.3], # percent (yoy), # count (e.g., 0.2 = 20% of quarters: to be multiplied by period)
    'revenue_stats': [np.nan, cv_threshold_prime, 0, np.nan], # size
    'opincome_stats': [np.nan, cv_threshold_prime, 0, np.nan], # size
    'opmargin_stats': [(20,10), cv_threshold_prime, 0, np.nan], # percent
    'nopincome_stats': [np.nan, cv_threshold, np.nan, np.nan], # size
    'asset_stats': [np.nan, cv_threshold, 0, np.nan], # size
    'debt_stats': [np.nan, cv_threshold, np.nan, np.nan], # size
    'equity_stats': [np.nan, cv_threshold, 0, np.nan], # size
    'liquid_asset_ratio_stats': [np.nan, cv_threshold, np.nan, np.nan], # percent
    'liquid_debt_ratio_stats': [np.nan, cv_threshold, np.nan, np.nan], # percent
    'debt_to_equity_ratio_stats': [200, cv_threshold, np.nan, np.nan] # percent
}
score = [5, 2, 2, 5, 1, 1, 1, 1, 1, 1, 1] # weights for each criteria
N = 10 # top to add

def compare_logic(data_dict, criteria_dict, period:str):
    key = list(data_dict.keys())
    if key != list(criteria_dict.keys()):
        raise ValueError("Key mismatch between data_dict and criteria_dict")

    res = [0] * len(data_dict.keys())
    comment = [''] * len(data_dict.keys())

    # revenue growth
    idx = 0
    data = data_dict[key[idx]]
    crit = criteria_dict[key[idx]] 
    p = int(period.replace('Q',''))
    conditions = [
        data[1] <= int(p*crit[1]), 
    ]
    if all(conditions):
        if data[0] >= crit[0][0]:
            res[idx] = score[idx]
        elif data[0] >= crit[0][1]:
            res[idx] = round(score[idx]*(data[0]-crit[0][1])/(crit[0][0]-crit[0][1]), 1)
        else:
            res[idx] = 0
    if data[1] == 0:
        comment[idx] += 'N' # No negative growth'

    # revenue stats, opincome stats, asset stats, equity stats
    for idx in [1, 2, 5, 7]: 
        data = data_dict[key[idx]]
        crit = criteria_dict[key[idx]] 
        conditions = [
            data[1] <= crit[1], # cv
            data[2] >= crit[2], # slope
        ]
        if all(conditions):
            res[idx] = score[idx]
        if data[3] >= 0:
            comment[idx] += 'A' # Acceration

    # opmargin stats
    for idx in [3]:
        data = data_dict[key[idx]]
        crit = criteria_dict[key[idx]] 
        conditions = [
            data[1] <= crit[1], # cv
            data[2] >= crit[2], # slope
        ]
        if all(conditions):
            if data[0] >= crit[0][0]:
                res[idx] = score[idx]
            elif data[0] >= crit[0][1]:
                res[idx] = round(score[idx]*(data[0]-crit[0][1])/(crit[0][0]-crit[0][1]), 1)
            else:
                res[idx] = 0
        if data[3] >= 0:
            comment[idx] += 'A' # Acceration

    # nopincome stats, debt stats, liquid_asset_ratio_stats, liquid_debt_ratio_stats
    for idx in [4, 6, 8, 9]:
        data = data_dict[key[idx]]
        crit = criteria_dict[key[idx]] 
        conditions = [
            data[1] <= crit[1], # cv
        ]
        if all(conditions):
            res[idx] = score[idx]

    # debt_to_equity_ratio_stats
    for idx in [10]:
        data = data_dict[key[idx]]
        crit = criteria_dict[key[idx]] 
        conditions = [
            data[0] <= crit[0], # mean
            data[1] <= crit[1], # cv
        ]
        if all(conditions):
            res[idx] = score[idx]
        if data[2] >= 0:
            comment[idx] += 'I' # Increasing
    
    return res, comment

def classify_companies(codelist, criteria_dict, period:str, qa_db=qa_db):
    selected_companies = []
    res_dict = {}
    for code in codelist:
        data_dict = qa_db.loc[code, period]
        if pd.isna(data_dict) == False:
            res, comment = compare_logic(data_dict, criteria_dict, period)
            if res.count(0) == 0:
                selected = True
                selected_companies.append(code)
                # print(code, selected, sum(res), res, comment)
            else: 
                selected = False
                pass
            # print(code, selected, sum(res), res, comment)
            res_dict[code] = {
                'selected': selected,
                'score': sum(res),
                'result': res,
                'comment': comment
            }
    res_df = pd.DataFrame.from_dict(res_dict, orient='index')
    res_df = res_df.sort_values(by='score', ascending=False) 
    return selected_companies, res_df

#%% 
df_krx = get_df_krx()
codelist = qa_db.index.tolist()
periods = get_periods()

all_selected_companies = []
all_res_df = {}
for period in periods:
    selected_companies, res_df  = classify_companies(codelist, criteria_dict, period)
    all_selected_companies += selected_companies
    all_res_df[period] = res_df

# print(all_res_df['24Q'])
#%%

top_codes = []
for period in periods: 
    top_codes += all_res_df[period].index[:N].tolist()

codelist = list(set(all_selected_companies + top_codes))

score_trend_df = pd.DataFrame(index = all_selected_companies, columns = ['name', 'selected', 'top'+str(N)]+periods)
for code in score_trend_df.index:
    score_trend_df.loc[code, 'name'] = df_krx.loc[code, 'Name']
    selected = ''
    top = ''
    for period in periods:
        if code in all_res_df[period].index:
            score_trend_df.loc[code, period] = all_res_df[period].loc[code, 'score']
            selected += 'T' if all_res_df[period].loc[code, 'selected'] else '-'
            top += 'Y' if code in all_res_df[period].index[:N] else '-'
        else:
            selected += '_'
            top += '_'
    score_trend_df.loc[code, 'selected'] = selected
    score_trend_df.loc[code, 'top'+str(N)] = top
display(score_trend_df)

# price trend, PER/PBR
# PER trend (refer to the already made code)
# %%
show_data('417790') 
# display(all_res_df['20Q'])
