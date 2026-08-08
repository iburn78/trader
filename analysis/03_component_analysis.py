#%%
from scraper.tools.models import CV_Manager, Component
from trader.analysis.sector_analysis import SectorAnalysis, CodeData
import pandas as pd

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

OPINCOME_GROWTH_RATE = 0.05 # per period 
OPMARGIN_THRESHOLD = 0.25 

def assess(sa):
    if sa.is_index: 
        print('no assess available for index data')
        return False

    # remove ffill duplicates (if exists)
    fr = sa.fr_data.drop_duplicates()
    opic = fr['opincome_qtr']
    rev = fr['revenue_qtr']
    opic_slope = sa.fr_rates.at['opincome', 'slope']

    if len(fr) < 5: 
        print('need fr data at least 5 qtrly data points')
        return False

    # logic 1: is opincome for last 4 quarters positive at all
    logic_1 = (opic.iloc[-4:] > 0).all()

    # logic 2: is latest opincome higher than prev year, quarter
    logic_2 = opic.iloc[-1] > max(opic.iloc[-2], opic.iloc[-5])

    # logic 3: has opincome an upward trend
    logic_3 = opic_slope > 0

    # logic 4: is opincome groth sufficiently strong
    logic_4 = opic_slope / opic.iloc[-4:].mean() > OPINCOME_GROWTH_RATE

    # logic 5: is opmargin high enough 
    logic_5 = ((opic/rev).iloc[-4:] > OPMARGIN_THRESHOLD).all()

    return [logic_1, logic_2, logic_3, logic_4, logic_5]



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