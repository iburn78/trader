from datetime import datetime, time
from zoneinfo import ZoneInfo
import holidays
from pathlib import Path
import pandas as pd
import numpy as np
import FinanceDataReader as fdr

KRW_UNIT_KR = {
    1e12: 'jo',
    1e9: '10-uk',
    1e8: 'uk', 
}

def load_market_data():
    BASE_DIR = Path(__file__).resolve().parents[1]
    DATA_DIR = BASE_DIR / 'data_collection' / 'data'

    PRICE_DB_PATH = DATA_DIR / 'price_DB.feather'
    VOLUME_DB_PATH = DATA_DIR / 'volume_DB.feather'

    FRM1_PATH = DATA_DIR / 'financial_reports_main1.feather'
    FRM2_PATH = DATA_DIR / 'financial_reports_main2.feather'
    FRM3_PATH = DATA_DIR / 'financial_reports_main3.feather'

    df_krx = gen_df_krx()
    prices = pd.read_feather(PRICE_DB_PATH)
    volumes = pd.read_feather(VOLUME_DB_PATH)
    frm1 = pd.read_feather(FRM1_PATH)
    frm2 = pd.read_feather(FRM2_PATH)
    frm3 = pd.read_feather(FRM3_PATH)
    fr_main_db = pd.concat([frm1, frm2, frm3], axis=0)

    return df_krx, prices, volumes, fr_main_db

# not heavy, always rebuild
def gen_df_krx():
    df_krx = fdr.StockListing('KRX')[['Code', 'Name', 'Market', 'Close', 'Volume', 'Amount', 'Marcap', 'Stocks']].set_index('Code')
    df_krx = df_krx.loc[df_krx['Market'].str.contains('KOSPI|KOSDAQ')]
    return df_krx

def is_KRX_open(now=None, strict=False):
    """
    Returns True if KRX regular market is open now.
    
    Rules:
    - Mon~Fri
    - Not Korean public holiday
    - 09:00 ~ 15:30 KST 
    - or ~ 12:00 KST (not strict)
    """

    KR_HOLIDAYS = holidays.KR()
    kst = ZoneInfo("Asia/Seoul")

    if now is None:
        now = datetime.now(kst)
    else:
        now = now.astimezone(kst)

    today = now.date()

    # Weekend
    if now.weekday() >= 5:
        return False

    # Korean holiday
    if today in KR_HOLIDAYS:
        return False

    market_open = time(9, 0)
    if strict:
        market_close = time(15, 30)
    else:
        market_close = time(12, 00)

    return market_open <= now.time() < market_close

def get_slope_intercept(s: pd.Series):
    s = s.dropna()
    x = np.arange(len(s))
    y = s.values

    slope, intercept = np.polyfit(x,y,1)  
    return slope, intercept