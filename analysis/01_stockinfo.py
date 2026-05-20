#%%
from dataclasses import dataclass, field
from typing import Literal
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from datetime import datetime
from trader.tools.as_tools import is_KRX_open, load_market_data, get_slope_intercept

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
# data structure: a single stock info or multiple stocks (sector) info
# =========================================================
@dataclass
class StockInfo: 
    codelist: list[str] = field(default_factory=list) 
    time: pd.Timestamp | None = None # creation time 

    main_df: pd.DataFrame | None = None

    # raw data
    ma_data: pd.DataFrame | None = None
    fr_data: pd.DataFrame | None = None

    # ma related: MarCap, Amount
    ma_rates: pd.DataFrame | None = None

    # fr related: PER, OpIncome, OpMargins
    fr_stats: pd.DataFrame | None = None

    meta: dict = field(  
        default_factory=lambda: {
            'unit': None,
            'aggregation': None,
            'start_date': None,
        })

# =========================================================
# handling ma data
# =========================================================
# ma: MarCap, Amount
def get_ma_data(code: str):
    if code not in df_krx.index: 
        raise Exception(f'check code {code}')

    outshares = df_krx.at[code, 'Stocks']
    ma_data = pd.DataFrame({
        'marcap': prices[code] * outshares / KRW_UNIT,
        'amount': volumes[code] * prices[code] / KRW_UNIT,
    })

    # ----------------------------------------------------------------------------
    # if market is open (or at least in early hours), then today record is removed
    # as volume is not a full day data
    # ----------------------------------------------------------------------------
    now = datetime.now()
    if is_KRX_open(now=now):
        ma_data = ma_data[ma_data.index.date != now.date()]

    return ma_data

def _ma_aggregate_periods(ma_data: pd.DataFrame, aggregation: Literal['d', 'w', 'm']):
    """
    aggregate into backward-aligned discrete blocks.
    incomplete oldest block is discarded.

    index: the last days of periods
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
            'last_day': block.index[-1],
            'marcap': marcap,
            'amount': amount,
        })

    return pd.DataFrame(rows).set_index('last_day')

def compute_ma_rates(ma_data: pd.DataFrame):
    rates = pd.DataFrame(
        index=['recent_inc', 'slope', 'intercept'],
        columns=['marcap', 'amount', 'unit'],
    )

    for col in ['marcap', 'amount']:
        rates.loc['recent_inc', col] = ma_data[col][-1] / ma_data[col][-2] - 1

        slope, intercpet = get_slope_intercept(ma_data[col])
        rates.loc['slope', col] = slope
        rates.loc['intercept', col] = intercpet

    rates.loc['recent_inc', 'unit'] = '%'
    rates.loc['slope', 'unit'] = KRW_UNIT_KR[KRW_UNIT]
    rates.loc['intercept', 'unit'] = KRW_UNIT_KR[KRW_UNIT]

    return rates

    # fit_values = intercept + slope*x

    # fitted = pd.DataFrame(index=ma_data.index)
    # fitted[col] = fit_
    
    # # saving fitted values for plots
    # fit_ = pd.Series(
    #     fit_values,
    #     index=s.index,
    # )

# =========================================================
# handling FR data
# =========================================================
# fr_main to code data (CFS or OFS)
def _get_fr_db_for_code(code):
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

# getting rev and opincome data
def get_fr_data(code):
    fr_db_for_code = _get_fr_db_for_code(code)
    row_r = _extract_account_data(fr_db_for_code, 'revenue')
    row_o = _extract_account_data(fr_db_for_code, 'operating_income')
    fr_data = pd.DataFrame({
        'revenue': row_r,
        'opincome': row_o,
    })
    return fr_data

# calc opincome slope and fwd opincome (based on quarterly data)
def _opincome_stats(start_date, fr_data: pd.DataFrame):
    start_idx = max(0, fr_data.index.searchsorted(start_date, side="right") - 1) # side="right" and -1 will give data from the quarter that start_date is in
    opincome = fr_data.iloc[start_idx:]['opincome']

    opincome_slope, _ = get_slope_intercept(opincome)
    fwd_opincome = sum([opincome_slope*i + opincome[-1] for i in [1, 2, 3, 4]])

    return float(opincome_slope), float(fwd_opincome) 

# =========================================================
# stockinfo building
# =========================================================
def build_stockinfo(codelist: list | str, aggregation: Literal['d', 'w', 'm'], fill=False) -> StockInfo:
    if isinstance(codelist, str):
        codelist = [codelist]
    
    for code in codelist:
        ma_data = get_ma_data(code)
        fr_data = get_fr_data(code)

        if ma_data is None or fr_data is None: ###_ review 'or' here
            ma_data = ma_.copy()
            fr_data = fr_.copy()
        else: 
            if fill:
                ma_data = ma_data.add(ma_, fill_value=0) # a copy is returned
                fr_data = fr_data.add(fr_, fill_value=0) 
            else:
                ma_data = ma_data.add(ma_) # do not let nan be added
                fr_data = fr_data.add(fr_)

    meta = {
        'unit': KRW_UNIT,
        'aggregation': aggregation,
        'start_date': start_date,
    }

    res = StockInfo(
        codelist=codelist,
        time=pd.Timestamp.now(),

        main_df=None,
        ma_data=ma_data, 
        fr_data=fr_data,
        ma_rates=None,
        fr_stats =None,
        meta=meta
    )

    res = _compute_stockinfo(res)
    return res

def _compute_stockinfo(stockinfo: StockInfo) -> StockInfo:
    ma_data = stockinfo.ma_data
    fr_data = stockinfo.fr_data

    # ltm: last twelve months
    fr_data['revenue_ltm'] = fr_data['revenue'].rolling(4).sum()
    fr_data['opincome_ltm'] = fr_data['opincome'].rolling(4).sum()
    fr_data['opmargin'] = fr_data['opincome']/fr_data['revenue']
    fr_data['opmargin_ltm'] = fr_data['opincome_ltm']/fr_data['revenue_ltm']

    # combine mr and fr - align dates using reindex
    main_df = ma_data
    main_df[fr_data.columns]=fr_data.reindex(main_df.index, method='ffill')
    ma_rates = compute_ma_rates(main_df)

    # PER: assumes the same 4 quarters 
    main_df['PER'] = main_df['marcap']/(4*main_df['opincome']) # x4 applied here
    main_df['PER_ltm'] = main_df['marcap']/main_df['opincome_ltm']

    # ffill
    main_df = main_df.replace([np.inf, -np.inf], np.nan).ffill().astype('float64')

    opincome_slope, fwd_opincome = _opincome_stats(stockinfo.meta['start_date'], fr_data) # should use fr_data
    PER_fwd = main_df['marcap'].iloc[-1]/fwd_opincome

    fr_stats = pd.DataFrame(
        index=['PER', 'opincome', 'opmargin'],
        columns=['ltm', 'qx4', 'fwd', 'slope', 'unit'],
    )

    _config = {
        'PER': {
            'ltm': main_df['PER_ltm'].iloc[-1],
            'qx4': main_df['PER'].iloc[-1],
            'fwd': PER_fwd,
            'unit': 'times',
        },

        'opincome': {
            'ltm': main_df['opincome_ltm'].iloc[-1],
            'qx4': main_df['opincome'].iloc[-1]*4,
            'fwd': fwd_opincome,
            'slope': opincome_slope,
            'unit': KRW_UNIT_KR[KRW_UNIT],
        },

        'opmargin': {
            'ltm': main_df['opmargin_ltm'].iloc[-1],
            'qx4': main_df['opmargin'].iloc[-1],
            'unit': '%',
        },
    }

    for row, values in _config.items():
        for col, val in values.items():
            fr_stats.loc[row, col] = val

    stockinfo.main_df = main_df
    stockinfo.ma_rates = ma_rates
    stockinfo.fr_stats = fr_stats

    return stockinfo

# =========================================================
# stockinfo operations
# =========================================================

###_ review the following
def add_stockinfo(st1: StockInfo, st2: StockInfo, fill=False):
    # to add, key parameters and index should match
    KEYS = ['unit', 'aggregation', 'start_date']
    meta = {}
    for k in KEYS:
        if st1.meta[k] != st2.meta[k]:
            raise ValueError('Key parameters mismatch')
        meta[k] = st1.meta[k]
    assert st1.main_df is not None 
    assert st2.main_df is not None
    if not st1.main_df.index.equals(st2.main_df.index):
        raise ValueError('main_df index mismatch')
    common = [x for x in st1.codelist if x in set(st2.codelist)]
    if common:
        raise ValueError(f'common codes are found {common} - addition suspended')

    ###_ should handle ma and fr... 
    if fill: 
        main_df=st1.main_df.add(st2.main_df, fill_value=0) # a copy is returned
    else:
        main_df=st1.main_df.add(st2.main_df) # nan stays as nan

    res = StockInfo(
        codelist=st1.codelist + st2.codelist,
        time=max(st1.time, st2.time),

        main_df=main_df,
        ma_rates=None,
        fr_stats =None,
        meta=meta
    )

    res = _compute_stockinfo(res)
    return res

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
    ###_ ma_fitted = stock_info.ma_fitted
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

    # ax1.plot(
    #     x,
    #     ma_fitted['marcap'],
    #     color='gray',
    #     linestyle='--',
    #     linewidth=2,
    #     label='marcap trend',
    # )

    bar_width = np.median(np.diff(mdates.date2num(x)))

    ax1_r.bar(
        x,
        main_df['amount'],
        width=bar_width,
        color='orange',
        alpha=0.5,
        label='amount',
    )

    # ax1_r.plot(
    #     x,
    #     ma_fitted['amount'],
    #     color='tab:orange',
    #     linestyle='--',
    #     linewidth=2,
    #     label='amount trend',
    # )

    # ---- ZERO BASELINE
    ax1.set_ylim(bottom=0)
    ax1_r.set_ylim(bottom=0)

    last_x = x[-1]

    ax1.annotate(
        f"rp:{stock_info.ma_rates.loc['recent_inc', 'marcap']:.0%}",
        xy=(last_x, main_df['marcap'].iloc[-1]),
        xytext=(3, 3),
        textcoords='offset points',
        fontsize = 12, 
    )

    ax1_r.annotate(
        f"ra:{stock_info.ma_rates.loc['recent_inc', 'amount']:.0%}",
        xy=(last_x, main_df['amount'].iloc[-1]),
        xytext=(3, 3),
        textcoords='offset points',
        fontsize = 12, 
    )

    ###_ fit_marcap = ma_fitted['marcap']
    ###_ fit_amount = ma_fitted['amount']

    ###_ mid_m = len(fit_marcap) // 2
    ###_ mid_a = len(fit_amount) // 2

    # ax1.annotate(
    #     f"sp:{stock_info.ma_rates.loc['slope', 'marcap']:,.0f}",
    #     xy=(fit_marcap.index[mid_m], fit_marcap.iloc[mid_m]),
    #     xytext=(0, 10),
    #     textcoords='offset points',
    #     fontsize = 12, 
    # )

    # ax1_r.annotate(
    #     f"sa:{stock_info.ma_rates.loc['slope', 'amount']:,.0f}",
    #     xy=(fit_amount.index[mid_a], fit_amount.iloc[mid_a]),
    #     xytext=(0, 10),
    #     textcoords='offset points',
    #     fontsize = 12, 
    # )

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

    opincome = opincome_raw * income_mult

    bar_width2 = np.median(np.diff(mdates.date2num(x)))

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

    ax2.set_title(
        f"opincome ({basis_text}) | "
        f"opmargin (%) | "
        f"PER (marcap / income)"
    )

    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()

    ax1.set_title(
        f"{stock_info.codelist} | "
        f"{stock_info.time:%Y-%m-%d %H:%M} | "
        f"aggr: {stock_info.meta['aggregation']}"
    )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines1r, labels1r = ax1_r.get_legend_handles_labels()
    ax1.legend(lines1 + lines1r, labels1 + labels1r, loc='upper left')

    lines2, labels2 = ax2.get_legend_handles_labels()
    lines2r, labels2r = ax2_r.get_legend_handles_labels()
    ax2.legend(lines2 + lines2r, labels2 + labels2r, loc='upper left')

    plt.tight_layout()
    plt.show()


#%% 
code = '000660'
code = '005930'
code = '373220'
aggregation = 'm'
start_date = '2020-01-01'

stockinfo = build_stockinfo(codelist=code, aggregation=aggregation, start_date=start_date)
plot_stockinfo(stockinfo, use_ltm = False)
# %%
stockinfo.ma_rates
stockinfo.fr_stats

# 1) rates are wrong when there is nan (lg)
# 2) delte fitted
# 3) ltm and qx4 are the same

# %%


1) make this cleaner
- stockinfo: single stock info
- sectorinfo: multiple stocks info
- mv, fr: merge later / quarterly compuation is mixed up 
- mv, fr can addup
- compute_rates can be applied to any stockinfo or sectorinfo

