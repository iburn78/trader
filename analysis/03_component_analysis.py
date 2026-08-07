#%%
from scraper.tools.models import CV_Manager, Component
from trader.analysis.sector_analysis import SectorAnalysis, CodeData


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
# print(sa.main_df)
print(sa.ma_data)
print(sa.fr_data)
#%% 
import pandas as pd

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