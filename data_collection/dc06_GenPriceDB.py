# Generate price DB 
# if price_DB and volume_DB are given then updates them, otherwise creates
#%% 
import pandas as pd
import FinanceDataReader as fdr
from trader.tools.tools import *

def _initialization(codelist, START_DATE): 
    price_data = {}
    volume_data = {}

    for code in codelist:
        print(code)
        try:
            res = fdr.DataReader(code, START_DATE)[['Close', 'Volume']]
            price_data[code] = res['Close']
            volume_data[code] = res['Volume']
        except Exception as e:
            print(f"Error retrieving data for {code}: {e}")
            continue  # Skip the code if there's an error

    pdb = pd.concat(price_data, axis=1)
    vdb = pd.concat(volume_data, axis=1)

    return pdb, vdb

def log_message(message, log_file=None):
    if log_file:
        log_print(log_file, message)
    else:
        print(message)

def update_DB(DB, snapshot, date, column):
    date_snapshot = snapshot[['Code', column]].set_index('Code').T
    date_snapshot.index = [date]  
    DB = date_snapshot.combine_first(DB)
    return DB

def gen_market_DB(price_DB_path, volume_DB_path, START_DATE, log_file=None):
    log_message('updating market prices...', log_file)

    market_dates = fdr.DataReader('005930', START_DATE).index
    market_snapshot = fdr.StockListing('KRX')[['Code', 'Market', 'Stocks']]
    market_snapshot = market_snapshot.loc[market_snapshot['Market'].str.contains('KOSPI|KOSDAQ')]
    
    try:
        price_DB = pd.read_feather(price_DB_path)
        volume_DB = pd.read_feather(volume_DB_path)
    except FileNotFoundError:  # Handle if files don't exist
        price_DB, volume_DB = _initialization(market_snapshot['Code'], START_DATE)

    # Get dates to update from last available date in price_DB
    dates_to_update = market_dates[market_dates.get_loc(price_DB.index[-1]):]

    prev_market_snapshot = fdr.StockListing('KRX', dates_to_update[0].strftime('%Y%m%d'))[['Code', 'Market','Stocks']] 
    intersection = pd.merge(prev_market_snapshot, market_snapshot, on=['Code', 'Stocks'], how='inner')
    code_list_to_fully_replace = list(set(market_snapshot['Code']) - set(intersection['Code']))

    for date in dates_to_update:
        date_snapshot = fdr.StockListing('KRX', date.strftime('%Y%m%d'))[['Code', 'Market', 'Close', 'Volume', 'Stocks']] 
        date_snapshot = date_snapshot.loc[date_snapshot['Market'].str.contains('KOSPI|KOSDAQ')]

        # Update all DBs consistently
        price_DB = update_DB(price_DB, date_snapshot, date, 'Close')
        volume_DB = update_DB(volume_DB, date_snapshot, date, 'Volume')

    # Replace the entire price/volume data for certain stocks
    for code in code_list_to_fully_replace:
        try:
            res = fdr.DataReader(code, START_DATE)[['Close', 'Volume']]
            price_DB[code] = res['Close']
            volume_DB[code] = res['Volume']
        except Exception as e:
            print(f"Error retrieving full data for {code}: {e}")
            continue  # Skip if there is an error

    # Ensure data types are correct
    price_DB = price_DB.astype('float')
    volume_DB = volume_DB.astype('float')

    # Save the updated databases
    price_DB.to_feather(price_DB_path)
    volume_DB.to_feather(volume_DB_path)

    return True

def _update_outshare_db(outshare_DB, new_data):
    """Update the outstanding shares database with new data."""
    # Drop rows in outshare_DB that have matching indices in new_data
    outshare_DB = outshare_DB.drop(new_data.index, errors='ignore')

    # Concatenate the new data with the remaining outshare_DB
    outshare_DB = pd.concat([outshare_DB, new_data], axis=0)

    # Optionally, sort by index
    outshare_DB = outshare_DB.sort_index(ascending=True)

    # Ensure data types are correct
    outshare_DB = outshare_DB.astype('float')

    return outshare_DB

def gen_OutstandingShares_DB(outshare_DB_path, START_DATE, log_file=None): 
    log_message('Updating outstanding shares information...', log_file)

    # Get market dates from a reference stock (e.g., Samsung '005930')
    market_dates = fdr.DataReader('005930', START_DATE).index

    # Fetch the initial snapshot of the market
    market_snapshot = fdr.StockListing('KRX')[['Code', 'Market', 'Stocks']]
    market_snapshot = market_snapshot.loc[market_snapshot['Market'].str.contains('KOSPI|KOSDAQ')]
    
    try:
        # Load existing outstanding shares DB
        outshare_DB = pd.read_feather(outshare_DB_path)
        update_start_date = outshare_DB.index[-1]  # Start updating from the last available date
    except FileNotFoundError:  # If the file doesn't exist, create an empty DataFrame
        outshare_DB = pd.DataFrame(index=pd.to_datetime([]))  # Empty DataFrame with DateTime index
        log_message("No existing outstanding shares DB found. Creating a new one...", log_file)
        update_start_date = market_dates[0]  # Set the first market date as the starting point

    # Get the list of dates to update starting from the last available date
    dates_to_update = market_dates[market_dates.get_loc(update_start_date):]

    snapshots = []
    CUT_CHUNK = 150

    for date in dates_to_update:
        log_message(f"Processing outstanding shares data for {date.strftime('%Y-%m-%d')}... {len(snapshots)}/{CUT_CHUNK}", log_file)
        
        # Fetch stock listing data for the specific date
        date_snapshot = fdr.StockListing('KRX', date.strftime('%Y%m%d'))[['Code', 'Market', 'Stocks']]
        date_snapshot = date_snapshot.loc[date_snapshot['Market'].str.contains('KOSPI|KOSDAQ')]

        # Prepare the snapshot for concatenation
        date_snapshot = date_snapshot[['Code', 'Stocks']].set_index('Code').T
        date_snapshot.index = [date]  # Set the current date as the index
        
        # Collect snapshots in a list
        snapshots.append(date_snapshot)

        # Process the snapshots in batches of 100
        if len(snapshots) == CUT_CHUNK:
            new_data = pd.concat(snapshots)
            outshare_DB = _update_outshare_db(outshare_DB, new_data)

            # Save the updated DB to a feather file
            outshare_DB.to_feather(outshare_DB_path)

            # Reset the snapshots list for the next batch
            snapshots = []

    # Concatenate and process any remaining snapshots
    if snapshots:
        new_data = pd.concat(snapshots)
        outshare_DB = _update_outshare_db(outshare_DB, new_data)

        # Save the updated DB to a feather file
        outshare_DB.to_feather(outshare_DB_path)

    return True

if __name__ == '__main__': 
    START_DATE = '2014-01-01'

    cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
    price_DB_path = os.path.join(cd_, 'data/price_DB.feather')
    volume_DB_path = os.path.join(cd_, 'data/volume_DB.feather')
    outshare_DB_path = os.path.join(cd_, 'data/outshare_DB.feather')
    log_file = os.path.join(cd_, 'log/data_collection.log')

    gen_market_DB(price_DB_path, volume_DB_path, START_DATE, log_file=log_file)
    gen_OutstandingShares_DB(outshare_DB_path, START_DATE, log_file)
