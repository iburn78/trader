#%%
from scraper.tools.models import CV_Manager, Component
from trader.analysis.sector_analysis import SectorAnalysis, CodeData
import pandas as pd
from trader.tools.analysis_tools import get_slope_intercept

cvm = CV_Manager()
component: Component = cvm.get_component('Memory')

sa = SectorAnalysis()
sa.from_component(component)
sa.get_stats(aggregation='d', start_date='2025-01-01')
sa.plot()
print(sa.ma_rates)
print(sa.fr_rates)

sm = SectorAnalysis()
sm.from_index('KOSPI')
sm.get_stats(aggregation='d', start_date='2025-01-01')
sm.plot()
print(sm.ma_rates)

OPINCOME_GROWTH_RATE = 0.05 # per period 
OPMARGIN_THRESHOLD = 0.25 
PER_LOW = 7
PER_MED = 12
MEASURE_DURATION = 20 # days 
BASE_DURATION = 120 # days

def build_assess_data(sa: SectorAnalysis):
    if sa.is_index: 
        print('no assess available for index data')
        return False

    # remove ffill duplicates (if exists)
    fr = sa.fr_data.drop_duplicates()
    opic = fr['opincome_qtr']
    rev = fr['revenue_qtr']
    opic_slope = sa.fr_rates.at['opincome', 'slope']
    PER_ltm = sa.main_df['PER_ltm']
    PER_qx4 = sa.main_df['PER_qx4']

    if len(fr) < 5: 
        print('need fr data at least 5 qtrly data points')
        return False

    res = {}
    # ------------------------------------------------------------------
    # opincome_health 
    # ------------------------------------------------------------------
    # check point 1: is opincome for last 4 quarters positive at all 
    c1 = bool((opic.iloc[-4:] > 0).all())

    # check point 2: is latest opincome higher than prev year, quarter 
    c2 = bool(opic.iloc[-1] > max(opic.iloc[-2], opic.iloc[-5]))

    # check point 3: has opincome an upward trend
    c3 = bool(opic_slope > 0)

    # opincome slope over the average of last 4 quarters
    opic_growth = opic_slope / opic.iloc[-4:].mean() 

    res['opincome_health'] = {
        'positive_last_4qtrs': c1, 
        'higher_than_comp': c2, # higher than comparable quarters
        'positive_slope': c3, # measured from start_date given 
        'growth_per_qtr': float(opic_growth),
    }

    ###_
    # bool(opic_growth > OPINCOME_GROWTH_RATE)

    # ------------------------------------------------------------------
    # opmargin 
    # ------------------------------------------------------------------
    # last 4 quarter opmargin
    res['opmargin_last_4qtrs'] = list((opic/rev).iloc[-4:].astype('float'))

    # ------------------------------------------------------------------
    # PER_ltm L, M, H
    # ------------------------------------------------------------------
    # if PER_ltm.iloc[-1] <= PER_LOW: l = "L"
    # elif PER_ltm.iloc[-1] <= PER_MED: l = "M"
    # else: l = "H"
    res['PER'] = {
        'PER_ltm': float(PER_ltm.iloc[-1]), 
        'per_qx4': float(PER_qx4.iloc[-1]),
    }

    # ------------------------------------------------------------------
    # Development_path: Volatility and Amount increment
    # ------------------------------------------------------------------
    # Rolling volatility:
    res['volatility_rolling_pct'] = calc_increment(sa.ma_data['marcap'].pct_change().rolling(MEASURE_DURATION).std().dropna())
    # Amount:
    res['amount_daily'] = calc_increment(sa.ma_data['amount_daily'])

    return res

def calc_increment(s: pd.Series, measure_duration=MEASURE_DURATION, base_duration=BASE_DURATION): 
    # default values: 
    # - measure_duration: 20 (1 months)
    # - base_duration: 120 (6 months, required length)
    # return: [measure to base (exclusive), slope]

    s = s.dropna()
    s = s[s != 0] # dropping zeros too (e.g., suspended days etc)

    slope, intercept = get_slope_intercept(s[-base_duration:-measure_duration])

    # define floor: 
    _min = min(s[-base_duration:])*0.7

    extrapolated_value = max(intercept + slope*(base_duration-measure_duration/2), _min)
    measure_duration_average = s[-measure_duration:].mean()

    measure_to_base_ratio = measure_duration_average/extrapolated_value
    # if ratio > 2: res = 'High'
    # elif ratio > 1: res = 'Up'
    # elif ratio > 0.5: res = 'Down'
    # else: res = 'Low'

    return [float(measure_to_base_ratio), float(slope)]

def calc_alpha_beta(
    stock: pd.Series, # price or marcap
    market: pd.Series, # index or marcap
    n = 1,
):
    """
    alpha : float
        Average return alpha per period if n = 1
        if n > 1, then the result is for n-period return 
    beta : float
        CAPM beta
    """

    df = pd.concat([stock, market], axis=1, join="inner").dropna()
    df.columns = ["stock", "market"]

    ret = df.pct_change().dropna()

    beta = ret["stock"].cov(ret["market"]) / ret["market"].var()
    _alpha = ret["stock"].mean() - beta * ret["market"].mean()
    alpha = (_alpha+1)**n - 1

    return float(alpha), float(beta)

calc_alpha_beta(sa.ma_data['marcap'], sm.ma_data['index_data'])


#%%
print(sa.main_df)
print(build_assess_data(sa))
# %%
