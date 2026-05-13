#%%
from trader.data_collection.dc06_GenPriceDB import get_prices
import pandas as pd
import pickle

with open('CCA/temp/data.pkl', 'rb') as f:
    data_dict = pickle.load(f)

START_DATE = '2024-01-01'
codelist = data_dict['select_codelist']
pdb, vdb = get_prices(codelist, START_DATE)

def inv(start, end, num_stock=10):
    PRINCIPLE_AMOUNT = 10**8
    NUM_STOCKS_TO_INCLUDE = num_stock
    BUY_DAYS_BEFORE = start
    SELL_DAYS_BEFORE = end
    buy_date = pdb.index[-BUY_DAYS_BEFORE]
    sell_date = pdb.index[-SELL_DAYS_BEFORE]
    amt_per_stock = PRINCIPLE_AMOUNT/NUM_STOCKS_TO_INCLUDE

    res = pd.DataFrame(columns = pdb.columns[:NUM_STOCKS_TO_INCLUDE])
    res.loc['buy_price'] = pdb.loc[buy_date]
    res.loc['sell_price'] = pdb.loc[sell_date]
    res.loc['quantity'] = amt_per_stock/pdb.loc[buy_date]
    res.loc['gain'] = (pdb.loc[sell_date]-pdb.loc[buy_date])*res.loc['quantity']
    res = res.astype('int')
    total_gain = round(res.loc['gain'].sum()/PRINCIPLE_AMOUNT*100, 3)
    
    return total_gain
