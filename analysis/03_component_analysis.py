#%%
from scraper.tools.models import CV_Manager, Component
from trader.analysis.sector_analysis import SectorAnalysis, CodeData
import pandas as pd
from trader.tools.analysis_tools import is_KRX_open, load_market_data, get_slope_intercept, KRW_UNIT_KR

c = CodeData('000660')
print(c)
#%% 
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
#%%

# sa.main_df
assess(sa)
#%% 

OPINCOME_GROWTH_RATE = 0.05 # per period 
OPMARGIN_THRESHOLD = 0.25 
PER_LOW = 7
PER_MED = 12

def assess(sa: SectorAnalysis):
    if sa.is_index: 
        print('no assess available for index data')
        return False

    # remove ffill duplicates (if exists)
    fr = sa.fr_data.drop_duplicates()
    opic = fr['opincome_qtr']
    rev = fr['revenue_qtr']
    opic_slope = sa.fr_rates.at['opincome', 'slope']
    PER_ltm = sa.main_df['PER_ltm']

    if len(fr) < 5: 
        print('need fr data at least 5 qtrly data points')
        return False

    res = {}
    # ------------------------------------------------------------------
    # opincome_generating 
    # ------------------------------------------------------------------
    # check point 1: is opincome for last 4 quarters positive at all 
    c1 = (opic.iloc[-4:] > 0).all()

    # check point 2: is latest opincome higher than prev year, quarter 
    c2 = opic.iloc[-1] > max(opic.iloc[-2], opic.iloc[-5])

    # check point 3: has opincome an upward trend
    c3 = opic_slope > 0

    if c1 and c2 and c3: res['opincome_generating'] = True
    else: res['opincome_generating'] = False

    # ------------------------------------------------------------------
    # opincome_growth_high 
    # ------------------------------------------------------------------
    # opincome slope over last 4 quarter opincome average
    res['opincome_growth_high'] = bool(opic_slope / opic.iloc[-4:].mean() > OPINCOME_GROWTH_RATE)

    # ------------------------------------------------------------------
    # opmargin_high_enough 
    # ------------------------------------------------------------------
    # last 4 quarter opmargin average
    res['opmargin_high'] = bool(((opic/rev).iloc[-4:] > OPMARGIN_THRESHOLD).all())

    # ------------------------------------------------------------------
    # PER_ltm L, M, H
    # ------------------------------------------------------------------
    if PER_ltm.iloc[-1] <= PER_LOW: l = "L"
    elif PER_ltm.iloc[-1] <= PER_MED: l = "M"
    else: l = "H"
    res['PER_ltm'] = l

    # ------------------------------------------------------------------
    # Development_path: Volatility and Amount increment
    # ------------------------------------------------------------------
    # Volatility: ?
    # Amount increment: last period(?) amount over average, generally increaing?
    

    return res

#%% 
def calc_increment(s: pd.Series, measure_duration = 20, base_duration = 120): 
    # default values: 
    # - measure_duration: 20 (1 months)
    # - base_duration: 120 (6 months, required length)

    s = s.dropna()
    s = s[s != 0] # dropping zeros too (e.g., suspended days etc)

    slope, intercept = get_slope_intercept(s[-base_duration:-measure_duration])

    # define floor: 
    _min = min(s[-base_duration:])*0.7

    extrapolated_value = max(intercept + slope*(base_duration-measure_duration/2), _min)
    measure_duration_average = s[-measure_duration:].mean()

    ratio = measure_duration_average/extrapolated_value
    if ratio > 2: res = 'High'
    elif ratio > 1: res = 'Up'
    elif ratio > 0.5: res = 'Down'
    else: res = 'Low'

    return ratio, slope, res
    
# volatility   
###_ is rolling correct? 
###_ is comparing to trend is correct?
a = calc_increment(sa.ma_data['marcap'].pct_change().rolling(20).std().dropna(), 1, 100)
print(a)
# amount 
b = calc_increment(sa.ma_data['amount_daily'])
print(b)

#%%

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
print(sa.fr_rates)