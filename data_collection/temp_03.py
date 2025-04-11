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

def get_quarterly_data(code, fr_db, unit=10**6, key_accounts=[]):
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
code = '005930'
res = get_quarterly_data(code, main_db)
#%%

# Function to test if 'res' is an outstanding company (last 16 quarters)
def is_outstanding_company(res):
    # Define adjustable thresholds at the top
    MIN_QUARTERS = 8  # Minimum quarters of data required
    MAX_QUARTERS = 100  # Maximum quarters to analyze (last quarters)
    REVENUE_GROWTH_MIN = 5.0  # Average YoY revenue growth (%) 
    MAX_NEGATIVE_GROWTH_COUNT = 8  # Max quarters with >5% revenue decline
    REVENUE_DIP_THRESHOLD = -5.0  # Threshold for a significant revenue dip (%)
    OP_MARGIN_MIN = 12.0  # Minimum average operating margin (%)
    NET_MARGIN_MIN = 10.0  # Minimum average net margin (%)
    LIQUID_ASSET_RATIO_MIN = 20.0  # Minimum average liquid asset ratio (%)
    LIQUID_DEBT_RATIO_MAX = 50.0  # Maximum average liquid debt ratio (%)
    DEBT_TO_EQUITY_MAX = 50.0  # Maximum average debt-to-equity ratio (in %, e.g., 50% = 0.5 as a ratio)
    REVENUE_VOLATILITY_MAX = 10.0  # Maximum revenue volatility (%)

    # Transpose the DataFrame so quarters are rows and accounts are columns
    df = res.T
    
    # Ensure numeric data
    df = df.astype(float)
    
    # Limit to the last MAX_QUARTERS (16) quarters
    if len(df) > MAX_QUARTERS:
        df = df.tail(MAX_QUARTERS)
    
    # Drop rows with missing data for key metrics (adjust as needed)
    df = df.dropna(subset=['revenue', 'net_income', 'operating_income', 
                           'assets', 'debts', 'liquid_assets', 'liquid_debts', 'liquid_asset_ratio', 'liquid_debt_ratio', 'debt_to_equity_ratio'])
    
    if len(df) < MIN_QUARTERS:
        return False, f"Insufficient data (need at least {MIN_QUARTERS} quarters, got {len(df)} after limiting to last {MAX_QUARTERS})"

    # 1. Revenue Growth: >REVENUE_GROWTH_MIN% YoY average, no more than MAX_NEGATIVE_GROWTH_COUNT dips
    revenue_yoy = df['revenue'].pct_change(periods=4) * 100  # YoY (4 quarters ago)
    avg_revenue_growth = revenue_yoy.mean()
    negative_growth_count = (revenue_yoy < REVENUE_DIP_THRESHOLD).sum()
    if avg_revenue_growth <= REVENUE_GROWTH_MIN or negative_growth_count > MAX_NEGATIVE_GROWTH_COUNT:
        return False, f"Revenue growth issue: Avg {avg_revenue_growth:.2f}% (min {REVENUE_GROWTH_MIN}%), {negative_growth_count} dips (max {MAX_NEGATIVE_GROWTH_COUNT})"

    # 2. Profitability: Operating margin >OP_MARGIN_MIN%, Net margin >NET_MARGIN_MIN%
    avg_op_margin = df['opmargin'].mean()
    net_margin = (df['net_income'] / df['revenue'] * 100)
    avg_net_margin = net_margin.mean()
    if avg_op_margin <= OP_MARGIN_MIN or avg_net_margin <= NET_MARGIN_MIN:
        return False, f"Profitability issue: Op margin {avg_op_margin:.2f}% (min {OP_MARGIN_MIN}%), Net margin {avg_net_margin:.2f}% (min {NET_MARGIN_MIN}%)"

    # 3. Liquidity: Liquid asset ratio >LIQUID_ASSET_RATIO_MIN%, Liquid debt ratio <LIQUID_DEBT_RATIO_MAX%
    avg_liquid_asset_ratio = df['liquid_asset_ratio'].mean()
    avg_liquid_debt_ratio = df['liquid_debt_ratio'].mean()
    if avg_liquid_asset_ratio <= LIQUID_ASSET_RATIO_MIN or avg_liquid_debt_ratio >= LIQUID_DEBT_RATIO_MAX:
        return False, f"Liquidity issue: Liquid asset ratio {avg_liquid_asset_ratio:.2f}% (min {LIQUID_ASSET_RATIO_MIN}%), Liquid debt ratio {avg_liquid_debt_ratio:.2f}% (max {LIQUID_DEBT_RATIO_MAX}%)"

    # 4. Leverage: Debt-to-equity ratio <DEBT_TO_EQUITY_MAX%
    df['equity'] = df['assets'] - df['debts']
    df['debt_to_equity_ratio'] = (df['debts'] / df['equity']) * 100
    avg_debt_to_equity = df['debt_to_equity_ratio'].mean()
    if avg_debt_to_equity >= DEBT_TO_EQUITY_MAX:
        return False, f"Leverage issue: Debt-to-equity ratio {avg_debt_to_equity:.2f}% (max {DEBT_TO_EQUITY_MAX}%)"

    # 5. Stability: Revenue volatility <REVENUE_VOLATILITY_MAX%
    revenue_volatility = df['revenue'].pct_change().std() * 100
    if revenue_volatility >= REVENUE_VOLATILITY_MAX:
        return False, f"Stability issue: Revenue volatility {revenue_volatility:.2f}% (max {REVENUE_VOLATILITY_MAX}%)"

    # If all criteria pass
    return True, "Outstanding company"

# Test the function
result, reason = is_outstanding_company(res)
print(f"Is Samsung Electronics outstanding? {result}")
print(f"Reason: {reason}")