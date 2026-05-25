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


# local gemma4 (installed via ollama)
# standard way to call an local model (using openai template)
from openai import OpenAI
import base64, mimetypes

client = OpenAI(
    base_url="http://localhost:11434/v1", # ollama
    api_key="dummy"
)

def get_local_response(input_text, image_file=None, client=client, model="gemma4"):
    content = [{
        "type": "text",
        "text": input_text,
    }]
    if image_file is not None:
        with open(image_file, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
        mime_type, _ = mimetypes.guess_type(image_file)
        mime_type = mime_type or "image/png"
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{image_b64}",
            }
        })

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ]
    )

    return response.choices[0].message.content
