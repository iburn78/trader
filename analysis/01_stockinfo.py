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

    # ma related: MarCap, Amount
    ma_rate: pd.DataFrame
    ma_fitted: pd.DataFrame # only used in graph drawing

    # fr related: PER, OpIncome, OpMargins, etc
    fr_stats: pd.DataFrame

    meta: dict = field(
        default_factory=lambda: {
            'unit': None,
            'aggregation': None,
            'start_date': None,
        }
)

# =========================================================
# handling ma data
# =========================================================
def _get_ma_data(code: str, start_date = None): # MarCap, Amount, start_date in 'yyyy-mm-dd' format
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

def _ma_aggregate_periods(
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
    
    # saving fitted values for plots
    fit_ = pd.Series(
        fit_values,
        index=s.index,
    )

    recent_inc = s.iloc[-1] / s.iloc[-2] - 1

    return slope, recent_inc, fit_

def _compute_ma_rates(
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


# =========================================================
# handling FR data
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

def _get_fr_data(fr_main_db, code):
    fr_db_for_code = _get_fr_db_for_code(fr_main_db, code)
    row_r = _extract_account_data(fr_db_for_code, 'revenue')
    row_o = _extract_account_data(fr_db_for_code, 'operating_income')
    fr_data = pd.DataFrame({
        'revenue': row_r,
        'opincome': row_o,
    })
    return fr_data

def _get_opincome_stats(stockinfo: StockInfo, fr_data: pd.DataFrame):
    sd = stockinfo.meta['start_date']
    start_idx = max(0, fr_data.index.searchsorted(sd, side="right") - 1) # side "right" - 1 will give data from the quarter that start_date is in
    opincome = fr_data.iloc[start_idx:]['opincome']

    x = np.arange(len(opincome))
    y = opincome.values.astype(float)
    opincome_slope, _ = np.polyfit(x, y, 1) # use only slope / intercept is misleading
    x_future = np.arange(1, 4) # three quarters needed
    y_future = opincome_slope*x_future + y[-1]
    fwd_opincome = y[-1]+sum(y_future)

    return float(fwd_opincome), float(opincome_slope)
    
# PER: assumes the same 4 quarters 
# ltm: last twelve months
###_
###_ be careful with trims... gets shorter and shorter when adding
###_ align dates start_date and main_df data mismatch --- will later be a headache.
###_ make modules clearer otherwise operations will not be easy... 

def append_fr_data(stockinfo: StockInfo, fr_data):
    fr_data['revenue_ltm'] = fr_data['revenue'].rolling(4).sum()
    fr_data['opincome_ltm'] = fr_data['opincome'].rolling(4).sum()
    fr_data['opmargin'] = fr_data['opincome']/fr_data['revenue']
    fr_data['opmargin_ltm'] = fr_data['opincome_ltm']/fr_data['revenue_ltm']
    fr_data = _ffill_inf(fr_data)

    stockinfo.main_df[fr_data.columns]=fr_data.reindex(stockinfo.main_df.index,method='ffill')
    stockinfo.main_df['PER'] = stockinfo.main_df['marcap']/(4*stockinfo.main_df['opincome']) # x4 applied here
    stockinfo.main_df['PER_ltm'] = stockinfo.main_df['marcap']/stockinfo.main_df['opincome_ltm']
    stockinfo.main_df = _ffill_inf(stockinfo.main_df)

    fwd_opincome, opincome_slope = _get_opincome_stats(stockinfo, fr_data)
    PER_fwd = stockinfo.main_df['marcap'].iloc[-1]/fwd_opincome
    fr_stats = pd.DataFrame(
        index=['PER', 'opincome', 'opmargin'],
        columns=['ltm', 'qx4', 'fwd', 'slope', 'unit'],
    )

    _config = {
        'PER': {
            'ltm': stockinfo.main_df['PER_ltm'].iloc[-1],
            'qx4': stockinfo.main_df['PER'].iloc[-1],
            'fwd': PER_fwd,
            'unit': 'times',
        },

        'opincome': {
            'ltm': stockinfo.main_df['opincome_ltm'].iloc[-1],
            'qx4': stockinfo.main_df['opincome'].iloc[-1]*4,
            'fwd': fwd_opincome,
            'slope': opincome_slope,
            'unit': KRW_UNIT_KR[KRW_UNIT],
        },

        'opmargin': {
            'ltm': stockinfo.main_df['opmargin_ltm'].iloc[-1],
            'qx4': stockinfo.main_df['opmargin'].iloc[-1],
            'unit': '%',
        },
    }

    for row, values in _config.items():
        for col, val in values.items():
            fr_stats.loc[row, col] = val

    stockinfo.fr_stats = fr_stats
    return stockinfo

# =========================================================
# stockinfo operations
# =========================================================
def build_stockinfo(code: str, aggregation: Literal['d', 'w', 'm'], start_date) -> StockInfo:

    _ma_data = _get_ma_data(code, start_date)
    ma_data = _ma_aggregate_periods(_ma_data, aggregation) # aggregrated
    ma_rate, ma_fitted = _compute_ma_rates(ma_data)
    fr_stats = pd.DataFrame() # empty df for now
    meta = {
        'unit': KRW_UNIT,
        'aggregation': aggregation,
        'start_date': start_date,
    }

    return StockInfo(
        code=code,
        time=pd.Timestamp.now(),

        main_df=ma_data,
        ma_rate=ma_rate,
        ma_fitted=ma_fitted,
        fr_stats =fr_stats,
        meta=meta
    )

def add_stockinfo(st1: StockInfo, st2: StockInfo):
    # to add, key parameters and index should match
    if st1.meta != st2.meta:
        raise ValueError('Key parameters mismatch')
    if not st1.main_df.index.equals(st2.main_df.index):
        raise ValueError('main_df index mismatch')
    


# =========================================================
# plotting
# =========================================================
def plot_stockinfo(
    stock_info: StockInfo,
    figsize: tuple = (12, 6),
    use_ltm: bool = False,
):

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(figsize[0], figsize[1] * 1.6),
        sharex=True
    )

    main_df = stock_info.main_df
    ma_fitted = stock_info.ma_fitted
    x = main_df.index

    # =====================================================G
    # COLUMN SELECTION
    # =====================================================
    if use_ltm:
        opincome_col = 'opincome_ltm'
        opmargin_col = 'opmargin_ltm'
        per_col = 'PER_ltm'
        basis_text = "LTM basis"
        income_mult = 1
    else:
        opincome_col = 'opincome'
        opmargin_col = 'opmargin'
        per_col = 'PER'
        basis_text = f"qx4 in {KRW_UNIT_KR[KRW_UNIT]}"
        income_mult = 4

    # =====================================================
    # (1) TOP: MARCAP + AMOUNT
    # =====================================================
    ax1_r = ax1.twinx()

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
        color='gray',
        linestyle='--',
        linewidth=2,
        label='marcap trend',
    )

    bar_width = np.median(np.diff(mdates.date2num(x)))

    ax1_r.bar(
        x,
        main_df['amount'],
        width=bar_width,
        color='orange',
        alpha=0.5,
        label='amount',
    )

    ax1_r.plot(
        x,
        ma_fitted['amount'],
        color='tab:orange',
        linestyle='--',
        linewidth=2,
        label='amount trend',
    )

    # ---- ZERO BASELINE
    ax1.set_ylim(bottom=0)
    ax1_r.set_ylim(bottom=0)

    # ---- slope + recent annotations (RESTORED)
    last_x = x[-1]

    ax1.annotate(
        f"rp:{stock_info.ma_rate.loc['recent_inc', 'marcap']:.0%}",
        xy=(last_x, main_df['marcap'].iloc[-1]),
        xytext=(3, 3),
        textcoords='offset points',
        fontsize = 12, 
    )

    ax1_r.annotate(
        f"ra:{stock_info.ma_rate.loc['recent_inc', 'amount']:.0%}",
        xy=(last_x, main_df['amount'].iloc[-1]),
        xytext=(3, 3),
        textcoords='offset points',
        fontsize = 12, 
    )

    # ---- slope annotations (IMPORTANT RESTORE)
    fit_marcap = ma_fitted['marcap']
    fit_amount = ma_fitted['amount']

    mid_m = len(fit_marcap) // 2
    mid_a = len(fit_amount) // 2

    ax1.annotate(
        f"sp:{stock_info.ma_rate.loc['slope', 'marcap']:,.0f}",
        xy=(fit_marcap.index[mid_m], fit_marcap.iloc[mid_m]),
        xytext=(0, 10),
        textcoords='offset points',
        fontsize = 12, 
    )

    ax1_r.annotate(
        f"sa:{stock_info.ma_rate.loc['slope', 'amount']:,.0f}",
        xy=(fit_amount.index[mid_a], fit_amount.iloc[mid_a]),
        xytext=(0, 10),
        textcoords='offset points',
        fontsize = 12, 
    )

    ax1.set_ylabel(f"MarCap ({KRW_UNIT_KR[KRW_UNIT]} KRW)")
    ax1_r.set_ylabel(f"Amount ({KRW_UNIT_KR[KRW_UNIT]} KRW)")

    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax1_r.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))

    ax1.grid(True, linestyle='--', alpha=0.3)

    # =====================================================
    # (2) BOTTOM: OPINCOME + OPMARGIN + PER
    # =====================================================
    ax2_r = ax2.twinx()

    opincome_raw = main_df[opincome_col]
    opmargin = main_df[opmargin_col]
    per = main_df[per_col]

    # ---- APPLY x4 HERE (FIX #1)
    opincome = opincome_raw * income_mult

    bar_width2 = np.median(np.diff(mdates.date2num(x)))

    # ---- OPINCOME (no gaps possible due to datetime spacing limit)
    ax2.bar(
        x,
        opincome,
        width=bar_width2,
        color='tab:blue',
        alpha=0.6,
        label='opincome',
    )

    # ---- OPMARGIN (visual scaling only)
    scale_factor = opincome.max() if opincome.max() != 0 else 1
    opmargin_scaled = opmargin * scale_factor

    ax2.plot(
        x,
        opmargin_scaled,
        linestyle=':',
        color='red',
        linewidth=3,
        label='opmargin',
    )

    # ---- PER
    ax2_r.plot(
        x,
        per,
        color='purple',
        linewidth=2,
        label='PER',
    )

    # ---- ZERO BASELINE
    ax2.set_ylim(bottom=min(0, opincome.min()))
    ax2_r.set_ylim(bottom=min(0, per.min()))

    # ---- annotations
    ax2.annotate(
        f"{opincome.iloc[-1]:,.0f}",
        xy=(last_x, opincome.iloc[-1]),
        xytext=(5, 0),
        textcoords='offset points',
        fontsize = 12, 
    )

    ax2.annotate(
        f"{opmargin.iloc[-1]:.2f}",
        xy=(last_x, opmargin_scaled.iloc[-1]),
        xytext=(5, 0),
        textcoords='offset points',
        fontsize = 12, 
    )

    ax2_r.annotate(
        f"{per.iloc[-1]:.1f}",
        xy=(last_x, per.iloc[-1]),
        xytext=(5, 0),
        textcoords='offset points',
        fontsize = 12, 
    )

    ax2.set_ylabel(f"Op Income ({KRW_UNIT_KR[KRW_UNIT]} KRW)")
    ax2_r.set_ylabel("PER")
    ax2.grid(True, linestyle='--', alpha=0.3)

    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax2_r.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))

    # ---- TITLE (UPDATED)
    ax2.set_title(
        f"opincome ({basis_text}) | "
        f"opmargin (%) | "
        f"PER (marcap / income)"
    )

    # =====================================================
    # X-AXIS
    # =====================================================
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()

    # =====================================================
    # TOP TITLE
    # =====================================================
    ax1.set_title(
        f"{stock_info.code} | "
        f"{stock_info.time:%Y-%m-%d %H:%M} | "
        f"aggr: {stock_info.meta['aggregation']}"
    )

    # =====================================================
    # LEGENDS (FIX #3)
    # =====================================================
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines1r, labels1r = ax1_r.get_legend_handles_labels()
    ax1.legend(lines1 + lines1r, labels1 + labels1r, loc='upper left')

    lines2, labels2 = ax2.get_legend_handles_labels()
    lines2r, labels2r = ax2_r.get_legend_handles_labels()
    ax2.legend(lines2 + lines2r, labels2 + labels2r, loc='upper left')

    # =====================================================
    # FINAL
    # =====================================================
    plt.tight_layout()
    plt.show()


#%% 
code = '000660'
code = '373220'
aggregation = 'm'
start_date = '2022-03-10'

stockinfo = build_stockinfo(code=code, aggregation=aggregation, start_date=start_date)
fr_data = _get_fr_data(fr_main_db, stockinfo.code)
stockinfo = append_fr_data(stockinfo, fr_data)

# plot_stockinfo(stockinfo)
plot_stockinfo(stockinfo, use_ltm = False)

b = stockinfo

# %%
print(stockinfo.meta)
print(stockinfo.ma_rate)
print(stockinfo.fr_stats)  
print(stockinfo.main_df)
# %%
print(a.main_df.index)
print(b.main_df.index)
add_stockinfo(a, b)



###_ incase opincome is negative, graph should show negative too.
# %%
