#%% 
import websockets  
import asyncio
import kis_auth as ka 
import kis_domstk as kb
import yaml
import pandas as pd
import numpy as np
import datetime
from io import StringIO
from collections import deque
import talib as ta
import nest_asyncio
from ws_tools import *


# Allow nested event loops in Jupyter Notebook
nest_asyncio.apply()

# ----------------------------------------------
# -- Auth and Config
# ----------------------------------------------
ka.auth(svr='prod')  # 인증서버 선택 (prod:운영, vps:개발)

with open(ka.config_root + 'kis_devlp.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
    HTS_ID = _cfg['hts_id']

__today__ = datetime.date.today().strftime("%Y%m%d")
__DEBUG__ = True  
_connect_key = get_approval()  # websocker 연결Key
_iv = None  # for 복호화
_ekey = None  # for 복호화


# ----------------------------------------------
# -- Analysis targets
# ----------------------------------------------
target_stocks = ('009540', '012630', '052300', '089860', '218410', '330590', '357550', '419080', '348370')



# ----------------------------------------------
# -- Data Structure
# ----------------------------------------------
contract_sub_df = dict()  # 실시간 국내주식 체결 결과를 종목별로 저장하기 위한 container
tr_plans = dict()         # 실시간 국내주식 체결 값에 따라 무언가를 수행할 Class 를 저장하기 위한 container
bid_ask_sub_df = dict()   # 실시간 국내주식 호가 결과를 종목별로 저장하기 위한 container
ba_plans = dict()         # 실시간 국내주식 호가 값에 따라 무언가를 수행할 Class 를 저장하기 위한 container
executed_df = pd.DataFrame(data=None, columns=contract_cols)  # 체결통보 저장용 DF

# ----------------------------------------------
# -- Custom Strategy Implementation
# ----------------------------------------------
# Stores 20 values and calculates the moving average
# Values are pushed into the queue and the moving average is calculated
class BasicPlan:
    def __init__(self, stock_code, window=20):
        self._stock_code = stock_code
        self._queue = deque(maxlen=window)
        self._prev_ma = None

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

    def eval(self):
        dftt = getStreamdDF(self._stock_code, convert=False, bar_sz='1Min')
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
            print(self._stock_code)

# streaming data 를 이용해 주어진 bar 크기(예: 1분, 5분 등)의 OHLC(x분봉) 데이터프레임을 반환한다.
# 이때 streamign data 는 websocket client 가 시작한 다음부터 지금까지의 해당 종목의 가격 정보를 의미한다.
# ** 동시호가 시간은 OHLC data 가 모두 NA 가 된다.
def getStreamdDF(stock_code, convert = False, bar_sz='1Min'):
    df3 = contract_sub_df.get(stock_code).copy()
    df3 = df3.set_index(['TICK_HOUR'])
    df3['STCK_PRPR'] = pd.to_numeric(df3['STCK_PRPR'], errors='coerce').convert_dtypes()
    if convert:
        df3 = df3['STCK_PRPR'].resample(bar_sz).ohlc() # 1분봉 데이터프레임 생성 using OHLC (Pandas inbuilt function)

    return df3

def register_contract_based_strategy(stock_code):
    tr_plans[stock_code] = BasicPlan(stock_code)  # 이동 평균선 계산 (웹소켓 프로그램 실행시 수집된 데이터만 반영)  
    ba_plans[stock_code] = RSI_ST(stock_code)  # RSI(Relative Strength Index, 상대강도지수)라는 주가 지표 계산

def register_bid_ask_based_strategy(stock_code):
    pass

def contract_pr_triggered_actions(stock_code, dp_):
    val1 =  dp_['STCK_PRPR'].tolist()[0]
    tr_plans[stock_code].push(int(val1))  # 이동평균값 활용
    ba_plans[stock_code].eval()         # RSI(Relative Strength Index, 상대강도지수)라는 주가 지표 계산 활용

def bid_ask_triggered_actions(stock_code):
    pass

async def execution_based_actions():
    for writer in connected_clients:
        try:
            await write_pickle(writer, executed_df)
        except websockets.ConnectionClosed:
            print("Connection closed while sending notice")

def independent_actions(): 
    pass
    # [국내주식] 주문/계좌 > 매수가능조회 (종목번호 5자리 + 종목단가) REST API
    # rt_data = kb.get_inquire_psbl_order(pdno=stock_code, ord_unpr=val1)
    # ord_qty = rt_data.loc[0, 'nrcvb_buy_qty']  # nrcvb_buy_qty	미수없는매수수량
    # print("[미수없는매수주문가능수량!] : " + ord_qty)

    # 국내주식 현금 주문
    # rt_data = kb.get_order_cash(ord_dv="buy",itm_no=stock_code, qty=ord_qty, unpr=val1)
    # print(rt_data.KRX_FWDG_ORD_ORGNO + "+" + rt_data.ODNO + "+" + rt_data.ORD_TMD) # 주문접수조직번호+주문접수번호+주문시각
    # print("매수/매도 조건 주문 : " + val1)

async def generate_notice(): 
    ind = 0
    while True:
        await asyncio.sleep(60)
        ind += 1
        notice = {"message": f"connected: {ind}min"}
        for writer in connected_clients:
            try:
                await write_pickle(writer, notice)
            except websockets.ConnectionClosed:
                print("Connection closed while sending notice")

def gen_response_data(command):
    print(command)
    return contract_sub_df
    # return contract_sub_df.get(command['code'])

# ----------------------------------------------
# -- Data handling
# ----------------------------------------------
# 수신데이터 파싱 및 처리
def _dparse(data):
    global executed_df
    d1 = data.split("|")
    dp_ = None

    hcols = []

    if len(d1) >= 4:
        tr_id = d1[1]
        if tr_id == KIS_WSReq.CONTRACT:  # 실시간체결
            hcols = contract_cols
        elif tr_id == KIS_WSReq.BID_ASK: # 실시간호가
            hcols = bid_ask_cols
        elif tr_id == KIS_WSReq.NOTICE:  # 계좌체결통보
            hcols = notice_cols
        else:
            pass

        if tr_id in (KIS_WSReq.CONTRACT, KIS_WSReq.BID_ASK):  # 실시간체결, 실시간호가
            dp_ = pd.read_csv(StringIO(d1[3]), header=None, sep='^', names=hcols, dtype=object)  # 수신데이터 parsing
            if __DEBUG__: print(dp_)  # 실시간체결, 실시간호가 수신 데이터 파싱 결과 확인
            dp_['TICK_HOUR'] = __today__ + dp_['TICK_HOUR']    # 수신시간
            dp_['TICK_HOUR'] = pd.to_datetime(dp_['TICK_HOUR'], format='%Y%m%d%H%M%S', errors='coerce')
            
        else:  # 실시간 계좌체결발생통보는 암호화되어서 수신되므로 복호화 과정이 필요
            dp_ = pd.read_csv(StringIO(aes_cbc_base64_dec(_ekey, _iv, d1[3])), header=None, sep='^', names=hcols, dtype=object) # 수신데이터 parsing 및 복호화
            if __DEBUG__: print(dp_)  # 실시간 계좌체결발생통보 수신 파싱 결과 확인
            if __DEBUG__: print(f'***EXECUTED NOTICE [{dp_.to_string(header=False, index=False)}]')

        if tr_id == KIS_WSReq.CONTRACT: # 실시간 체결
            if __DEBUG__: print(dp_.to_string(header=False, index=False))
            stock_code = dp_[dp_.columns[0]].values.tolist()[0]
            df2_ = dp_[reserved_cols]
            selected_df = contract_sub_df.get(stock_code)
            if selected_df is not None and not selected_df.dropna().empty:
                dft_ = pd.concat([selected_df, df2_], axis=0, ignore_index=True)
            else:
                dft_ = df2_
            contract_sub_df[stock_code] = dft_
            contract_pr_triggered_actions(stock_code, dft_)

        if tr_id == KIS_WSReq.BID_ASK: # 실시간 호가
            if __DEBUG__: print(dp_.to_string(header=False, index=False))
            stock_code = dp_[dp_.columns[0]].values.tolist()[0]
            bid_ask_sub_df[stock_code] = dp_
            bid_ask_triggered_actions(stock_code)

        elif tr_id == KIS_WSReq.NOTICE:  # 체결통보의 경우, 일단 executed_df 에만 저장해 둠
            if __DEBUG__: print(dp_.to_string(header=False, index=False))
            executed_df = pd.concat([executed_df, dp_], axis=0, ignore_index=True)
            asyncio.create_task(execution_based_actions())

        else:
            pass
    else:
        print("Data length error...{data}")


# ----------------------------------------------
# -- Websocket Communication Logic
# ----------------------------------------------
connected_clients = set()
async def on_open(ws, stocks=target_stocks):
    # scks 에는 40개까지만 가능
    for scode in stocks:
        await subscribe(ws, KIS_WSReq.BID_ASK, _connect_key, scode)       # 실시간 호가
        await subscribe(ws, KIS_WSReq.CONTRACT, _connect_key, scode)      # 실시간 체결
    # 실시간 계좌체결발생통보를 등록한다. 계좌체결발생통보 결과는 executed_df 에 저장된다.
    await subscribe(ws, KIS_WSReq.NOTICE, _connect_key, HTS_ID) # HTS ID 입력

async def on_message(ws, data):
    # print('on_message=', data)
    global _iv, _ekey
    if data[0] in ('0', '1'):  # 0: not encrypted, 1: encrypted | 실시간체결 or 실시간호가
        _dparse(data)
    else:  # system message or PINGPONG
        rsp, _iv, _ekey = get_sys_resp(data, _iv, _ekey)
        if rsp.isPingPong:
            await ws.pong()
        else:
            if (not rsp.isUnSub and rsp.tr_id == KIS_WSReq.CONTRACT):
                # one time registerd for contract
                contract_sub_df[rsp.tr_key] = pd.DataFrame(columns=reserved_cols)
                register_contract_based_strategy(rsp.tr_key)
            elif (not rsp.isUnSub and rsp.tr_id == KIS_WSReq.BID_ASK):
                # one time registerd for bid-ask
                register_bid_ask_based_strategy(rsp.tr_key)
            elif (not rsp.isUnSub and rsp.tr_id == KIS_WSReq.NOTICE):
                # one time registerd for notice
                pass
            elif (rsp.isUnSub):
                del (contract_sub_df[rsp.tr_key])
            else:
                print(rsp)

async def on_error(ws, error):
    print('error=', error)

async def on_close(ws, status_code, close_msg):
    print('on_close close_status_code=', status_code, " close_msg=", close_msg)

# sub_data 는 종목코드(실시간체결, 실시간호가) 또는 HTS_ID(실시간 계좌체결발생통보)
async def subscribe(ws, sub_type, app_key, sub_data):  # 세션 종목코드(실시간체결, 실시간호가) 등록
    try:
        await ws.send(build_message(app_key, sub_type, sub_data))
    except websockets.exceptions.ConnectionClosed as e:
        print(f"WebSocket connection closed: {e}")

async def unsubscribe(ws, sub_type, app_key, sub_data): # 세션 종목코드(실시간체결, 실시간호가) 등록해제
    try:
        await ws.send(build_message(app_key, sub_type, sub_data, '2'))
    except websockets.exceptions.ConnectionClosed as e:
        print(f"WebSocket connection closed: {e}")

async def connect_to_server():
    # Connect to the WebSocket server and handle communication.
    uri = "ws://ops.koreainvestment.com:21000/tryitout"
    try:
        async with websockets.connect(uri) as ws:
            await on_open(ws)
            async for message in ws:
                await on_message(ws, message)
    except Exception as e:
        await on_error(ws, e)
    finally:
        await on_close(ws, 0, "Connection closed.")

async def run_websocket_client():
    await connect_to_server()

# Handle client connections
async def handle_client(reader, writer):
    connected_clients.add(writer)  
    print('Client connected')
    TIMEOUT = 3600 * 3  # n hours

    try:
        while True:
            try:
                command = await asyncio.wait_for(read_pickle(reader), timeout=TIMEOUT)
            except asyncio.TimeoutError:
                print("Client timeout")
                break
            except asyncio.IncompleteReadError:
                print("Client disconnected due to incomplete data")
                break
            except Exception as e:
                print(f"Error: {e}")
                break
            response_data = gen_response_data(command)  # Generate a response based on the command
            await write_pickle(writer, response_data)
    except asyncio.CancelledError:
        print("Client task canceled")
    finally:
        connected_clients.remove(writer)
        writer.close()
        await writer.wait_closed()
        print("Client connection closed")

# Main entry point
async def main():
    # Start the server
    server = await asyncio.start_server(handle_client, "127.0.0.1", 8888)
    print("Server is running...")
    
    # Keep the server running indefinitely
    await asyncio.gather(
        server.serve_forever(),
        run_websocket_client(),
        # generate_notice()  
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt: 
        print("KeyboardInterrupt received. Shutting down...")