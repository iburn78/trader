import pandas as pd
import FinanceDataReader as fdr
from tools.dc_tools import *

from concurrent.futures import ThreadPoolExecutor
from functools import partial

# parallel download version: 8 request is usually safe
def _fetch(code, START_DATE):
    try:
        print(code)
        res = fdr.DataReader(code, START_DATE)['Close']
        return code, res
    except Exception as e:
        print(f"Error retrieving data for {code}: {e}")
        return None

# parallel download version: 8 request is usually safe
def _initialization(codelist, START_DATE, workers=8) -> tuple:
    price_data = {}

    fetch = partial(_fetch, START_DATE=START_DATE)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = executor.map(fetch, codelist)

        for result in results:
            if result is None:
                continue

            code, res = result
            price_data[code] = res

    pdb = pd.concat(price_data, axis=1)
    return pdb

def get_prices(codelist, START_DATE):
    return _initialization(codelist, START_DATE)

def log_message(message, log_file=None):
    if log_file is not None:
        log_print(log_file, message)
    else:
        print(message)

def update_DB(DB, snapshot, date, column):
    row = snapshot.set_index('Code')[column]
    DB.loc[date, row.index] = row
    return DB

def gen_market_DB(price_DB_path, START_DATE, log_file=None):
    log_message('updating market prices...', log_file)

    market_dates = fdr.DataReader('005930', START_DATE).index
    market_snapshot = fdr.StockListing('KRX')[['Code', 'Market', 'Stocks']]
    market_snapshot = market_snapshot.loc[market_snapshot['Market'].str.contains('KOSPI|KOSDAQ')]
    
    try:
        price_DB = pd.read_feather(price_DB_path)
    except FileNotFoundError:  # Handle if files don't exist
        price_DB = _initialization(market_snapshot['Code'], START_DATE)

    # Get dates to update from last available date in price_DB
    dates_to_update = market_dates[market_dates.get_loc(price_DB.index[-1]):]

    prev_market_snapshot = fdr.StockListing('KRX', dates_to_update[0].strftime('%Y%m%d'))[['Code', 'Market','Stocks']] 
    intersection = pd.merge(prev_market_snapshot, market_snapshot, on=['Code', 'Stocks'], how='inner')
    code_list_to_fully_replace = list(set(market_snapshot['Code']) - set(intersection['Code']))

    for date in dates_to_update:
        # this is only available through CACHE from 2026-03-08
        date_snapshot = fdr.StockListing('KRX', date.strftime('%Y%m%d'))[['Code', 'Market', 'Close', 'Volume', 'Amount', 'Marcap', 'Stocks']] 
        date_snapshot = date_snapshot.loc[date_snapshot['Market'].str.contains('KOSPI|KOSDAQ')]

        price_DB = update_DB(price_DB, date_snapshot, date, 'Close')

    # Replace the entire price/volume data for certain stocks
    for code in code_list_to_fully_replace:
        try:
            res = fdr.DataReader(code, START_DATE)['Close']
            price_DB[code] = res
        except Exception as e:
            print(f"Error retrieving full data for {code}: {e}")
            continue  # Skip if there is an error
    
    # remove delisted
    price_DB = price_DB.dropna(axis=1, subset=[price_DB.index[-1]])

    price_DB = price_DB.astype('float')
    price_DB.to_feather(price_DB_path)

    return True


if __name__ == '__main__': 

    START_DATE = '2014-01-01'

    cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
    log_file = os.path.join(cd_, 'log/data_collect.log')
    price_DB_path = os.path.join(cd_, 'data/price_DB.feather')

    gen_market_DB(price_DB_path, START_DATE, log_file=log_file)

