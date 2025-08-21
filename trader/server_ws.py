#%% 
import websockets  
import asyncio
import kis_auth as ka 
import pandas as pd
from io import StringIO
from tools_ws import *
from analysis_class import *

# ----------------------------------------------
# -- Auth and Config
# ----------------------------------------------
ka.auth(svr='vps')  # 인증서버 및 계좌 선택 (prod:실전_main, auto:실전_autotrading, vps:개발)

__today__ = pd.Timestamp.now().strftime("%Y%m%d")
__DEBUG__ = False  
_connect_key = get_approval()  # websocket 연결Key
_HTS_ID = ka.getTREnv().hts_id
_iv = None  # for 복호화
_ekey = None  # for 복호화

# ----------------------------------------------
# -- Analysis targets
# ----------------------------------------------
target_stocks = ('005930', '000660',) 

# ----------------------------------------------
# -- Data Structure
# ----------------------------------------------
# Contract: 체결 in this code
contract_sub_df = dict()  # 실시간 국내주식 체결 결과를 종목별로 저장하기 위한 container
bid_ask_sub_df = dict()   # 실시간 국내주식 호가 결과를 종목별로 저장하기 위한 container
executed_df = pd.DataFrame(data=None, columns=contract_cols)  # 체결통보 저장용 DF

# ----------------------------------------------
# -- Custom Strategy Implementation
# ----------------------------------------------
ma_instances = dict()         # MovingAverage Class 를 저장하기 위한 container
rsi_instances = dict()         # RSI_ST Class 를 저장하기 위한 container
ba_instances = dict()         # BID_ASK_status Class 를 저장하기 위한 container

def register_contract_based_actions(stock_code):
    ma_instances[stock_code] = MovingAverage(stock_code)  # 이동 평균선 계산 (웹소켓 프로그램 실행시 수집된 데이터만 반영)  
    rsi_instances[stock_code] = RSI_ST(stock_code)  # RSI(Relative Strength Index, 상대강도지수)라는 주가 지표 계산

def register_bid_ask_based_actions(stock_code):
    ba_instances[stock_code] = BID_ASK_status(stock_code)  # BID_ASK_status 계산

def contract_triggered_actions(stock_code, dp_):
    val1 = int(dp_['STCK_PRPR'].iloc[-1])
    ma_instances[stock_code].push(val1)      # 이동평균값 활용
    rsi_instances[stock_code].eval(contract_sub_df)         # RSI(Relative Strength Index, 상대강도지수)라는 주가 지표 계산 활용

def bid_ask_triggered_actions(stock_code):
    ba_instances[stock_code].eval(bid_ask_sub_df)  # BID_ASK_status 계산 

async def execution_based_actions():
    for writer in connected_clients:
        try:
            await write_pickle(writer, executed_df)
        except websockets.ConnectionClosed:
            print("Connection closed while sending notice.")

def gen_response_data(command):
    if command == None: # when client disconneted, etc...
        return None
    if command.get('get') == 'contract':
        return contract_sub_df
    elif command.get('get') == 'bid_ask':
        return bid_ask_sub_df
    elif command.get('get') == 'executed':
        return executed_df
    elif command.get('get') == 'strategy_ma':
        if command.get('code') in ma_instances:
            return ma_instances[command.get('code')]
        else:
            return '(code not exist)' # None
    elif command.get('get') == 'strategy_rsi':
        if command.get('code') in rsi_instances:
            return rsi_instances[command.get('code')]
        else:
            return '(code not exist)' # None
    else:
        return '(invalid command)' # None

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
                print("Connection closed while sending notice.")

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
            print(f'***EXECUTED NOTICE [{dp_.to_string(header=False, index=False)}]')

        if tr_id == KIS_WSReq.CONTRACT: # 실시간 체결
            if __DEBUG__: print(dp_.to_string(header=False, index=False))
            stock_code = dp_.iloc[0,0]
            df2_ = dp_[reserved_cols]
            selected_df = contract_sub_df.get(stock_code)
            if selected_df is not None and not selected_df.dropna().empty:
                dft_ = pd.concat([selected_df, df2_], axis=0, ignore_index=True)
            else:
                dft_ = df2_
            contract_sub_df[stock_code] = dft_
            contract_triggered_actions(stock_code, dft_)

        if tr_id == KIS_WSReq.BID_ASK: # 실시간 호가
            if __DEBUG__: print(dp_.to_string(header=False, index=False))
            stock_code = dp_.iloc[0,0]
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
client_id_counter = 0
async def on_open(ws, stocks=target_stocks):
    # scks 에는 40개까지만 가능
    for scode in stocks:
        await subscribe(ws, KIS_WSReq.CONTRACT, _connect_key, scode)      # 실시간 체결
        await subscribe(ws, KIS_WSReq.BID_ASK, _connect_key, scode)       # 실시간 호가
    # 실시간 계좌체결발생통보를 등록한다. 계좌체결발생통보 결과는 executed_df 에 저장된다.
    await subscribe(ws, KIS_WSReq.NOTICE, _connect_key, _HTS_ID) # HTS ID 입력

async def on_message(ws, data):
    # print('on_message=', data)
    global _iv, _ekey
    if data[0] in ('0', '1'):  # 0: not encrypted, 1: encrypted | 실시간체결 or 실시간호가
        print(data)
        a = _dparse(data)
        print(a)
    else:  # system message or PINGPONG
        rsp, _iv, _ekey = get_sys_resp(data, _iv, _ekey)
        if rsp.isPingPong:
            await ws.pong()
        else:
            if (not rsp.isUnSub and rsp.tr_id == KIS_WSReq.CONTRACT):
                # one time registerd for contract
                contract_sub_df[rsp.tr_key] = pd.DataFrame(columns=reserved_cols)
                register_contract_based_actions(rsp.tr_key)
            elif (not rsp.isUnSub and rsp.tr_id == KIS_WSReq.BID_ASK):
                # one time registerd for bid-ask
                register_bid_ask_based_actions(rsp.tr_key)
            elif (not rsp.isUnSub and rsp.tr_id == KIS_WSReq.NOTICE):
                # one time registerd for notice
                pass
            elif (rsp.isUnSub):
                del (contract_sub_df[rsp.tr_key])
            else:
                print(rsp)

async def on_error(error):
    print('error=', error)

async def on_close(status_code, close_msg):
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
        await on_error(e)
    finally:
        await on_close(0, "Connection closed.")


async def run_websocket_client():
    while True:
        try:
            await connect_to_server()
        except asyncio.CancelledError:
            print("WebSocket task canceled.")
            break
        except Exception as e:
            print(f"Error in run_websocket_client: {e}")
            await asyncio.sleep(5)  # Optional: Wait before retrying

# Handle client connections
async def handle_client(reader, writer):
    global client_id_counter  # as we are modifying the global non-mutable variable
    try:
        connected_clients.add(writer)  
        client_id_counter += 1
        client_id = str(client_id_counter)
        print(f'Client connected with id: {client_id}')
        await write_pickle(writer, "Assigned id: " + client_id)

        TIMEOUT = 3600 * 3  # n hours
        while True:
            try:
                command = await asyncio.wait_for(read_pickle(reader), timeout=TIMEOUT)
                response_data = gen_response_data(command)  # Generate a response based on the command
                if response_data is not None: # don't use != None here
                    print(response_data)
                    await write_pickle(writer, response_data)
                else:
                    break
            except asyncio.TimeoutError as e:
                print(f"Client timeout: {e}")
                break
            except ConnectionResetError as e:
                print(f"Connection reset: {e}")
                break
            except OSError as e:
                print(f"OS error: {e}")
                break
            except asyncio.IncompleteReadError as e:
                print(f"Incomplete Read Error: {e}")
                break
            except Exception as e:
                print(f"Error: {e}")
                break
    except asyncio.CancelledError as e:
        print(f"Client task canceled: {e}")
    finally:
        connected_clients.discard(writer)
        if not writer.is_closing():
            writer.close()
            await writer.wait_closed()
        print(f'Client connected closed id: {client_id}')

# Graceful shutdown handler
async def shutdown(tasks, server):
    for task in tasks:
        task.cancel()
    try:
        results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=10)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i} failed during shutdown: {result}")
    except asyncio.TimeoutError:
        print("Some tasks failed to cancel within the timeout period.")

    if server:
        server.close()
        await server.wait_closed()
        print("Server closed.")

# Main entry point
async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 8888)
    print("Server is running...")

    tasks = [
        asyncio.create_task(run_websocket_client()),
        asyncio.create_task(server.serve_forever()),
        asyncio.create_task(generate_notice()),
    ]

    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Error in main: {e}")
    finally: # cleanup code to esnure that all tasks are cancelled and the server is closed
        await shutdown(tasks, server)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt: 
        print("KeyboardInterrupt received. Shutting down...")