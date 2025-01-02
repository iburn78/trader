#%% 
from trader.tools.tools import generate_krx_data
from trader.tools.koreainvest_module import *
from trader.analysis.analysis_tools import *

class Broker:
    def __init__(self):
        self.broker = self.get_broker()

    def get_broker(self, mock=False):
        ppd_ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # ../..
        with open(os.path.join(ppd_, 'config/config.json'), 'r') as json_file:
            config = json.load(json_file)
            if mock:
                # key_mock = config['key_mock']
                # secret_mock = config['secret_mock']
                # acc_no_mock = config['acc_no_mock']
                # broker = KoreaInvestment(api_key=key_mock, api_secret=secret_mock, acc_no=acc_no_mock, mock=True)
                pass
            else: 
                key = config['key']
                secret = config['secret']
                acc_no = config['acc_no']
                broker = KoreaInvestment(api_key=key, api_secret=secret, acc_no=acc_no, mock=False)
        return broker

    # returns last 30 datapoints according to defined period
    def fetch_foreign_ownership(self, code, period): 
        # period: D, W, M
        base_url = "https://openapi.koreainvestment.com:9443"
        path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        url = f"{base_url}/{path}"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": self.broker.access_token,
            "appKey": self.broker.api_key,
            "appSecret": self.broker.api_secret,
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
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .. 
    KRX_DATA_FILE = os.path.join(pd_, 'data_collection/data/df_krx.feather')

    def generate_corr_data(self, krx_data_file=KRX_DATA_FILE):
        df_krx = read_or_regen(krx_data_file, generate_krx_data)
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