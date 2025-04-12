#%% 
import os
import pandas as pd
from trader.tools.tools import _choose_unique_rows

cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
# below dbs are updated by the previous day (if synced)
main_db_file = os.path.join(cd_, 'data/financial_reports_main.feather') 
price_db_file = os.path.join(cd_, 'data/price_DB.feather') 
df_krx_file = os.path.join(cd_, 'data/df_krx.feather') 

main_db = pd.read_feather(main_db_file)
price_db = pd.read_feather(price_db_file)
df_krx = pd.read_feather(df_krx_file)

# display(main_db)
# display(price_db)
# display(df_krx)

def get_quarterly_data(code, fr_db, unit=10**6):
    quarter_cols= [s for s in fr_db.columns.values if 'Q' in s]
    quarter_cols.sort()
    fs_div_mode = 'CFS'
    y = fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), ['account']+quarter_cols].drop_duplicates().set_index(['account'])
    if y.isnull().all().all():
        fs_div_mode = 'OFS'
        y = fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), ['account']+quarter_cols].drop_duplicates().set_index(['account'])
    if y.isnull().all().all():
        # raise Exception('quarterly data of {} is empty.'.format(code))
        print('quarterly data of {} is empty.'.format(code))
        return None

    # date_updated = str(fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), 'date_updated'].values[0])
    y.columns = [s.replace('2020','XX').replace('20','').replace('XX','20').replace('_','.').replace('Q','') for s in quarter_cols]
    yim = y/unit
    yim=_choose_unique_rows(yim, 'account')
    yim.loc['opmargin', :] = yim.loc['operating_income']/yim.loc['revenue'].replace(0, pd.NA)*100   # sometimes, revenue entry is zero, then it computes to '+- np.inf'
    yim.loc['liquid_asset_ratio', :] = yim.loc['liquid_assets']/yim.loc['assets']*100
    yim.loc['liquid_debt_ratio', :] = yim.loc['liquid_debts']/yim.loc['debts']*100
    yim.loc['debt_to_equity_ratio', :] = yim.loc['debts']/yim.loc['equity']*100
    return yim #, date_updated


#%% 

def is_outstanding_company(q_df):
    KEY_ACCOUNT = 'operating_income'
    MIN_QUARTERS = 8  # Minimum quarters of data required
    MAX_QUARTERS = 16  # Maximum quarters to analyze 
    REVENUE_GROWTH_MIN = 10.0  # Average YoY revenue growth (%) 
    REVENUE_DIP_THRESHOLD = -5.0  # Threshold for a significant revenue dip (%)
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

# q_df = get_quarterly_data('005930', main_db)
# result, reason = is_outstanding_company(q_df)

#%% 

for code in df_krx.index[500:1000]:
    print(code)

    q_df = get_quarterly_data(code, main_db)
    result, reason = is_outstanding_company(q_df)
    if result: 
        print(code, df_krx.loc[code, 'Name'], reason)
