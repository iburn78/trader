#%%
from dataclasses import dataclass, field
from typing import Literal
import numpy as np
import pandas as pd
from functools import reduce
from datetime import datetime
from trader.tools.as_tools import is_KRX_open, load_market_data, get_slope_intercept, KRW_UNIT_KR
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

'''
ma: MarCap (last day), Amount (sum of a period)
outshares: # shares outstanding
volume: # shares traded 
amount: money amount traded (sum of each block)
slope: liear regression over all periods since start_date
recent_inc: comparing between last 2 priods
ltm: last twelve months
'''
df_krx, prices, volumes, fr_main_db = load_market_data()
DEFAULT_KRW_UNIT: float = 1e9 

@dataclass
class CodeData:
    code: str
    time: pd.Timestamp | None = None # creation time

    # daily marcap and volume data
    ma_data: pd.DataFrame | None = None

    # quarterly revenue and opincome data
    fr_data: pd.DataFrame | None = None

    unit: float = DEFAULT_KRW_UNIT

    def __post_init__(self):
        self.time = pd.Timestamp.now()
        self.ma_data = self.get_ma_data()
        self.fr_data = self.get_fr_data()

    # ma: MarCap, Amount in daily basis
    def get_ma_data(self):
        if self.code not in df_krx.index: 
            raise Exception(f'check code {self.code}')

        outshares = df_krx.at[self.code, 'Stocks']
        ma_data = pd.DataFrame({
            'marcap': prices[self.code] * outshares / self.unit,
            'amount': volumes[self.code] * prices[self.code] / self.unit,
        })

        # ----------------------------------------------------------------------------
        # if market is open (or at least in early hours), then today record is removed
        # as volume is not a full day data
        # ----------------------------------------------------------------------------
        now = datetime.now()
        if is_KRX_open(now=now):
            ma_data = ma_data[ma_data.index.date != now.date()]

        return ma_data
    
    # fr: financial records in quarterly basis
    def get_fr_data(self):
        QCOLS = sorted(c for c in fr_main_db.columns if 'Q' in c)
        _quarter_map = {
            '1Q': '01-01',
            '2Q': '04-01',
            '3Q': '07-01',
            '4Q': '10-01',
        }
        DATECOLS = [
            pd.Timestamp(f'{year}-{_quarter_map[q]}')
            for year, q in (col.split('_') for col in QCOLS)
        ]

        # get CFS(consolidated) if not empty
        fr_target = fr_main_db.loc[fr_main_db['code']==self.code]
        fr_db_for_code = fr_target.loc[fr_target['fs_div'] == "CFS"]
        cfs_qcols = fr_db_for_code.loc[(fr_db_for_code['account'] == 'revenue') | (fr_db_for_code['account'] == 'operating_income'), QCOLS]
        if cfs_qcols.isna().all().all():
            fr_db_for_code = fr_target.loc[fr_target['fs_div'] == "OFS"] 

        row_r = fr_db_for_code.loc[fr_db_for_code['account'] == 'revenue', QCOLS].iloc[0].copy() # series
        row_r = (row_r/self.unit).ffill()
        row_r.index = DATECOLS

        row_o = fr_db_for_code.loc[fr_db_for_code['account'] == 'operating_income', QCOLS].iloc[0].copy() # series
        row_o = (row_o/self.unit).ffill()
        row_o.index = DATECOLS
        fr_data = pd.DataFrame({
            'revenue_qtr': row_r,
            'opincome_qtr': row_o,
        })
        return fr_data

class SectorInfo: 
    def __init__(self, codelist: list, unit=None, fill=False):
        if len(set(codelist)) != len(codelist): 
            raise ValueError('non-unique cd_list')

        if unit is not None:
            cd_list = [CodeData(code=code, unit=unit) for code in codelist]
        else: 
            cd_list = [CodeData(code) for code in codelist]

        self.time: pd.Timestamp | None = cd_list[0].time  # codelist creation time
        self.codelist = codelist
        self.ma_data = self._add_dfs([cd.ma_data for cd in cd_list], fill) # daily basis
        self.fr_data = self._add_dfs([cd.fr_data for cd in cd_list], fill) # quarterly basis
        self.meta = {
            'unit': cd_list[0].unit, # KRW unit
        }
    
    def _add_dfs(self, df_list, fill=False):
        return reduce(lambda a, b: a.add(b, fill_value=0 if fill else None), df_list)

    def get_stats(self, aggregation: Literal['d', 'w', 'm'], start_date): # start date in "yyyy-mm-dd" format
        # data is 'aggregated' from 'start_date'
        self.meta['aggregation'] = aggregation
        self.meta['start_date'] = start_date

        self.main_df = self._ma_aggregate_periods(aggregation, start_date)
        self.main_df = self._combine_fr_data()
        self.ma_rates = self._compute_ma_rates()
        self.fr_rates = self._compute_fr_rates(start_date)

    def _ma_aggregate_periods(self, aggregation, start_date):
        # business days in each aggregation
        BLOCK_MAP = {
            'd': 1,
            'w': 5,
            'm': 20,
        }
        """
        aggregate into backward-aligned discrete blocks.
        incomplete oldest block is discarded.

        index: the last days of periods
        """
        if aggregation not in BLOCK_MAP:
            raise ValueError(f'invalid aggregation: {aggregation}')

        block_size = BLOCK_MAP[aggregation]

        # use from start_date
        usable = (len(self.ma_data.loc[start_date:]) // block_size) * block_size

        if usable == 0:
            raise ValueError('not enough rows')

        ma_aggr_data = self.ma_data.iloc[-usable:]

        rows = []
        for start in range(0, usable, block_size):

            block = ma_aggr_data.iloc[start:start + block_size]
            marcap = block['marcap'].iloc[-1]
            amount_subtotal = block['amount'].sum() # Amount is sum over the aggregated period, i.e., subtotal

            rows.append({
                'last_day': block.index[-1],
                'marcap': marcap,
                'amount_subtotal': amount_subtotal,
            })

        return pd.DataFrame(rows).set_index('last_day')

    def _compute_ma_rates(self):
        ma_rates = pd.DataFrame(
            index=['recent_inc', 'slope', 'intercept'],
            columns=['marcap', 'amount_subtotal', 'unit'],
        )

        for col in ['marcap', 'amount_subtotal']:
            ma_rates.loc['recent_inc', col] = self.main_df[col].iloc[-1] / self.main_df[col].iloc[-2] - 1

            slope, intercpet = get_slope_intercept(self.main_df[col])
            ma_rates.loc['slope', col] = slope
            ma_rates.loc['intercept', col] = intercpet

        ma_rates.loc['recent_inc', 'unit'] = '%'
        ma_rates.loc['slope', 'unit'] = KRW_UNIT_KR[self.meta['unit']]
        ma_rates.loc['intercept', 'unit'] = KRW_UNIT_KR[self.meta['unit']]

        return ma_rates
    def _combine_fr_data(self):
        # fr_data preprocess before combine
        _fr_data = self.fr_data.copy()
        _fr_data['revenue_ltm'] = _fr_data['revenue_qtr'].rolling(4).sum()
        _fr_data['opincome_ltm'] = _fr_data['opincome_qtr'].rolling(4).sum()
        _fr_data['opincome_qx4'] = _fr_data['opincome_qtr']*4
        _fr_data['opmargin_qtr'] = _fr_data['opincome_qtr']/_fr_data['revenue_qtr'] # quarterly opmargin
        _fr_data['opmargin_ltm'] = _fr_data['opincome_ltm']/_fr_data['revenue_ltm']

        # align index and combine
        self.main_df[_fr_data.columns]=_fr_data.reindex(self.main_df.index, method='ffill')

        # PER: assumes the same 4 quarters 
        self.main_df['PER_qx4'] = self.main_df['marcap']/self.main_df['opincome_qx4']
        self.main_df['PER_ltm'] = self.main_df['marcap']/self.main_df['opincome_ltm']

        # ffill and return
        return self.main_df.replace([np.inf, -np.inf], np.nan).ffill().astype('float64')

    def _compute_fr_rates(self, start_date):
        # calc opincome slope and fwd opincome (based on quarterly data)
        start_idx = max(0, self.fr_data.index.searchsorted(start_date, side="right") - 1) # side="right" and -1 will give data from the quarter that start_date is in
        opincome = self.fr_data.iloc[start_idx:]['opincome_qtr']

        opincome_slope, _ = get_slope_intercept(opincome)
        fwd_annual_opincome = sum([opincome_slope*i + opincome.iloc[-1] for i in [1, 2, 3, 4]]) # should use quarterly data
        PER_fwd = self.main_df['marcap'].iloc[-1]/fwd_annual_opincome

        fr_rates = pd.DataFrame(
            index=['PER', 'opincome', 'opmargin'],
            columns=['ltm', 'qx4', 'fwd', 'slope', 'unit'],
        )

        _config = {
            'PER': {
                'ltm': self.main_df['PER_ltm'].iloc[-1],
                'qx4': self.main_df['PER_qx4'].iloc[-1],
                'fwd': PER_fwd,
                'unit': 'times',
            },

            'opincome': {
                'ltm': self.main_df['opincome_ltm'].iloc[-1],
                'qx4': self.main_df['opincome_qx4'].iloc[-1],
                'fwd': fwd_annual_opincome,
                'slope': opincome_slope,
                'unit': KRW_UNIT_KR[self.meta['unit']],
            },

            'opmargin': {
                'ltm': self.main_df['opmargin_ltm'].iloc[-1],
                'qx4': self.main_df['opmargin_qtr'].iloc[-1],
                'unit': '%',
            },
        }

        for row, values in _config.items():
            for col, val in values.items():
                fr_rates.loc[row, col] = val

        return fr_rates


    # =========================================================
    # plotting
    # =========================================================
    def plot(self, figsize: tuple = (12, 6), use_ltm: bool = True):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(figsize[0], figsize[1] * 1.6), sharex=True)
        
        x = self.main_df.index
        # =====================================================G
        # COLUMN SELECTION
        # =====================================================
        if use_ltm:
            opincome_col = 'opincome_ltm'
            opmargin_col = 'opmargin_ltm'
            per_col = 'PER_ltm'
            basis_text = f"Annualized by LTM"
        else:
            opincome_col = 'opincome_qx4'
            opmargin_col = 'opmargin_qtr' # quarterly op margin
            per_col = 'PER_qx4' 
            basis_text = f"Annualized by qx4"

        # =====================================================
        # (1) TOP: MARCAP + AMOUNT
        # =====================================================
        ax1_r = ax1.twinx()

        ax1.plot(
            x,
            self.main_df['marcap'],
            color='black',
            linewidth=2,
            label='marcap',
        )

        mc_fitted = self.ma_rates.at['slope', 'marcap']*np.arange(len(x)) + self.ma_rates.at['intercept', 'marcap']
        ax1.plot(
            x,
            mc_fitted,
            color='gray',
            linestyle='--',
            linewidth=2,
            label='marcap trend',
        )

        ax1_r.bar(
            x,
            self.main_df['amount_subtotal'],
            width=max(3, np.median(np.diff(mdates.date2num(x)))), # bar_width
            color='orange',
            alpha=0.5,
            label='amount_subtotal',
        )

        amt_fitted = self.ma_rates.at['slope', 'amount_subtotal']*np.arange(len(x)) + self.ma_rates.at['intercept', 'amount_subtotal']
        ax1_r.plot(
            x,
            amt_fitted,
            color='tab:orange',
            linestyle='--',
            linewidth=2,
            label='amount_subtotal trend',
        )

        # ---- ZERO BASELINE
        ax1.set_ylim(bottom=0)
        ax1_r.set_ylim(bottom=0)

        ax1.annotate(
            f"rp:{self.ma_rates.loc['recent_inc', 'marcap']:.0%}",
            xy=(x[-1], self.main_df['marcap'].iloc[-1]),
            xytext=(-3, 5),
            textcoords='offset points',
            fontsize = 12, 
        )

        ax1_r.annotate(
            f"ra:{self.ma_rates.loc['recent_inc', 'amount_subtotal']:.0%}",
            xy=(x[-1], self.main_df['amount_subtotal'].iloc[-1]),
            xytext=(-3, -5),
            textcoords='offset points',
            fontsize = 12, 
        )

        mid_ = len(x) // 2

        ax1.annotate(
            f"sp:{self.ma_rates.at['slope', 'marcap']:,.0f}",
            xy=(x[mid_], mc_fitted[mid_]),
            xytext=(0, 10),
            textcoords='offset points',
            fontsize = 12, 
        )

        ax1_r.annotate(
            f"sa:{self.ma_rates.at['slope', 'amount_subtotal']:,.0f}",
            xy=(x[mid_], amt_fitted[mid_]),
            xytext=(0, 10),
            textcoords='offset points',
            fontsize = 12, 
        )

        ax1.set_ylabel(f"MarCap ({KRW_UNIT_KR[self.meta['unit']]} KRW)")
        ax1_r.set_ylabel(f"Amount ({KRW_UNIT_KR[self.meta['unit']]} KRW)")

        ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax1_r.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))

        ax1.grid(True, linestyle='--', alpha=0.3)

        # =====================================================
        # (2) BOTTOM: OPINCOME, OPMARGIN, PER
        # =====================================================
        ax2_r = ax2.twinx()

        opincome = self.main_df[opincome_col]
        opmargin = self.main_df[opmargin_col]
        per = self.main_df[per_col]

        bar_width2 = np.median(np.diff(mdates.date2num(x)))

        ax2.bar(
            x,
            opincome,
            width=bar_width2,
            color='tab:blue',
            alpha=0.6,
            label='opincome',
        )

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
            xy=(x[-1], opincome.iloc[-1]),
            xytext=(1, 2),
            textcoords='offset points',
            fontsize = 12, 
        )

        ax2.annotate(
            f"{opmargin.iloc[-1]:.2f}",
            xy=(x[-1], opmargin_scaled.iloc[-1]),
            xytext=(1, 2),
            textcoords='offset points',
            fontsize = 12, 
        )

        ax2_r.annotate(
            f"{per.iloc[-1]:.1f}",
            xy=(x[-1], per.iloc[-1]),
            xytext=(1, 2),
            textcoords='offset points',
            fontsize = 12, 
        )

        ax2.set_ylabel(f"Op Income ({KRW_UNIT_KR[self.meta['unit']]} KRW)")
        ax2_r.set_ylabel("PER")
        ax2.grid(True, linestyle='--', alpha=0.3)

        ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax2_r.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))

        ax2.set_title(
            f"[{basis_text}] opincome | "
            f"opmargin (%) | "
            f"PER (marcap / opincome)"
        )

        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()

        ax1.set_title(
            f"{self.codelist} | "
            f"{self.time:%Y-%m-%d %H:%M} | "
            f"aggr: {self.meta['aggregation']}"
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
code1 = '000660'
code2 = '005930'
code3 = '373220'
codelist = [code1, code2, code3]
codelist = [code3]
aggregation = 'w'
start_date = '2020-01-01'

si = SectorInfo(codelist=codelist)
si.get_stats(aggregation=aggregation, start_date=start_date)
#%%
si.plot()
si.plot(use_ltm=False)
#%%
print(si.ma_rates)
print(si.fr_rates)


# %%
# print(si.main_df)
print(max(si.main_df['amount_subtotal']))
# %%
c = si.main_df['amount_subtotal'].idxmax()
print(si.main_df[c:])
# %%
print(si.main_df)
# %%
# 
# for lg ensol, aggr vol slope is really ?
# 
# align fitted with actual data
# - ployfit already removed na
# - draw properly
# check other stat - impact of na
