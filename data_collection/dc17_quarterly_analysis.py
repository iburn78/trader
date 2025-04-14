#%%
import pandas as pd
import os
from trader.tools.tools import get_dbs, get_quarterly_data, basic_stats, rounder

fr_db, pr_db, df_krx, qa_db = get_dbs() 

pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
qa_db_file = os.path.join(pd_, 'data_collection/data/qa_db.pkl') 

KEY_ACCOUNT = 'operating_income'
MIN_QUARTERS = 8  # Minimum quarters of data required
MAX_QUARTERS = 24  # Maximum quarters to analyze 
STEPS = 4  # Number of quarters to reduce analysis window
REVENUE_DIP_THRESHOLD = -5.0  # Threshold for a significant revenue dip (%)
TODAY = pd.Timestamp.today().strftime('%Y-%m-%d')

#%% 
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

def code_handler(code):
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

def builder(qa_db, codelist): 
    reslist = []
    for code in codelist:
        res = code_handler(code)
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

codes = df_krx.index.tolist()[0:1000]
qa_db = builder(qa_db, codes)
display(qa_db)

#%% 

def is_outstanding_company(q_df):
    REVENUE_GROWTH_MIN = 10.0  # Average YoY revenue growth (%) 
    MAX_NEGATIVE_GROWTH_COUNT = float(MAX_QUARTERS/5)  # Max quarters with >[]% revenue decline
    OP_MARGIN_MIN = 12.0
    NET_MARGIN_MIN = 10.0
    LIQUID_ASSET_RATIO_STD_MAX = 10.0 # Max std deviation of liquid asset ratio (%)
    LIQUID_DEBT_RATIO_STD_MAX = 10.0 # Max std deviation of liquid debt ratio (%)
    DEBT_TO_EQUITY_MAX = 150.0 # Max average debt-to-equity ratio (%)
    DEBT_TO_EQUITY_STD_MAX = 10.0 # Max std deviation of debt-to-equity ratio (%)

    if q_df is None or len(q_df) == 0:
        return False, "No data available"   

    df = q_df.T
    df = df[-MAX_QUARTERS:]
    if len(df[KEY_ACCOUNT].dropna()) < MIN_QUARTERS:
        return False, f"Insufficient data (need at least {MIN_QUARTERS} quarters, got {len(df[KEY_ACCOUNT].dropna())})"

    # 1. Revenue Growth and Stability
    # if len(df['revenue'].dropna()) < MIN_QUARTERS:
    #     return False, "Revenue data is missing"
    revenue_yoy = df['revenue'].dropna().pct_change(periods=4) * 100  # YoY (4 quarters ago)
    avg_revenue_growth = revenue_yoy.mean()
    negative_growth_count = (revenue_yoy < REVENUE_DIP_THRESHOLD).sum()
    if pd.isna(avg_revenue_growth) or pd.isna(negative_growth_count):
        return False, "Revenue growth data is missing"
    if avg_revenue_growth < REVENUE_GROWTH_MIN or negative_growth_count > MAX_NEGATIVE_GROWTH_COUNT:
        return False, f"Revenue growth issue: Avg {avg_revenue_growth:.2f}% (min {REVENUE_GROWTH_MIN}%), {negative_growth_count} dips (max {MAX_NEGATIVE_GROWTH_COUNT})"

    # 2. Profitability
    avg_op_margin = df['opmargin'].mean()
    net_margin = (df['net_income'] / df['revenue'] * 100)
    avg_net_margin = net_margin.mean()
    if avg_op_margin <= OP_MARGIN_MIN or avg_net_margin <= NET_MARGIN_MIN:
        return False, f"Profitability issue: Op margin {avg_op_margin:.2f}% (min {OP_MARGIN_MIN}%), Net margin {avg_net_margin:.2f}% (min {NET_MARGIN_MIN}%)"

    # 3. Liquidity
    liquid_asset_ratio_std = df['liquid_asset_ratio'].std()
    liquid_debt_ratio_std = df['liquid_debt_ratio'].std()
    if liquid_asset_ratio_std > LIQUID_ASSET_RATIO_STD_MAX or liquid_debt_ratio_std > LIQUID_DEBT_RATIO_STD_MAX:
        return False, f"Liquidity issue: Liquid asset ratio std {liquid_asset_ratio_std:.2f} (max {LIQUID_ASSET_RATIO_STD_MAX}), Liquid debt ratio std {liquid_debt_ratio_std:.2f} (max {LIQUID_DEBT_RATIO_STD_MAX})"

    # 4. Leverage
    avg_debt_to_equity = df['debt_to_equity_ratio'].mean()
    debt_to_equity_std = df['debt_to_equity_ratio'].std()
    if avg_debt_to_equity > DEBT_TO_EQUITY_MAX or debt_to_equity_std > DEBT_TO_EQUITY_STD_MAX:
        return False, f"Leverage issue: Debt-to-equity ratio {avg_debt_to_equity:.2f}% (max {DEBT_TO_EQUITY_MAX}%) Debt-to-equity std {debt_to_equity_std:.2f} (max {DEBT_TO_EQUITY_STD_MAX})"

    # If all criteria pass
    return True, "Outstanding company"

