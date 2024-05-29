#%%
import pandas as pd
import FinanceDataReader as fdr

# parameters
c = 3 # the current period (months)
p = 12 # the previous period to the current period (months)
r = 0.4 # ratio; 1-r = drop rate
m = 2 # multiples of std-deviations

baseDate = pd.Timestamp.today()
c_start = (baseDate - pd.DateOffset(months=c)).strftime("%Y-%m-%d")
c_end = baseDate.strftime("%Y-%m-%d")
p_start = (baseDate - pd.DateOffset(months=c+p)).strftime("%Y-%m-%d")
p_end = (baseDate - pd.DateOffset(months=c, days=1)).strftime("%Y-%m-%d")

code_list = fdr.StockListing('KRX')['Code']

def drop_enough(code, c_start = c_start, c_end = c_end, p_start = p_start, p_end = p_end, r=r, m=m):
    c_prices = fdr.DataReader(code , c_start, c_end)['Close']
    p_prices = fdr.DataReader(code, p_start, p_end)['Close']

    ac = c_prices.mean()
    sc = c_prices.std()
    ap = p_prices.mean()
    sp = p_prices.std()

    if ac/ap <= r and (ap-ac >= m*(sc+sp)): 
        return True, [code, ac, sc, ap, sp]
    else: 
        return False, [code, ac, sc, ap, sp]

#%%

passed = []
stats = []
for code in code_list[100:300]:
    print(code)
    r, res = drop_enough(code)
    if r:
        passed.append(code)
    stats.append(res)

summary = pd.DataFrame(stats, columns = ['code', 'ac', 'sc', 'ap', 'sp'])
(summary['ap']-summary['ac']).plot()
print(passed)

