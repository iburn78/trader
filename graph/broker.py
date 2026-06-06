#%% 
import os
import yaml 
import requests
import pandas as pd
import time

ppd_ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # ../..
df_krx = pd.read_feather(os.path.join(ppd_, 'trader/data_collect/data/df_krx.feather')) 

class Broker:
    def __init__(self, mode='demo'):
        self.mode = mode
        with open(os.path.join(ppd_, 'config/KIS_devlp.yaml'), encoding='UTF-8') as f: 
            _cfg = yaml.load(f, Loader=yaml.FullLoader)
    
        if self.mode == 'prod':
            self.base = 'https://openapi.koreainvestment.com:9443'
            self.key = _cfg['main_app']
            self.sec = _cfg['main_sec']
            self.sleep_duration = 0.1
        elif self.mode == 'demo': 
            self.base = 'https://openapivts.koreainvestment.com:29443'
            self.key = _cfg['paper_app']
            self.sec = _cfg['paper_sec']
            self.sleep_duration = 0.7

        p = {
            "grant_type": "client_credentials",
            "appkey": self.key, 
            "appsecret": self.sec,
        }
        token_url = f"{self.base}/oauth2/tokenP"

        res = requests.post(token_url, json=p).json()
        self.token = res['access_token'] # 1 access per 1 min

    # returns last 30 datapoints according to defined period
    def fetch_foreign_ownership(self, code, period): 
        # period: D, W, M
        path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        url = f"{self.base}/{path}"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.token}",
            "appkey": self.key,
            "appsecret": self.sec,
            "tr_id": "FHKST01010400",
            "custtype": "P",
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "UN",
            "FID_INPUT_ISCD": code,
            "FID_PERIOD_DIV_CODE": period, 
            "FID_ORG_ADJ_PRC": "1", # modified stock prices
        }

        res = requests.get(url, headers=headers, params=params)
        time.sleep(self.sleep_duration)
        if res.json()['rt_cd'] == '0' and len(res.json()['output']) > 0:
            res = pd.DataFrame(res.json()['output'])
        else: 
            print(f"cannot process {code}: {res.json()}")
            return None

        type_casting = {'stck_clpr':'int', 'hts_frgn_ehrt':'float'}
        res = res.astype(type_casting).rename(columns={'stck_bsop_date':'date', 'stck_clpr':'price', 'hts_frgn_ehrt':'fo'})
        foreign_ownership = res.set_index('date')[['price', 'fo']].sort_index()
        foreign_ownership.index = pd.to_datetime(foreign_ownership.index, format='%Y%m%d')
        foreign_ownership['code'] = code
        # corr logic: 
        corr = foreign_ownership['price'].corr(foreign_ownership['fo'])

        return foreign_ownership, corr

    def fetch_corr_foreign_ownership(self, code): 
        try:
            fo_d, cr_d = self.fetch_foreign_ownership(code, 'D')
            fo_w, cr_w = self.fetch_foreign_ownership(code, 'W')
            fo_m, cr_m = self.fetch_foreign_ownership(code, 'M')
        except:
            return None
        date = fo_d.index.values[-1]
        return [code, cr_d, cr_w, cr_m, date]

    MARCAP_THRESHOLD = 200000*10**8 
    IPO_YEAR_THRESHOLD = 3 
    
    def generate_corr_data(self, df_krx=df_krx):
        df_krx = df_krx.loc[df_krx['Marcap'] >= Broker.MARCAP_THRESHOLD]
        df_krx = df_krx.loc[pd.Timestamp.today()- df_krx['ListingDate'] > pd.Timedelta(days = Broker.IPO_YEAR_THRESHOLD*(365+1))]
        corr = []
        for code in df_krx.index:
            corr_ = self.fetch_corr_foreign_ownership(code)
            if corr_ is None: 
                print(f"skipping {code}")
                continue
            corr_.append(df_krx.loc[code, 'Name'])
            corr.append(corr_)

        corr = pd.DataFrame(corr, columns=['code', 'D', 'W', 'M', 'date', 'name'])
        corr['average'] = corr[['D', 'W', 'M']].mean(axis=1)
        corr['std']= corr[['D', 'W', 'M']].std(axis=1)
        corr.dropna(inplace=True)
        # example usage
        # corr_top = corr.loc[(corr['average'] > 0.7) & (corr['std'] < 0.1)]
        # corr_inv = corr[corr[['w', 'm']].min(axis=1) > 0.7].sort_values('d')
        return corr
    
    def get_div(self, code, start_date, end_date, detail=False): 
        path = "/uapi/domestic-stock/v1/ksdinfo/dividend" # 예탁원정보(배당일정)
        url = f"{self.base}/{path}"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.token}",
            "appkey": self.key,
            "appsecret": self.sec,
            "tr_id": "HHKDB669102C0",
            "custtype": "P",
        }

        params = {
            "CTS" : "",
            "GB1" : "0",
            "F_DT" : start_date, 
            "T_DT" : end_date, 
            "SHT_CD" : code, 
            "HIGH_GB" : "",
        }
        output = requests.get(url, headers=headers, params=params).json()['output1']
        time.sleep(self.sleep_duration)

        res = pd.DataFrame(output)
        if detail: 
            return res
        if len(res) == 0:
            return pd.DataFrame()

        # 기준일, 배당금지급일
        res['record_date'] = pd.to_datetime(res['record_date'], errors='coerce')
        res['divi_pay_dt'] = pd.to_datetime(res['divi_pay_dt'], errors='coerce')

        # 현금배당금, 액면가, 주식배당률(%), 현금배당률(%)
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

    ###_
    def build_div_DB(codelist, div_DB_path = None):

        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config/config.json'), 'r') as json_file:
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
            cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
            div_DB_path = os.path.join(cd_, f'data/div_DB_{end_date}.feather')
        res.to_feather(div_DB_path)
    
    if __name__ == '__main__':
        cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
        df_krx_path = os.path.join(cd_, 'data/df_krx.feather')

        df_krx = pd.read_feather(df_krx_path)
        codelist = df_krx.index
        build_div_DB(codelist)
        print('Building dividend DB is completed')


# usage: 
if __name__ == "__main__":
    broker = Broker('demo')
    corr_data = broker.generate_corr_data()
    print(corr_data)

