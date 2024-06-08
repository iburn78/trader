#%%
import pandas as pd

# parameters
c = 1 # the current period (months)
p = 1 # the previous period to the current period (months)
r = 0.5 # ratio; 1-r = drop rate
m = 0 # multiples of std-deviations

baseDate = pd.Timestamp.today().normalize()
c_start = (baseDate - pd.DateOffset(months=c))
c_end = baseDate
p_start = (baseDate - pd.DateOffset(months=c+p))
p_end = (baseDate - pd.DateOffset(months=c, days=1))
price_DB = pd.read_feather('data/price_DB.feather')

def drop_enough(prices):
    c_prices = prices.loc[(prices.index >= c_start) & (prices.index <= c_end)]
    p_prices = prices.loc[(prices.index >= p_start) & (prices.index <= p_end)]

    ac = c_prices.mean()
    sc = c_prices.std()
    ap = p_prices.mean()
    sp = p_prices.std()

    if (ac/ap <= r) and ((ap-ac)>= m*(sc+sp)): 
        return True, [ac, sc, ap, sp]
    else: 
        return False, [ac, sc, ap, sp]

passed = []
stats = []
for code in price_DB.columns:
    tf, res = drop_enough(price_DB[code])
    if tf:
        passed.append(code)
    stats.append([code] + res)

summary = pd.DataFrame(stats, columns = ['code', 'ac', 'sc', 'ap', 'sp'])
print(summary)
print(passed)
