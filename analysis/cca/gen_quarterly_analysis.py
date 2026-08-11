#%%
import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from trader.tools.dc_tools import get_main_financial_reports_db, get_quarterly_data
# -----------------------------------------------------------------------------------
# QA_DB (quarterly analysis dbs)
# - infrequent update is ok (though fast), no need to daily update
# - used in CCA(company classification), but completely independent from CCA in generation

# - used pkl to save objects in df
# - this is purely local computation, no network overloads
# -----------------------------------------------------------------------------------
'''
index 'Code'
column 'meta'
    meta_dict = {
        'name': '삼성전자',
        'date': '2026-06-10', # date of analysis
        'last_quarter': '26.2' # last quarter of data
    }
column '{n}Q': n = 24, 20, ..., 8
    # stats = [mean, cv, slope, acc]
    quarter_dict = {
        'revenue_growth': [avg_revenue_growth_pct, negative_growth_count], # percent (yoy by quater), # count
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
'''

KEY_ACCOUNT = 'operating_income'
MIN_QUARTERS = 8  # Minimum quarters of data required
MAX_QUARTERS = 24  # Maximum quarters to analyze 
STEPS = 4  # Number of quarters to reduce analysis window
REVENUE_DIP_THRESHOLD = -5.0  # Threshold for a significant revenue dip (%, quarter)
TODAY = pd.Timestamp.today().strftime('%Y-%m-%d')

def slope_and_acc(series: pd.Series):
    series = series.dropna().astype(float)
    x = np.arange(len(series))
    y = series.values

    if len(y) < 2:
        return np.nan, np.nan

    mean = np.mean(y)
    slope = np.polyfit(x, y, 1)[0]
    if len(x) > 2:
        acc = np.polyfit(x, y, 2)[0]
    else:
        acc = np.nan

    # "increasing" if slope > 0 else "decreasing" if slope < 0 else "flat",
    # "accelerating upward" if a > 0 else "accelerating downward" if a < 0 else "no acceleration"
    return slope, acc

def rounder(x):
    if x is None or pd.isna(x) or np.isinf(x):
        return np.nan
    elif isinstance(x, str):
        return x
    elif isinstance(x, (int, np.integer)):
        return x 
    elif isinstance(x, (float, np.floating)):
        if abs(x) >= 100: 
            return int(x)
        else:
            return round(x, 2)

def basic_stats(series: pd.Series):
    mean = series.mean()
    std = series.std()
    slope, acc = slope_and_acc(series)
    cv = std / mean if pd.notna(mean) and mean != 0 else np.nan
    lst = [mean, cv, slope, acc]
    return [rounder(x) for x in lst]

def calculate_stats(df):
    # 1. Revenue Growth and Stability
    ry = df['revenue'].dropna()
    if len(ry) > 4:
        revenue_yoy = ry.pct_change(periods=4) * 100  # YoY (4 quarters ago)
        avg_revenue_growth_pct = rounder(revenue_yoy.mean())
        negative_growth_count = (revenue_yoy < REVENUE_DIP_THRESHOLD).sum()
    else:
        avg_revenue_growth_pct = np.nan
        negative_growth_count = np.nan
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
    quarter_dict = {
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
    return quarter_dict

def code_handler(code, fr_db, df_krx):
    q_df = get_quarterly_data(code, fr_db)
    if q_df is None:
        return None
    key_account_len = len(q_df.loc[KEY_ACCOUNT].dropna())

    if key_account_len < MIN_QUARTERS:
        return None
    quarter_steps = list(range(MIN_QUARTERS, min(key_account_len, MAX_QUARTERS)+1, STEPS))[::-1]
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

def qa_db_builder(codelist, fr_db, df_krx, qa_db_file, qa_db = None): 
    reslist = []
    pbar = tqdm(codelist, desc="QA DB")    
    for code in pbar:
        pbar.set_postfix(code=code)
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
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    df_krx_file = os.path.join(pd_, 'data_collect/data/df_krx.feather') 

    fr_db = get_main_financial_reports_db()
    df_krx = pd.read_feather(df_krx_file)

    codelist = df_krx.index.tolist()

    # save qa_db file
    qa_db_file = os.path.join(pd_, 'data_collect/data/qa_db.pkl') 
    qa_db = qa_db_builder(codelist, fr_db, df_krx, qa_db_file) 
