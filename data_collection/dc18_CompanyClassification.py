#%% 
import pandas as pd
import numpy as np
import os

pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
qa_db_file = os.path.join(pd_, 'data_collection/data/qa_db.pkl') 
qa_db = pd.read_pickle(qa_db_file)

cv_threshold_prime = 0.3
cv_threshold = 0.7
outstanding_companies = {
    'revenue_growth': [5, 0.3], # percent, # count (e.g., 0.2 = 20% of quarters: to be multiplied by period)
    'revenue_stats': [np.nan, cv_threshold_prime, 0, np.nan], # size
    'opincome_stats': [np.nan, cv_threshold_prime, 0, np.nan], # size
    'opmargin_stats': [12, cv_threshold_prime, 0, np.nan], # percent
    'nopincome_stats': [np.nan, cv_threshold, np.nan, np.nan], # size
    'asset_stats': [np.nan, cv_threshold, 0, np.nan], # size
    'debt_stats': [np.nan, cv_threshold, np.nan, np.nan], # size
    'equity_stats': [np.nan, cv_threshold, 0, np.nan], # size
    'liquid_asset_ratio_stats': [np.nan, cv_threshold, np.nan, np.nan], # percent
    'liquid_debt_ratio_stats': [np.nan, cv_threshold, np.nan, np.nan], # percent
    'debt_to_equity_ratio_stats': [200, cv_threshold, np.nan, np.nan] # percent
}

def compare_logic(period, data_dict, criteria_dict):
    key = list(data_dict.keys())
    if key != list(criteria_dict.keys()):
        return False

    res = [False] * len(data_dict.keys())
    comment = [''] * len(data_dict.keys())

    # revenue growth
    idx = 0
    data = data_dict[key[idx]]
    crit = criteria_dict[key[idx]] 
    conditions = [
        data[0] >= crit[0], 
        data[1] <= int(period*crit[1]), 
    ]
    if all(conditions):
        res[idx] = True
    if data[0] >= crit[0]*2:
        comment[idx] += 'H' # High growth'
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
            res[idx] = True
        if data[3] >= 0:
            comment[idx] += 'A' # Acceration

    # opmargin stats
    for idx in [3]:
        data = data_dict[key[idx]]
        crit = criteria_dict[key[idx]] 
        conditions = [
            data[0] >= crit[0], # mean
            data[1] <= crit[1], # cv
            data[2] >= crit[2], # slope
        ]
        if all(conditions):
            res[idx] = True
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
            res[idx] = True

    # debt_to_equity_ratio_stats
    for idx in [10]:
        data = data_dict[key[idx]]
        crit = criteria_dict[key[idx]] 
        conditions = [
            data[0] <= crit[0], # mean
            data[1] <= crit[1], # cv
        ]
        if all(conditions):
            res[idx] = True
        if data[2] >= 0:
            comment[idx] += 'I' # Increasing
    
    return res, comment

# visualize datadict 
# overall score datadict
# price trend, PER/PBR
# PER trend (refer to the already made code)

for code in qa_db.index[:]:
    data_dict = qa_db.loc[code, '24Q']
    period = 16
    if pd.isna(data_dict) == False:
        res, comment = compare_logic(period, data_dict, outstanding_companies)
        # print(sum(res), res, comment)
        if all(res):
            print(code, '################ Outstanding company')
            print(comment)
        else: 
            pass
    else: 
        pass
