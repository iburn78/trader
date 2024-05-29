#%%
import pandas as pd
import FinanceDataReader as fdr

START_DATE = '2014-01-01'
market_dates = fdr.DataReader('005930', START_DATE).index

def initialization(codelist): 
    price_data = {}
    for i, code in enumerate(codelist):
        print(i, code)
        res = fdr.DataReader(code, START_DATE)['Close']
        res.name = code
        price_data[code] = res
    return pd.concat(price_data, axis=1)

market_snapshot = fdr.StockListing('KRX')[['Code', 'Market', 'Close', 'Stocks']]
market_snapshot = market_snapshot.loc[market_snapshot['Market'].str.contains('KOSPI|KOSDAQ')]

try: 
    price_DB = pd.read_feather('data/price_DB.feather')
except:
    price_DB = initialization(market_snapshot['Code'])

dates_to_update = market_dates[list(market_dates).index(price_DB.index[-1]):]

prev_market_snapshot = fdr.StockListing('KRX', dates_to_update[0].strftime('%Y%m%d'))[['Code', 'Market', 'Close', 'Stocks']] 
intersection = pd.merge(prev_market_snapshot, market_snapshot, on=['Code', 'Stocks'], how='inner')
code_list_to_fully_replace = list(set(market_snapshot['Code'])-set(intersection['Code']))

for date in dates_to_update:
    date_snapshot = fdr.StockListing('KRX', date.strftime('%Y%m%d'))[['Code', 'Market', 'Close', 'Stocks']] 
    date_snapshot = date_snapshot.loc[date_snapshot['Market'].str.contains('KOSPI|KOSDAQ')]
    date_snapshot = date_snapshot[['Code', 'Close']].set_index('Code')
    date_snapshot.columns = {date}
    date_snapshot = date_snapshot.T
    price_DB = price_DB.join(date_snapshot[date_snapshot.columns.difference(price_DB.columns)], how='outer')
    price_DB.update(date_snapshot)

for code in code_list_to_fully_replace:
    res = fdr.DataReader(code, START_DATE)['Close']
    res.name = code
    price_DB[code] = res

price_DB=price_DB.astype('float')
price_DB.to_feather('data/price_DB.feather')

print('success...')

