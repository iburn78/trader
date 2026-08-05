#%%
from scraper.tools.models import CV_Manager
from trader.analysis.sector_analysis import SectorAnalysis

cvm = CV_Manager()
component = cvm.get_component('Memory')

sa = SectorAnalysis()
sa.from_codelist(component.get_codelist())
sa.get_stats(aggregation='d', start_date='2025-01-01')
sa.plot()
print(sa.ma_rates)
print(sa.fr_rates)

sm = SectorAnalysis()
sm.from_index('KOSPI')
sm.get_stats(aggregation='w', start_date='2025-01-01')
sm.plot()
print(sm.ma_rates)
#%% 
import pandas as pd
import numpy as np

# Beta = Cov(stock returns, market returns) / Var(market returns)
# Alpha = mean(stock returns) − beta × mean(market returns)

def calc_alpha_beta(
    stock: pd.Series,
    market: pd.Series,
    n = 1,
    log_return: bool = False, 
):
    """
    Calculate CAPM alpha and beta of `stock` relative to `market`.

    Parameters
    ----------
    stock : pd.Series
        Stock price series.
    market : pd.Series
        Market index price series.
    log_return : bool
        If True, use log returns. Otherwise use percentage returns.

    Returns
    -------
    alpha : float
        Average return alpha per period.
    beta : float
        CAPM beta.
    """

    df = pd.concat([stock, market], axis=1, join="inner").dropna()
    df.columns = ["stock", "market"]

    if log_return:
        ret = np.log(df / df.shift(1)).dropna()
    else:
        ret = df.pct_change().dropna()

    beta = ret["stock"].cov(ret["market"]) / ret["market"].var()
    alpha = ret["stock"].mean() - beta * ret["market"].mean()

    if log_return:
        alpha = np.exp(alpha*n) - 1
    else:
        alpha = (alpha+1)**n - 1

    return alpha, beta

calc_alpha_beta(sa.ma_data['marcap'], sm.ma_data['index_data'])

