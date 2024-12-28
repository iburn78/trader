import asyncio
import kis_domstk as kd
from trader.tools_ws import read_pickle, write_pickle
from trader.analysis_class import *   

def independent_actions(): 
    res = kd.get_inquire_balance_obj()
    print(res)

    # [국내주식] 주문/계좌 > 매수가능조회 (종목번호 5자리 + 종목단가) REST API
    # val1: as str
    # rt_data = kd.get_inquire_psbl_order(pdno=stock_code, ord_unpr=val1)
    # ord_qty = rt_data.loc[0, 'nrcvb_buy_qty']  # nrcvb_buy_qty	미수없는매수수량
    # print("[미수없는매수주문가능수량!] : " + ord_qty)

    # 국내주식 현금 주문
    # rt_data = kd.get_order_cash(ord_dv="buy",itm_no=stock_code, qty=ord_qty, unpr=val1)
    # val1: as str
    # print(rt_data.KRX_FWDG_ORD_ORGNO + "+" + rt_data.ODNO + "+" + rt_data.ORD_TMD) # 주문접수조직번호+주문접수번호+주문시각
    # print("매수/매도 조건 주문 : " + val1)

# Central function to read messages from the server
async def read_from_server(reader):
    try:
        while True:
            try:
                response = await read_pickle(reader) # read response from the server as a pickle object
                if response is None:
                    break
                # handle logic here ######################
                # 1. response per query 
                # 2. infrequent updates (e.g., order status)
                print(f"Received response: {response}")

            except Exception as e:
                print(f"Error: {e}")
                break
    except asyncio.IncompleteReadError as e:
        print(f"Server closed the connection: {e}")
    except asyncio.CancelledError as e:
        print(f"Listening task was canceled: {e}")
    except Exception as e:
        print(f"Error while reading: {e}")
    finally: 
        pass

# One-time query to the server
async def query_data(writer):
    try: 
        while True:
            # "contract", "bid_ask", "executed", "strategy_ma", "stragegy_rsi", ""
            command_ = await asyncio.to_thread(input, "Enter command (or 'exit' to quit): ")
            command_ = command_.strip()
            code_ = None
            if command_ == "exit":
                print("Command mode exiting...")
                break
            if command_ in ['strategy_ma', 'strategy_rsi']:
                code_ = await asyncio.to_thread(input, "Enter code:")
                code_ = str(code_.strip())
            try:
                command = {
                    "get": command_, 
                    "code": code_,
                }
                await write_pickle(writer, command) # write command object to the server as a pickle object
                print(f"Sent query: {command}")
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"Error while getting input and sending query: {e}")
    except asyncio.CancelledError as e:
        print(f"Query-data task was canceled: {e}")
    except Exception as e:
        print(f"Error while sending query: {e}")

# Graceful shutdown handler
async def shutdown(tasks, writer):
    for task in tasks:
        task.cancel()
    try:
        results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=10)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i} failed during shutdown: {result}")
    except asyncio.TimeoutError:
        print("Some tasks failed to cancel within the timeout period.")

    if writer:
        writer.close()
        await writer.wait_closed()
        print("Connection closed.")

# Main task to handle both querying and listening
async def main():
    reader, writer = await asyncio.open_connection("127.0.0.1", 8888)
    print("Connected to the server")

    tasks = [
        asyncio.create_task(read_from_server(reader)), 
        asyncio.create_task(query_data(writer)),
        # tasks...
    ]

    try: 
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Error in main: {e}")
    finally: 
        await shutdown(tasks, writer)

if __name__ == "__main__":
    # try: 
    #     asyncio.run(main())
    # except KeyboardInterrupt:
    #     print("KeyboardInterrupt: Shutting down...")
    import kis_auth as ka
    import sys
    svr = sys.argv[1]
    ka.auth(svr=svr)  # 인증서버 및 계좌 선택 (prod:실전_main, auto:실전_autotrading, vps:개발)
    independent_actions()