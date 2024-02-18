#%% 
import json
from tools.koreainvest_module import * 
from pprint import pprint
import requests

with open('../config/config.json', 'r') as json_file:
    config = json.load(json_file)
    key = config['key']
    secret = config['secret']
    acc_no = config['acc_no']
    key_mock = config['key_mock']
    secret_mock = config['secret_mock']
    acc_no_mock = config['acc_no_mock']

# broker = mojito.KoreaInvestment(api_key=key, api_secret=secret, acc_no=acc_no, mock=False)
broker = KoreaInvestment(api_key=key_mock, api_secret=secret_mock, acc_no=acc_no_mock, mock=True)

# in mock mode, functionality limit is stricter
# resp = broker.create_market_buy_order("005930", 5) # 삼성전자, 10주, 시장가
# resp = broker.fetch_balance_domestic()
# pprint(resp)

def _fetch_today_1m_ohlcv(broker, symbol: str, to: str):
    """국내주식시세/주식당일분봉조회

    Args:
        symbol (str): 6자리 종목코드
        to (str): "HH:MM:SS"
    """
    base_url = "https://openapivts.koreainvestment.com:29443"
    path = "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
    url = f"{base_url}/{path}"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": broker.access_token,
        "appKey": broker.api_key,
        "appSecret": broker.api_secret,
        "tr_id": "FHKST03010200",
        "tr_cont": "",
    }

    params = {
        "fid_etc_cls_code": "",
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": symbol,
        "fid_input_hour_1": to,
        "fid_pw_data_incu_yn": "Y"
    }
    res = requests.get(url, headers=headers, params=params)
    return res.json()

# resp = broker.fetch_balance_domestic()
# pprint(resp)

#%%
# if __name__ == "__main__":
    # broker_ws = KoreaInvestmentWS(key_mock, secret_mock, ["H0STCNT0", "H0STASP0"], ["005930", "000660"], user_id="iburn78")
    # broker_ws.start()
    # while True:
    #     data_ = broker_ws.get()
    #     if data_[0] == '체결':
    #         print(data_[1])
    #     elif data_[0] == '호가':
    #         print(data_[1])
    #     elif data_[0] == '체잔':
    #         print(data_[1])

#%%

# import sqlite3
# import pandas as pd

# db_path = 'df_krx.db'
# conn = sqlite3.connect(db_path)

# df_krx = pd.read_feather('data_collection/data/df_krx.feather')
# df_krx['ListingDate'] = df_krx['ListingDate'].dt.strftime('%Y-%m-%d')

# df_krx.to_sql('krx_data', conn, if_exists='replace')
# conn.commit()
# conn.close()

