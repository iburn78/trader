#%% 
import os
import yaml 
import requests
import pandas as pd
import time

ppd_ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # ../..
df_krx = pd.read_feather(os.path.join(ppd_, 'trader/data_collection/data/df_krx.feather')) 

class Broker:
    def __init__(self, mode='demo'):
        self.mode = mode
        with open(os.path.join(ppd_, 'config/KIS_devlp.yaml'), encoding='UTF-8') as f: 
            _cfg = yaml.load(f, Loader=yaml.FullLoader)
    
        if self.mode == 'prod':
            self.base = 'https://openapi.koreainvestment.com:9443'
            self.key = _cfg['main_app']
            self.sec = _cfg['main_sec']
        elif self.mode == 'demo': 
            self.base = 'https://openapivts.koreainvestment.com:29443'
            self.key = _cfg['paper_app']
            self.sec = _cfg['paper_sec']

        p = {
            "grant_type": "client_credentials",
            "appkey": self.key, 
            "appsecret": self.sec,
        }
        token_url = f"{self.base}/oauth2/tokenP"
        self.token = requests.post(token_url, json=p).json()['access_token']

    # returns last 30 datapoints according to defined period
    def fetch_foreign_ownership(self, code, period): 
        # period: D, W, M
        path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        url = f"{self.base}/{path}"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": self.token,
            "appKey": self.key,
            "appSecret": self.sec,
            "tr_id": "FHKST01010400",
            "tr_cont": "",
        }

        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
            "FID_PERIOD_DIV_CODE":period, 
            "FID_ORG_ADJ_PRC":"0000000000" # modified stock prices
        }

        res = requests.get(url, headers=headers, params=params)
        if res.json()['rt_cd'] == '0' and len(res.json()['output']) > 0:
            res = pd.DataFrame(res.json()['output'])
        else: 
            return None

        type_casting = {'stck_clpr':'int', 'hts_frgn_ehrt':'float'}
        res = res.astype(type_casting).rename(columns={'stck_bsop_date':'date', 'stck_clpr':'price', 'hts_frgn_ehrt':'fo'})
        foreign_ownership = res.set_index('date')[['price', 'fo']].sort_index()
        foreign_ownership.index = pd.to_datetime(foreign_ownership.index, format='%Y%m%d')
        foreign_ownership['code'] = code
        corr = foreign_ownership['price'].corr(foreign_ownership['fo'])

        return foreign_ownership, corr

    def fetch_corr_foreign_ownership(self, code): 
        fo_d, cr_d = self.fetch_foreign_ownership(code, 'D')
        fo_w, cr_w = self.fetch_foreign_ownership(code, 'W')
        fo_m, cr_m = self.fetch_foreign_ownership(code, 'M')
        date = fo_d.index.values[-1]

        return [code, cr_d, cr_w, cr_m, date]

    MARCAP_THRESHOLD = 5000*10**8 
    IPO_YEAR_THRESHOLD = 3 
    
    def generate_corr_data(self, df_krx=df_krx):
        df_krx = df_krx.loc[df_krx['Marcap'] >= Broker.MARCAP_THRESHOLD]
        df_krx = df_krx.loc[pd.Timestamp.today()- df_krx['ListingDate'] > pd.Timedelta(days = Broker.IPO_YEAR_THRESHOLD*(365+1))]
        corr = []
        for code in df_krx.index:
            corr_ = self.fetch_corr_foreign_ownership(code)
            time.sleep(0.1)
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


#%% 
c= Broker('prod')
print(df_krx)
#%% 
d = c.generate_corr_data()
print(d)
