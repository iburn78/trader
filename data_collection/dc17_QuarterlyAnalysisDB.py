#%%
import pandas as pd
import numpy as np
import os
from trader.tools.tools import get_dbs, get_quarterly_data, basic_stats, rounder, log_print

def calculate_stats(df):
    # 1. Revenue Growth and Stability
    revenue_yoy = df['revenue'].dropna().pct_change(periods=4) * 100  # YoY (4 quarters ago)
    avg_revenue_growth_pct = rounder(revenue_yoy.mean())
    negative_growth_count = (revenue_yoy < REVENUE_DIP_THRESHOLD).sum()
    rev_stats = basic_stats(df['revenue'])

    # 2. Profitability
    opincome_stats = basic_stats(df['operating_income'])
    opmargin_pct_stats = basic_stats(df['opmargin']) # percent
    nopincome_stats = basic_stats(df['net_income'] - df['operating_income'])

    # 3. Balance Sheet statistics
    asset_stats = basic_stats(df['assets'])
    debt_stats = basic_stats(df['debts'])
    equity_stats = basic_stats(df['equity'])

    # 4. Liquidity
    liquid_asset_ratio_pct_stats = basic_stats(df['liquid_asset_ratio']) # percent
    liquid_debt_ratio_pct_stats = basic_stats(df['liquid_debt_ratio']) # percent

    # 5. Leverage
    debt_to_equity_ratio_pct_stats = basic_stats(df['debt_to_equity_ratio']) # percent

    # stats = [mean, cv, slope, acc]
    result_dict = {
        'revenue_growth': [avg_revenue_growth_pct, negative_growth_count], # percent, # count
        'revenue_stats': rev_stats, # size
        'opincome_stats': opincome_stats, # size
        'opmargin_stats': opmargin_pct_stats, # percent
        'nopincome_stats': nopincome_stats, # size
        'asset_stats': asset_stats, # size
        'debt_stats': debt_stats, # size
        'equity_stats': equity_stats, # size
        'liquid_asset_ratio_stats': liquid_asset_ratio_pct_stats, # percent
        'liquid_debt_ratio_stats': liquid_debt_ratio_pct_stats, # percent
        'debt_to_equity_ratio_stats': debt_to_equity_ratio_pct_stats, # percent
    }
    return result_dict

def code_handler(code, fr_db, df_krx):
    print(code)
    q_df = get_quarterly_data(code, fr_db)
    if q_df is None:
        return None
    key_account_len = len(q_df.loc[KEY_ACCOUNT].dropna())
    if key_account_len < MIN_QUARTERS:
        return None
    quarter_steps = range(min(key_account_len, MAX_QUARTERS), MIN_QUARTERS-1, -STEPS)
    name = df_krx.loc[code, 'Name']
    quarter_labels = [f'{q}Q' for q in quarter_steps]  
    res = pd.DataFrame(columns=['meta'] + quarter_labels, index=[code])
    meta_dict = {
        'name': name,
        'date': TODAY, # date of analysis
        'last_quarter': q_df.columns[-1], # last quarter of data
    }
    res.at[code, 'meta'] = meta_dict
    for i, qs in enumerate(quarter_steps):
        df = q_df.T[-qs:] # only generates a view
        res.at[code, quarter_labels[i]] = calculate_stats(df)
    return res # returns a dataframe with single row and multiple columns

def qa_db_builder(codelist, qa_db, fr_db, df_krx, qa_db_file): 
    reslist = []
    for code in codelist:
        res = code_handler(code, fr_db, df_krx)
        if res is not None:
            reslist.append(res)
    if len(reslist) == 0:
        return qa_db
    elif len(reslist) == 1:
        reslist_all = pd.DataFrame(reslist[0])
    else: 
        reslist_all = pd.concat(reslist)
    if qa_db is not None:
        qa_db = pd.concat([qa_db, reslist_all])
        qa_db = qa_db.loc[~qa_db.index.duplicated(keep='last')]
        q_cols = [int(col[:-1]) for col in qa_db.columns if col != 'meta']
        q_cols = sorted(q_cols, reverse=True)
        quarter_labels = [f'{q}Q' for q in q_cols]  
        qa_db = qa_db[['meta'] + quarter_labels]
    else:
        qa_db = reslist_all
    # Reindex to match df_krx index and drop rows that are not in df_krx
    qa_db = qa_db.reindex(df_krx.index) 
    qa_db = qa_db.dropna(how='all')
    qa_db.to_pickle(qa_db_file)
    return qa_db

if __name__ == "__main__":
    fr_db, df_krx, qa_db = get_dbs(check_time=False) # in autorun, git-commit is done daily

    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    qa_db_file = os.path.join(pd_, 'data_collection/data/qa_db.pkl') 
    plot_gen_control_file = os.path.join(pd_, 'data_collection/data/plot_gen_control.npy')
    log_file = os.path.join(pd_, 'data_collection/log/quarterly_analysis_db.log')

    KEY_ACCOUNT = 'operating_income'
    MIN_QUARTERS = 8  # Minimum quarters of data required
    MAX_QUARTERS = 24  # Maximum quarters to analyze 
    STEPS = 4  # Number of quarters to reduce analysis window
    REVENUE_DIP_THRESHOLD = -5.0  # Threshold for a significant revenue dip (%)
    TODAY = pd.Timestamp.today().strftime('%Y-%m-%d')

    INITIAL_SIZE = 2500 # initial size of the codelist
    if qa_db == None:
        log_print(log_file, f'{TODAY} QA DB: initialization with {INITIAL_SIZE} codes')
        codelist = df_krx.index.tolist()[0:2500]
    else:
        if not os.path.exists(plot_gen_control_file):
            log_print(log_file, f'{TODAY} QA DB: ***** plot_gen_control.npy does not exist. *****')
            # raise FileNotFoundError('***** plot_gen_control.npy does not exist. *****')
            codelist = []
        else: 
            codelist = np.load(plot_gen_control_file, allow_pickle=True)
            log_print(log_file, f'{TODAY} QA DB: updating {codelist.tolist()}')
    try:
        qa_db = qa_db_builder(codelist, qa_db, fr_db, df_krx, qa_db_file) 
    except Exception as error:
        log_print(log_file, str(error))
        # raise error

