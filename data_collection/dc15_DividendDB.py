#%% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.koreainvest_module import *
import pandas as pd
import time

def get_div(broker, code, start_date, end_date): 
    base_url = "https://openapi.koreainvestment.com:9443"
    path = "/uapi/domestic-stock/v1/ksdinfo/dividend"
    url = f"{base_url}/{path}"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": broker.access_token,
        "appKey": broker.api_key,
        "appSecret": broker.api_secret,
        "tr_id": "HHKDB669102C0",
        "tr_cont": "",
    }

    params = {
        "CTS" : "",
        "GB1" : "0",
        "F_DT" : start_date, 
        "T_DT" : end_date, 
        "SHT_CD" : code, 
        "HIGH_GB" : "",
    }

    time.sleep(0.1)
    print(code)
    output = requests.get(url, headers=headers, params=params).json()['output1']
    res = pd.DataFrame(output)
    if len(res) == 0:
        return pd.DataFrame()
    res['record_date'] = pd.to_datetime(res['record_date'], errors='coerce')
    res['divi_pay_dt'] = pd.to_datetime(res['divi_pay_dt'], errors='coerce')
    type_casting = {'per_sto_divi_amt':'int', 'face_val': 'int', 'stk_divi_rate': 'float', 'divi_rate': 'float'}
    res = res.astype(type_casting)

    # clean na and zero 
    res = res.dropna(subset=['record_date', 'per_sto_divi_amt'])
    res = res[res['per_sto_divi_amt'] !=0 ]
    if len(res) == 0:
        return pd.DataFrame()

    # normalize per_stock_dividend_amount
    res_normalized = res.copy()
    latest_div_idx = res['record_date'].idxmax()
    normalizer = res['face_val']/res.loc[latest_div_idx]['face_val']
    res_normalized['face_val'] = res['face_val']/normalizer
    res_normalized['per_sto_divi_amt'] = res['per_sto_divi_amt']/normalizer

    # add yearly dividend
    res_yearly_sum = res_normalized.groupby(res_normalized['record_date'].dt.year)['per_sto_divi_amt'].sum().reset_index()
    res_yearly_sum.rename(columns={'record_date': 'year', 'per_sto_divi_amt': code}, inplace=True)
    res_yearly_sum.set_index('year', inplace=True)

    return res_yearly_sum

def build_div_DB(codelist, div_DB_path = None):

    with open('../../config/config.json', 'r') as json_file:
        config = json.load(json_file)
        key = config['key']
        secret = config['secret']
        acc_no = config['acc_no']

    broker = KoreaInvestment(api_key=key, api_secret=secret, acc_no=acc_no, mock=False)
    start_date = pd.to_datetime('2014-01-01').strftime('%Y%m%d')
    end_date = pd.to_datetime('now').strftime('%Y%m%d')

    results = [get_div(broker, code, start_date, end_date) for code in codelist]
    res =  pd.concat(results, axis=1)

    if div_DB_path == None:
        div_DB_path = f'data/div_DB_{end_date}.feather' 
    res.to_feather(div_DB_path)
    
if __name__ == '__main__':
    df_krx_path = 'data/df_krx.feather'
    df_krx = pd.read_feather(df_krx_path)
    codelist = df_krx.index
    build_div_DB(codelist)
    print('Building dividend DB is completed')
