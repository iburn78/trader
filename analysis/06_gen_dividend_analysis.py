#%%
import pandas as pd

fr_main_path = '../data_collection/data/financial_reports_main.feather'
df_krx_path = '../data_collection/data/df_krx.feather'
price_DB_path = '../data_collection/data/price_DB.feather'
volume_DB_path = '../data_collection/data/volume_DB.feather'
outshare_DB_path = '../data_collection/data/outshare_DB.feather'
div_DB_path = '../data_collection/data/div_DB_20241014.feather'

fr_main = pd.read_feather(fr_main_path)
df_krx = pd.read_feather(df_krx_path)
price_DB = pd.read_feather(price_DB_path)
volume_DB = pd.read_feather(volume_DB_path)
outshare_DB = pd.read_feather(outshare_DB_path)
div_DB = pd.read_feather(div_DB_path)

#%% 

import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from data_collection.dc15_DividendDB import *
code = '002310'
div = get_div_single_company(code)
div = div.dropna(subset=['record_date', 'per_sto_divi_amt', 'face_val'])
face_val_from_div = div['face_val'][0]
print(face_val_from_div)
#%% 

# display(fr_main)
# display(df_krx)
# display(price_DB)
# display(volume_DB)
# display(outshare_DB)
# display(div_DB)

#%% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.koreainvest_module import *
import pandas as pd

def get_company_info(broker, code):
    base_url = "https://openapi.koreainvestment.com:9443"
    path = "/uapi/domestic-stock/v1/quotations/search-stock-info"
    url = f"{base_url}/{path}"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": broker.access_token,
        "appKey": broker.api_key,
        "appSecret": broker.api_secret,
        "tr_id": "CTPF1002R",
        "tr_cont": "",
    }

    params = {
        "PRDT_TYPE_CD" : "300",
        "PDNO" : code,
    }

    output = requests.get(url, headers=headers, params=params).json()['output']
    return output

def gen_broker():
    with open('../../config/config.json', 'r') as json_file:
        config = json.load(json_file)
        key = config['key']
        secret = config['secret']
        acc_no = config['acc_no']

    broker = KoreaInvestment(api_key=key, api_secret=secret, acc_no=acc_no, mock=False)
    return broker

def get_latest_face_value(broker, code):
    return get_company_info(broker, code)['papr']

code = '002310'
broker = gen_broker()

print(get_latest_face_value(broker, code))