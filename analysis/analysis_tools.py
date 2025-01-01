#%%
import os
import FinanceDataReader as fdr
from trader.tools.tools import generate_krx_data
from trader.tools.koreainvest_module import *
import pandas as pd
import time

LANG_DICT = {
    'KRW': '원',
    'K KRW': '천원', '1K KRW': '천원', '1000 KRW': '천원', '1,000 KRW': '천원',
    'M KRW': '백만원', '1M KRW': '백만원', 
    '100M KRW': '억원',
    'B KRW': '십억원', '1B KRW': '십억원', 
    'T KRW': '조원', '1T KRW': '조원', 
    'x': '배수',
    'multiple': '배수',
    'multiples': '배수',
    'foreigner': '외국인',
    'foreigners': '외국인',
    'price': '주가',
    'quarter': '분기',
    'quarters': '분기',
    'revenue': '매출',
    'operating income': '영업이익',
    'net income': '순이익',
    'MarCap': '시총',
    'marcap': '시총',
    'market cap': '시총',
    'IPO': '상장',
}

CONVERT_DICT = {
    'revenue': 'Revenue',
    'operating income': 'Operating Income',
    'net income': 'Net Income',
    'quarters': 'Quarters'
}

QUARTER_START_DATE = '2014-01-01'
RR_TIME_ALLOWANCE = 24*3600
FR_MAIN_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_collection/data/financial_reports_main.feather')
OUTPUT_PLOTS_DIR = 'plots/'
KRX_DATA_FILE = 'data/df_krx.feather'

def retrieve_quarterly_data_code(code, fr_main_path=FR_MAIN_PATH):
    fr_main = pd.read_feather(fr_main_path)
    fh = fr_main.loc[(fr_main['code']==code) & (fr_main['fs_div']=='CFS')].dropna(axis=1, how='all')  # main_DB might have all na columns
    return fh

def gen_output_plot_path_file(prefix=None, suffix=None, filetype='.png', plot_dir = OUTPUT_PLOTS_DIR): 
    fname = ''
    if prefix: fname += prefix +'_'
    fname += pd.Timestamp.now().strftime("%y%m%d_%H%M%S_%f")[:-3]
    if suffix: fname += '_' + suffix
    fname += filetype
    return os.path.join(plot_dir, fname)

def lang_formatter(text, lang = 'K'):
    if lang == 'K':
        return LANG_DICT.get(text, text)
    else:
        return CONVERT_DICT.get(text, text)

# this fucntion is used in ticker.FuncFormatter(), not for general use
def precision_formatter(x, _): 
    if x < 10:
        return round(x,1)
    else: 
        return f'{int(x):,}'

def precision_adjust(x):
    if abs(x) < 0.1:
        x = round(x, 5)
    elif abs(x) < 1: 
        x = round(x, 3)
    elif abs(x) < 100: 
        x = round(x, 1)
    else:
        try:
            x = int(x)
        except:  # in case Inf or NaN
            x = 0
    return x    

def get_last_quarter(fh):
    return max([q for q in fh.columns if 'Q' in q])

def get_quarters(last_quarter, num = 5 ):
    year, quarter = last_quarter.split('_')
    year = int(year)
    quarter = int(quarter[0])  # Convert quarter from '2Q' to 2
    quarters = []
    current_year, current_quarter = year, quarter

    for _ in range(num):
        quarters.append(f"{current_year}_{current_quarter}Q")
        if current_quarter == 1:
            current_quarter = 4
            current_year -= 1
        else:
            current_quarter -= 1
    return quarters[::-1]

def quarter_format(year_short, qr):
    quarter_string = 'Q'
    return str(year_short)+quarter_string+str(qr)

def get_quarter_simpler_string(quarters):
    res = []
    for q in quarters: 
        ys = q[2:4]
        qt = q[5:6]
        res.append(quarter_format(ys,qt))
    return res

def get_last_N_quarter_price(code, qts_back=None, start_date=QUARTER_START_DATE):
    # preparing last N quaters price data
    pr_raw = fdr.DataReader(code, start_date)['Close']
    last_date = pr_raw.index[-1]
    # Calculate the month of the current quarter
    quarter_month = ((last_date.month - 1) // 3) * 3 + 1
    # Calculate the first day of the quarter start_qts_back quarters before last_date
    if qts_back != None: 
        start_date = pd.Timestamp(year=last_date.year, month=quarter_month, day=1) - pd.DateOffset(months=3 * qts_back)
    return pr_raw.loc[start_date:]

# adding rolling last 4 quater values
def L4_addition(fh, target_account):
    new_row = {'code':fh['code'].iloc[0], 'account':'L4_'+target_account }
    quarter_columns = [col for col in fh.columns if 'Q' in col]
    sorted_quarter_columns = sorted(quarter_columns)
    target_row = fh[fh['account']==target_account].iloc[0]

    for i in range(3, len(sorted_quarter_columns)):
        previous_4_quarters = sorted_quarter_columns[i-3:i+1]
        rolling_sum = target_row[previous_4_quarters].sum()
        new_row[sorted_quarter_columns[i]] = rolling_sum

    new_row_df = pd.DataFrame([new_row])
    return pd.concat([fh, new_row_df], ignore_index=True)

def get_shares_outstanding(code): 
    sl = fdr.StockListing('KRX')
    return sl.loc[sl['Code']==code, ['Stocks']].values[0,0]

def get_prev_n_quarter_in_format(quarter, n: int = 1):
    return str(quarter-n).replace('Q','_') + 'Q'

# preparing PER 
# assumption: 
# - performace is immediately known to the market at the end of each quarter
# - for example, when calculating PER, prices (i.e., market cap) of a quarter will be devided by the sum of previous 4 quarters value of net_income
def get_PER_rolling(code, fh, qts_back, target_account='net_income'):
    # target_account='net_income'
    marcap = get_last_N_quarter_price(code, qts_back)*get_shares_outstanding(code)
    PER = pd.Series(index = marcap.index)
    for i in marcap.index:
        q = pd.to_datetime(i).to_period('Q')
        pq = get_prev_n_quarter_in_format(q, 1)
        if pq not in fh.columns:
            pq = get_prev_n_quarter_in_format(q, 2)
        L4 = fh.loc[fh['account']=='L4_'+target_account, [pq]].values[0,0]
        PER[i] = marcap[i] / L4
    return PER

def get_PBR(code, fh, qts_back):
    target_account='equity'
    marcap = get_last_N_quarter_price(code, qts_back)*get_shares_outstanding(code)
    PBR = pd.Series(index = marcap.index)
    for i in marcap.index:
        q = pd.to_datetime(i).to_period('Q')
        pq = get_prev_n_quarter_in_format(q, 1)
        if pq not in fh.columns:
            pq = get_prev_n_quarter_in_format(q, 2)
        divider = fh.loc[fh['account']==target_account, [pq]].values[0,0]
        PBR[i] = marcap[i] / divider
    return PBR

def read_or_regen(data_file, regen_func, time_allowance = RR_TIME_ALLOWANCE, **kwargs):
    if data_file == None: 
        raise Exception('file path should be given')
    if regen_func == generate_krx_data:
        kwargs['sql_db_creation'] = False
    if os.path.exists(data_file):
        last_modified = os.path.getmtime(data_file)
        if time.time() - last_modified <= time_allowance:
            res = pd.read_feather(data_file)
        else:
            res = regen_func(**kwargs)
            res.to_feather(data_file)
    else: 
        res = regen_func(**kwargs)
        res.to_feather(data_file)
    return res

def lookup_name_onetime(code, lang='K', eng_name = None): # for efficiency use this function only for onetime lookup
    if lang == 'K': 
        krx_data_file = KRX_DATA_FILE 
        df_krx = read_or_regen(krx_data_file, generate_krx_data)
        return df_krx.loc[code, 'Name']
    else: 
        if eng_name == None: 
            print('### WARNING: Please give English Name for the company ###')
        return ""

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
    
    output = requests.get(url, headers=headers, params=params).json()
    if 'output' in output: 
        output = output['output']
    else: 
        output = None
    return output

def get_latest_face_value(broker, code):
    res = get_company_info(broker, code)
    if res == None:
        return None
    else: 
        return res['papr']

# use Broker class instead
# def gen_broker():
#     with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config/config.json', 'r') as json_file:
#         config = json.load(json_file)
#         key = config['key']
#         secret = config['secret']
#         acc_no = config['acc_no']

#     broker = KoreaInvestment(api_key=key, api_secret=secret, acc_no=acc_no, mock=False)
#     return broker
    
from trader.data_collection.dc15_DividendDB import *
def get_div_single_company(broker, code): 
    start_date = pd.to_datetime('2014-01-01').strftime('%Y%m%d')
    end_date = pd.to_datetime('now').strftime('%Y%m%d')

    return get_div(broker, code, start_date, end_date, detail=True).dropna(subset=['record_date', 'per_sto_divi_amt', 'face_val'])

# give days in the format of 'yyyymmdd'
# day_from = '20240101'
# day_to = '20240201'
def market_change_analysis(day_from, day_to):
    y_close = fdr.StockListing('KRX', day_from)
    t_close = fdr.StockListing('KRX', day_to)

    y_close_KOSPI = y_close.loc[y_close['Market']=='KOSPI']
    t_close_KOSPI = t_close.loc[t_close['Market']=='KOSPI']

    y_close_KOSDAQ = y_close.loc[y_close['Market']=='KOSDAQ']
    t_close_KOSDAQ = t_close.loc[t_close['Market']=='KOSDAQ']

    res_KOSPI = t_close_KOSPI.merge(y_close_KOSPI[['Code', 'Close', 'Volume', 'Marcap']], on='Code', how='inner', suffixes=('_t', '_y'))
    res_KOSPI = res_KOSPI[['Code', 'Name', 'Marcap_y', 'Marcap_t', 'Close_y', 'Close_t', 'Volume_y', 'Volume_t']]
    type_cast = ['Marcap_y', 'Marcap_t', 'Close_y', 'Close_t', 'Volume_y', 'Volume_t']
    res_KOSPI[type_cast] = res_KOSPI[type_cast].apply(pd.to_numeric, errors='coerce').fillna(0).astype('int64')
    res_KOSDAQ = t_close_KOSDAQ.merge(y_close_KOSDAQ[['Code', 'Close', 'Volume', 'Marcap']], on='Code', how='inner', suffixes=('_t', '_y'))
    res_KOSDAQ = res_KOSDAQ[['Code', 'Name', 'Marcap_y', 'Marcap_t', 'Close_y', 'Close_t', 'Volume_y', 'Volume_t']]
    res_KOSDAQ[type_cast] = res_KOSDAQ[type_cast].apply(pd.to_numeric, errors='coerce').fillna(0).astype('int64')
    res_KOSPI = res_KOSPI.sort_values(by='Marcap_y', ascending=False).reset_index(drop=True)
    res_KOSDAQ = res_KOSDAQ.sort_values(by='Marcap_y', ascending=False).reset_index(drop=True)

    return res_KOSPI, res_KOSDAQ

def market_grouping_anaysis(target_DB):
    # --------------------------------------------------
    # add logic or modify logic of grouping
    # --------------------------------------------------
    target_DB['Group'] = target_DB.index // 100
    # --------------------------------------------------
    # Marcap changes and Volume(price weighted averaged) chages are calculated per group
    # --------------------------------------------------
    group_mc = target_DB.groupby('Group').apply(
        lambda group: (group['Marcap_t'].sum()-group['Marcap_y'].sum())/group['Marcap_y'].sum()*100
    ).reset_index(name='Measure')

    group_vol = target_DB.groupby('Group').apply(
        lambda g: ((g['Volume_t'] * g['Close_t']).sum() - (g['Volume_y'] * g['Close_y']).sum()) / (g['Volume_y'] * g['Close_y']).sum() * 100
    ).reset_index(name='Measure')

    return target_DB, group_mc, group_vol

# target_DB = res_KOSPI or res_KOSDAQ from market_change_analysis function
def top_movements_in_group(target_DB, select_by_marcap = 100):
    target_group = target_DB.iloc[:select_by_marcap].copy()
    target_group['p_increase'] = (target_group['Marcap_t']-target_group['Marcap_y'])/target_group['Marcap_y']*100
    target_group['v_increase'] = (target_group['Volume_t']*target_group['Close_t']-target_group['Volume_y']*target_group['Close_y'])/(target_group['Volume_y']*target_group['Close_y'])*100
    target_group1=target_group.sort_values(by='p_increase', ascending=False)
    price_top_performers = target_group1.iloc[:20]
    price_bottom_performers = target_group1.iloc[-20:]
    target_group2=target_group.sort_values(by='v_increase', ascending=False)
    volume_top_performers = target_group2.iloc[:20]
    volume_bottom_performers = target_group2.iloc[-20:]
    return price_top_performers, price_bottom_performers, volume_top_performers, volume_bottom_performers


