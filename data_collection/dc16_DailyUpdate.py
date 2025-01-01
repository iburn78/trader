#%%
import json
from trader.tools.tools import *
import OpenDartReader 
from trader.tools.dictionary import DART_APIS

price_DB_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_collection/data/price_DB.feather')
price_DB = pd.read_feather(price_DB_path)
df_krx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_collection/data/df_krx.feather')
df_krx = pd.read_feather(df_krx_path)

daily_update_file = 'andy/daily_update.json'
ud = dict()
ud['Report date'] = str(nearest_midnight(-1))   

code1 = '011200' #HMM
code1_range = (16000, 18000)
code2 = '294090' #25f
code2_range = (5000, 10000)

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

l1 = get_krx_unique_update_list(dart, yesterday, today)
l7 = get_krx_unique_update_list(dart, one_week_ago, today)
RNK_LIM = 100
lt1 = return_list_within_rank(l1, RNK_LIM, df_krx)
lt7 = return_list_within_rank(l7, RNK_LIM, df_krx)

nl1 = lookup_names_from_codelist(l1, df_krx)
nl7 = lookup_names_from_codelist(l7, df_krx)
nlt1 = lookup_names_from_codelist(lt1, df_krx)
nlt7 = lookup_names_from_codelist(lt7, df_krx)

ud[f'Yesterday changes (top {RNK_LIM})'] = nlt1
ud[f'Last week changes (top {RNK_LIM})'] = nlt7
ud['Yesterday changes'] = nl1
ud['Last week changes'] = nl7

with open(daily_update_file, mode='w', encoding='utf-8') as udf:
    json.dump(ud, udf, indent=4)
