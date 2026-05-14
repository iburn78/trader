#%%
from dataclasses import dataclass, field
from typing import Literal
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from datetime import datetime
from trader.tools.as_tools import is_KRX_open, load_market_data

'''
ma: MarCap + Amount
outshares: # shares outstanding
volume: # shares traded
amount: money amount traded
slope: liear regression over all periods 
recent_inc: comparing between last 2 priods
'''
df_krx, prices, volumes, fr_main_db = load_market_data()

# business days in each aggregation
BLOCK_MAP = {
    'd': 1,
    'w': 5,
    'm': 20,
}

KRW_UNIT = 1e9 
KRW_UNIT_KR = {
    1e12: 'jo',
    1e9: '10-uk',
    1e8: 'uk', 
}

QCOLS = sorted(c for c in fr_main_db.columns if 'Q' in c)
quarter_map = {
    '1Q': '01-01',
    '2Q': '04-01',
    '3Q': '07-01',
    '4Q': '10-01',
}
DATECOLS = [
    pd.Timestamp(f'{year}-{quarter_map[q]}')
    for year, q in (col.split('_') for col in QCOLS)
]
# =========================================================
# data structure
# =========================================================

@dataclass
class StockInfo:
    code: str
    time: pd.Timestamp # creation time 

    main_df: pd.DataFrame

    # ma related
    ma_rate: pd.DataFrame
    ma_fitted: pd.DataFrame

    meta: dict = field(
        default_factory=lambda: {
            'unit': None,
            'aggregation': None,
        }
)

# =========================================================
# operators
# =========================================================
def get_ma_data(code: str, start_date = None): # MarCap, Amount, start_date in 'yyyy-mm-dd' format
    outshares = df_krx.at[code, 'Stocks']

    ma_data = pd.DataFrame({
        'marcap': prices[code] * outshares / KRW_UNIT,
        'amount': volumes[code] * prices[code] / KRW_UNIT,
    })
    ma_data = ma_data.dropna()

    now = datetime.now()
    # ----------------------------------------------------------------------------
    # if market is open (or at least in early hours), then today record is removed
    # ----------------------------------------------------------------------------
    if is_KRX_open(now=now):
        ma_data = ma_data[ma_data.index.date != now.date()]
    
    if start_date:
        ma_data = ma_data.loc[start_date:]

    return ma_data

def ma_aggregate_periods(
    ma_data: pd.DataFrame,
    aggregation: Literal['d', 'w', 'm'],
) -> pd.DataFrame:
    """
    Aggregate daily records into backward-aligned
    discrete blocks.

    Incomplete oldest block is discarded.
    """

    if aggregation not in BLOCK_MAP:
        raise ValueError(f'invalid aggregation: {aggregation}')

    block_size = BLOCK_MAP[aggregation]

    usable = (len(ma_data) // block_size) * block_size

    if usable == 0:
        raise ValueError('not enough rows')

    ma_data = ma_data.iloc[-usable:]

    rows = []

    for start in range(0, usable, block_size):

        block = ma_data.iloc[start:start + block_size]
        marcap = block['marcap'].iloc[-1]
        amount = block['amount'].mean()

        rows.append({
            'time': block.index[-1],
            'marcap': marcap,
            'amount': amount,
        })

    return pd.DataFrame(rows).set_index('time')

def _compute_single_regression(
    s: pd.Series,
) -> tuple[float, float, pd.Series]:
    """
    Compute:
        - geometric slope (log)
        - recent pct change
        - fitted regression series
    """

    x = np.arange(len(s))
    y = s.values

    # just use linear
    slope, intercept = np.polyfit(x,y,1)
    fit_values = intercept + slope*x
    
    # saving fitted values is more efficient than recalc in plot
    fit_ = pd.Series(
        fit_values,
        index=s.index,
    )

    recent_inc = s.iloc[-1] / s.iloc[-2] - 1

    return slope, recent_inc, fit_

def compute_ma_rates(
    ma_data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute:
        - trend slopes
        - recent increases
        - fitted regression lines
    """

    rate = pd.DataFrame(
        index=['slope', 'recent_inc'],
        columns=['marcap', 'amount', 'unit'],
    )

    fitted = pd.DataFrame(index=ma_data.index)

    for col in ['marcap', 'amount']:
        slope, recent_inc, fit_ = _compute_single_regression(ma_data[col])

        rate.loc['slope', col] = slope
        rate.loc['slope', 'unit'] = KRW_UNIT_KR[KRW_UNIT]
        rate.loc['recent_inc', col] = recent_inc
        rate.loc['recent_inc', 'unit'] = '%'

        fitted[col] = fit_

    return rate, fitted

def build_stockinfo(
    code: str,
    aggregation: Literal['d', 'w', 'm'] = 'w',
    start_date = None
) -> StockInfo:

    _ma_data = get_ma_data(code, start_date)
    ma_data = ma_aggregate_periods(_ma_data, aggregation) # aggregrated
    ma_rate, ma_fitted = compute_ma_rates(ma_data)
    meta = {
        'unit': KRW_UNIT,
        'aggregation': aggregation
    }

    return StockInfo(
        code=code,
        time=pd.Timestamp.now(),

        main_df=ma_data,
        ma_rate=ma_rate,
        ma_fitted=ma_fitted,
        meta=meta
    )


# =========================================================
# plotting
# =========================================================

def plot_stockinfo(
    stock_info: StockInfo,
    figsize: tuple = (12, 6),
):

    fig, ax1 = plt.subplots(figsize=figsize)
    ax2 = ax1.twinx()

    main_df = stock_info.main_df
    ma_fitted = stock_info.ma_fitted
    x = main_df.index

    ax1.plot(
        x,
        main_df['marcap'],
        color='black',
        linewidth=2,
        label='marcap',
    )
    ax1.plot(
        x,
        ma_fitted['marcap'],
        linewidth=2,
        color='gray',
        linestyle='--',
        label='marcap trend',
    )

    ax2.bar(
        x,
        main_df['amount'],
        color='orange',
        alpha=0.5,
        width=np.median(np.diff(mdates.date2num(x))) * 0.7,
        label='amount',
    )
    ax2.plot(
        x,
        ma_fitted['amount'],
        linewidth=2,
        alpha=0.8,
        color='tab:orange',
        linestyle='--',
        label='amount trend',
    )

    # -----------------------------------------------------
    # annotations, title, grid, axis, legends, etc
    # -----------------------------------------------------
    latest_time = main_df.index[-1]
    latest_marcap = main_df['marcap'].iloc[-1]
    latest_amount = main_df['amount'].iloc[-1]

    recent_marcap_inc = stock_info.ma_rate.loc['recent_inc', 'marcap']
    recent_amount_inc = stock_info.ma_rate.loc['recent_inc', 'amount']

    ax1.annotate(
        f'rp:{recent_marcap_inc:.0%}',
        xy=(latest_time, latest_marcap),
        xytext=(3, 3),
        textcoords='offset points',
    )

    ax2.annotate(
        f'ra:{recent_amount_inc:.0%}',
        xy=(latest_time, latest_amount),
        xytext=(3, 3),
        textcoords='offset points',
    )
    slope_marcap = stock_info.ma_rate.loc['slope', 'marcap']
    slope_amount = stock_info.ma_rate.loc['slope', 'amount']

    fit_marcap = ma_fitted['marcap']
    fit_amount = ma_fitted['amount']

    mid_marcap = len(fit_marcap) // 2
    mid_amount = len(fit_amount) // 2

    marcap_x = fit_marcap.index[mid_marcap]
    marcap_y = fit_marcap.iloc[mid_marcap]

    amount_x = fit_amount.index[mid_amount]
    amount_y = fit_amount.iloc[mid_amount]

    ax1.annotate(
        f'sp:{slope_marcap:,.0f}',
        xy=(marcap_x, marcap_y),
        xytext=(0, 10),
        textcoords='offset points',
    )

    ax2.annotate(
        f'sa:{slope_amount:,.0f}',
        xy=(amount_x, amount_y),
        xytext=(0, 10),
        textcoords='offset points',
    )
    title = (
        f'{stock_info.code}'
        f' | '
        f'{stock_info.time:%Y-%m-%d %H:%M}'
        f' | '
        f'aggr: {stock_info.meta['aggregation']}'
    )
    ax1.set_title(title)
    ax1.set_ylabel(f'MarCap ({KRW_UNIT_KR[KRW_UNIT]} KRW)')
    ax2.set_ylabel(f'Amount ({KRW_UNIT_KR[KRW_UNIT]} KRW)')

    ax1.set_ylim(bottom=0)
    ax2.set_ylim(bottom=0)

    ax1.yaxis.set_major_formatter(
        FuncFormatter(lambda x, _: f'{x:,.0f}')
    )
    ax2.yaxis.set_major_formatter(
        FuncFormatter(lambda x, _: f'{x:,.0f}')
    )

    ax1.grid(
        True,
        linestyle='--',
        alpha=0.3,
    )

    ax1.xaxis.set_major_formatter(
        mdates.DateFormatter('%Y-%m-%d')
    )
    fig.autofmt_xdate()

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc='upper left',
    )

    plt.tight_layout()
    plt.show()


# =========================================================
# adding FR data
# =========================================================

def _get_fr_db_for_code(fr_main_db, code):
    # use CFS if data exists, and otherwise OFS (for that account)
    fr_target = fr_main_db.loc[fr_main_db['code']==code]
    cfs = fr_target.loc[fr_target['fs_div'] == "CFS"]
    cfs_qcols = cfs.loc[(cfs['account'] == 'revenue') | (cfs['account'] == 'operating_income'), QCOLS]
    # get CFS(consolidated) if not empty
    if cfs_qcols.isna().all().all():
        ofs = fr_target.loc[fr_target['fs_div'] == "OFS"] 
        return ofs
    return cfs

def _extract_account_data(fr_db_for_code, account):
    row = fr_db_for_code.loc[fr_db_for_code['account'] == account, QCOLS].iloc[0].copy() # series
    row.index = DATECOLS
    row = row.ffill()
    row = row/KRW_UNIT
    return row

def _ffill_inf(df):
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.ffill().dropna()
    return df

# ltm: last twelve months
def _build_fr_data(fr_main_db, code):
    fr_db_for_code = _get_fr_db_for_code(fr_main_db, code)
    row_r = _extract_account_data(fr_db_for_code, 'revenue')
    row_o = _extract_account_data(fr_db_for_code, 'operating_income')
    fr_data = pd.DataFrame({
        'revenue': row_r,
        'opincome': row_o,
    })
    fr_data['revenue_ltm'] = fr_data['revenue'].rolling(4).sum()
    fr_data['opincome_ltm'] = fr_data['opincome'].rolling(4).sum()
    fr_data['opmargin'] = fr_data['opincome']/fr_data['revenue']
    fr_data['opmargin_ltm'] = fr_data['opincome_ltm']/fr_data['revenue_ltm']
    return _ffill_inf(fr_data)

# PER: assumes the same 4 quarters 
def append_fr_data(stockinfo: StockInfo):
    fr_data = _build_fr_data(fr_main_db, stockinfo.code)
    stockinfo.main_df[fr_data.columns]=fr_data.reindex(stockinfo.main_df.index,method='ffill')
    stockinfo.main_df['PER'] = stockinfo.main_df['marcap']/(4*stockinfo.main_df['opincome'])
    stockinfo.main_df['PER_ltm'] = stockinfo.main_df['marcap']/stockinfo.main_df['opincome_ltm']
    stockinfo.main_df = _ffill_inf(stockinfo.main_df)
    return stockinfo


#%% 
code = '005930'
aggregation = 'm'
start_date = '2023-01-01'

stockinfo = build_stockinfo(code=code, aggregation=aggregation, start_date=start_date)
stockinfo = append_fr_data(stockinfo)
plot_stockinfo(stockinfo)

print(stockinfo.main_df)
