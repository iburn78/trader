import numpy as np
import pandas as pd
from collections import deque
import talib as ta

# Stores 20 values and calculates the moving average
# Values are pushed into the queue and the moving average is calculated
class MovingAverage:
    def __init__(self, stock_code, window=20):
        self._stock_code = stock_code
        self._queue = deque(maxlen=window)
        self._prev_ma = None
    
    def __str__(self): 
        return f"{self._stock_code} - Moving Average Strategy: {self._prev_ma}"  

    def push(self, value):
        self._queue.append(value)
        ma = sum(self._queue) / len(self._queue)
        diff = ma - self._prev_ma if self._prev_ma is not None else None
        self._prev_ma = ma

        print(f"{self._stock_code}****** value: {value}, MA: {ma}, diff: {diff}...")

# RSI(Relative Strength Index, 상대강도지수)라는 주가 지표 계산
# RSI는 주식시장에서 가격의 상승압력과 하락압력 간의 상대적 강도를 나타내는 지표로, 주식시장의 상승과 하락의 정도를 나타내는 지표
# RSI가 70 이상이면 과매수 상태, 30 이하이면 과매도 상태로 판단
# RSI가 50 이하이면 매수세가 매도세보다 강하다고 판단
class RSI_ST:   
    def __init__(self, stock_code, window=21):
        self._stock_code = stock_code
        self._queue = deque(maxlen=window)
        self.rsi_period = window
        self.latest_rsi = None
    
    def __str__(self): 
        return f"{self._stock_code} - RSI Strategy: {self.latest_rsi}"

    def eval(self, contract_sub_df):
        dftt = getStreamdDF(self._stock_code, contract_sub_df, convert=False, bar_sz='1Min')
        np_closes = np.array(dftt['STCK_PRPR'], dtype=np.float64)
        rsi = ta.RSI(np_closes, self.rsi_period)

        last_rsi = rsi[-1]
        if last_rsi < 30:
            print(f"({self._stock_code})[BUY] ***RSI: {last_rsi}")    # 통상적으로 RSI가 30 이하면 과매도 상태인 것으로 판단하고 시장이 과도하게 하락했음을 나타냄
        elif last_rsi < 70 and last_rsi >= 30:
            print(f"({self._stock_code})[N/A] ***RSI: {last_rsi}")
        elif last_rsi >= 70:
            print(f"({self._stock_code})[SELL] ***RSI: {last_rsi}")   # 통상적으로 RSI가 70 이상이면 과매수 상태로 간주하고 시장이 과열되었을 가능성이 있음을 나타냄
        else:
            pass
            # print(self._stock_code)
        self.latest_rsi = last_rsi

# streaming data 를 이용해 주어진 bar 크기(예: 1분, 5분 등)의 OHLC(x분봉) 데이터프레임을 반환한다.
# 이때 streaming data 는 websocket client 가 시작한 다음부터 지금까지의 해당 종목의 가격 정보를 의미한다.
# ** 동시호가 시간은 OHLC data 가 모두 NA 가 된다.
def getStreamdDF(stock_code, contract_sub_df, convert = False, bar_sz='1Min'):
    df3 = contract_sub_df.get(stock_code).copy()
    df3 = df3.set_index(['TICK_HOUR'])
    df3['STCK_PRPR'] = pd.to_numeric(df3['STCK_PRPR'], errors='coerce').convert_dtypes()
    if convert:
        df3 = df3['STCK_PRPR'].resample(bar_sz).ohlc() # 1분봉 데이터프레임 생성 using OHLC (Pandas inbuilt function)

    return df3

class BID_ASK_status:
    def __init__(self, stock_code):
        self._stock_code = stock_code
    
    def eval(self, bid_ask_sub_df): 
        _df = bid_ask_sub_df.get(self._stock_code)
        if _df is not None:
            a1 = _df['ASKP1'].iloc[0]  # 매도호가1   
            a2 = _df['ASKP2'].iloc[0]  # 매도호가2   
            b1 = _df['BIDP1'].iloc[0]  # 매수호가1   
            b2 = _df['BIDP2'].iloc[0]  # 매수호가2   
            print(f"({self._stock_code})[BID_ASK] ***ASKP1: {a1}, ASKP2: {a2}, BIDP1: {b1}, BIDP2: {b2}")
            va1 = _df['ASKP_RSQN1'].iloc[0]  # 매도호가1   
            va2 = _df['ASKP_RSQN2'].iloc[0]  # 매도호가2   
            vb1 = _df['BIDP_RSQN1'].iloc[0]  # 매수호가1   
            vb2 = _df['BIDP_RSQN2'].iloc[0]  # 매수호가2   
            print(f"({self._stock_code})[BID_ASK] ***ASKP_RSQN1: {va1}, ASKP_RSQN2: {va2}, BIDP_RSQN1: {vb1}, BIDP_RSQN2: {vb2}")
        else:
            print(f"({self._stock_code})[BID_ASK] ***No data available")