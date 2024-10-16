#%%
import json, sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *
import OpenDartReader 
from tools.dictionary import DART_APIS

def code_desc(pr_DB, code, range): 
    pr_date = pr_DB[code].index[-1]
    price = pr_DB.loc[pr_date, [code]].values[0]
    lb, ub = range
    if (price >= lb) & (price <= ub):
        status = f'price with in range ({lb}, {ub})'
    elif lb > price: 
        status = f'price LOWER than {lb}: need attention!'
    elif price > ub:
        status = f'price HIGHER than {ub}: check'
    else:
        status = f'error - range ({lb}, {ub})' 
    return pr_date.strftime('%Y-%m-%d'), status

price_DB_path = '../data_collection/data/price_DB.feather'
price_DB = pd.read_feather(price_DB_path)
df_krx_path = '../data_collection/data/df_krx.feather'
df_krx = pd.read_feather(df_krx_path)

andy_update_file = 'andy/andy_update.json'
ud = dict()
ud['Report date'] = str(nearest_midnight(-1))

code1 = '011200' #HMM
code1_range = (16000, 18000)
code2 = '294090' #25f
code2_range = (5500, 10000)

ud['# 1'] = "---"
ud['Code 1 date'], ud['Code 1 status'] = code_desc(price_DB, code1, code1_range)

ud['# 2'] = "---"
ud['Code 2 date'], ud['Code 2 status'] = code_desc(price_DB, code2, code2_range)

ud['# 3'] = "---"

dart_ind = 0
dart = OpenDartReader(DART_APIS[dart_ind])

# start_day = '2023-11-14'
# end_day = '2023-11-15'
today_raw = nearest_midnight(-1)
yesterday = (today_raw - pd.Timedelta(days=1)).strftime('%Y-%m-%d')  # Format as 'YYYY-MM-DD'
one_week_ago = (today_raw - pd.Timedelta(weeks=1)).strftime('%Y-%m-%d')  # Format as 'YYYY-MM-DD'
today = today_raw.strftime('%Y-%m-%d')  # Format as 'YYYY-MM-DD'

def get_unique_list(dart, start, end):
    res = dart.list(start=yesterday, end=today, kind='A') # works only withn three month gap between start_day and end_day
    res = res['stock_code'].unique()
    res = res[res.astype(bool)].tolist()
    return res

def lookup_names(codelist, df_krx):
    return [df_krx.loc[x]['Name'] for x in codelist]

def check_within_rank(codelist, RNK_LIM, df_krx):
    df_sorted = df_krx.sort_values(by='Marcap', ascending=True)
    return [i for i in codelist if i in df_krx.index[:RNK_LIM]] 

l1 = get_unique_list(dart, one_week_ago, today)
l7 = get_unique_list(dart, yesterday, today)
RNK_LIM = 100
lt1 = check_within_rank(l1, RNK_LIM, df_krx)
lt7 = check_within_rank(l7, RNK_LIM, df_krx)

nl1 = lookup_names(l1, df_krx)
nl7 = lookup_names(l7, df_krx)
nlt1 = lookup_names(lt1, df_krx)
nlt7 = lookup_names(lt7, df_krx)

ud[f'Yesterday changes (top {RNK_LIM})'] = nlt1
ud[f'Last week changes (top {RNK_LIM})'] = nlt7
ud['Yesterday changes'] = nl1
ud['Last week changes'] = nl7

with open(andy_update_file, mode='w') as udf:
    json.dump(ud, udf, indent=4)

