#%%
import os, time, random
import pandas as pd
import FinanceDataReader as fdr
import yfinance as yf
import numpy as np

from concurrent.futures import ThreadPoolExecutor
from functools import partial

from yfinance.exceptions import YFRateLimitError

# intention:
# - if fdr makes error: halt by ValueError
# - if yf not exist, then go with fdr
# - if yf exists but the latest date is mismathced: halt by ValueError (run later)

# parallel download version: 8 request is usually safe
def _fetch(code, START_DATE):
    # note: 
    # - fdr_data is more widely available (as it is from KRX), but volume is not split adjusted
    # - yf_data is not available for all, but volume is split adjusted 
    # strategy:
    # - use fdr as basis and whenever possible, update with yf
    # - don't include today for initialization

    END_DATE_fdr = (pd.Timestamp.today().normalize()-pd.Timedelta(days=1)).date() # inclusive
    fdr_data = fdr.DataReader(code, START_DATE, END_DATE_fdr)
    if fdr_data.empty: 
        # then something wrong, start over
        raise ValueError(f'code {code} not available in FDR')
    fdr_data = fdr_data[['Close', 'Volume']]

    tkr = yf.Ticker(code+".KS")
    RETRY_TIME_SEC = 180
    while True:
        try:
            yf_data = tkr.history(start=START_DATE)[['Close', 'Volume']]
            break
        except YFRateLimitError as e:
            print(f'While processing [{code}], yf rate limit hit: {e}')
            print(f'retrying in {RETRY_TIME_SEC} + random secs')
            time.sleep(RETRY_TIME_SEC+random.uniform(0,30))
            print(f'retrying...')

    # use fdr as basis
    res = fdr_data.copy()
    if yf_data.empty:
        # no yf -> use fdr only
        return code, res

    yf_data.index = yf_data.index.tz_localize(None)
    fdr_last = fdr_data.index.max()

    # if fdr_last must exist in yf, otherwise use fdr
    if fdr_last not in yf_data.index:
        print(f'[{code}] Latest FDR date {fdr_last.date()} not in Yahoo. Using fdr only.')
        return code, res

    fdr_close = fdr_data.at[fdr_last, 'Close']
    yf_close  = yf_data.at[fdr_last, 'Close']

    # use Volume from yf if Close is identical in both
    # - allow tiny float error
    if not np.isclose(fdr_close, yf_close, rtol=1e-3):
        print(f'[{code}] Close mismatch on {fdr_last.date()}: fdr={fdr_close}, yf={yf_close}. Using fdr only.')
        return code, res

    res['Volume'] = yf_data['Volume'].reindex(res.index)
    return code, res

# parallel download version: 8 request is usually safe
def initialization(START_DATE, paths, workers=8):
    price_data = {}
    volume_data = {}

    codelist = _get_market_snapshot()['Code']
    fetch = partial(_fetch, START_DATE=START_DATE)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = executor.map(fetch, codelist)
        for result in results:
            code, res = result
            price_data[code] = res['Close']
            volume_data[code] = res['Volume']

    pdb = pd.concat(price_data, axis=1)
    vdb = pd.concat(volume_data, axis=1)

    _save_db(pdb, paths[0])
    _save_db(vdb, paths[1])

def _save_db(db, path):
    # remove delisted
    db = db.dropna(axis=1, subset=[db.index[-1]])

    # float is efficient in NaN handling etc 
    db = db.astype('float')

    db.to_feather(path)

def _update_DB(DB, snapshot, date, column):
    row = snapshot.set_index('Code')[column]
    DB.loc[date, row.index] = row
    return DB

def _get_market_snapshot(date = None):
    if date == None: 
        market_snapshot = fdr.StockListing('KRX')[['Code', 'Market', 'Stocks']]
    else:
        date_req = date.strftime('%Y%m%d')
        market_snapshot = fdr.StockListing('KRX', date_req)[['Code', 'Market', 'Stocks']]

    return market_snapshot.loc[market_snapshot['Market'].str.contains('KOSPI|KOSDAQ')]

def gen_market_DB(paths, START_DATE):
    market_dates = fdr.DataReader('005930', START_DATE).index
    market_snapshot = _get_market_snapshot()

    try:
        price_db = pd.read_feather(paths[0])
        volume_db = pd.read_feather(paths[1])
    except FileNotFoundError:  # Handle if files don't exist
        print('files not found - creating new ones; could take some time')
        initialization(START_DATE=START_DATE, paths=paths)

    # Get dates to update from the last available date in price_db
    # the data in the last date should be updated too (if loaded from file)
    dates_to_update = market_dates[market_dates.get_loc(price_db.index[-1]):]

    prev_market_snapshot = _get_market_snapshot(dates_to_update[0])
    intersection = pd.merge(prev_market_snapshot, market_snapshot, on=['Code', 'Stocks'], how='inner')
    code_list_to_fully_replace = list(set(market_snapshot['Code']) - set(intersection['Code']))

    # Replace the entire price/volume data for certain stocks
    # filled until yesterday
    for code in code_list_to_fully_replace:
        try:
            code, res = _fetch(code, START_DATE)
            price_db[code] = res['Close']
            volume_db[code] = res['Volume']
        except Exception as e:
            print(f"Error retrieving full data for {code}: {e}")
            continue  # Skip if there is an error
    
    # snapshot update should be done after full replaces above
    for date in dates_to_update:
        # this is only available through CACHE from 2026-03-08
        date_req = date.strftime('%Y%m%d')
        # Quick Fix (FDR Error): -------------------------
        if date_req == '20260608': date_req = '20260605'
        # ------------------------------------------------
        date_snapshot = fdr.StockListing('KRX', date_req)[['Code', 'Market', 'Close', 'Volume', 'Amount', 'Marcap', 'Stocks']] 
        date_snapshot = date_snapshot.loc[date_snapshot['Market'].str.contains('KOSPI|KOSDAQ')]

        price_db = _update_DB(price_db, date_snapshot, date, 'Close')
        volume_db = _update_DB(volume_db, date_snapshot, date, 'Volume')
    
    _save_db(price_db, price_db_path)
    _save_db(volume_db, volume_db_path)


if __name__ == '__main__': 
    print("initiating - prices and volumes updates...")
    START_DATE = '2016-01-01'
    cd_ = os.path.dirname(os.path.abspath(__file__)) # .
    price_db_path = os.path.join(cd_, 'data/price_db.feather')
    volume_db_path = os.path.join(cd_, 'data/volume_db.feather')
    paths = [price_db_path, volume_db_path]

    # -------------------------------------
    # if need to initialize, use this
    # -------------------------------------
    # initialization(START_DATE, paths)

    gen_market_DB(paths, START_DATE)

    # price_db = pd.read_feather(paths[0])
    # volume_db = pd.read_feather(paths[1])

    # print(price_db)
    # print(volume_db)

