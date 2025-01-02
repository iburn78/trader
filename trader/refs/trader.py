#%% 
import json
from pprint import pprint
from trader.tools.koreainvest_module import *

class Trader():
    def __init__(self):
        # NEED TO PLACE THIS FILE IN RIGHT DIRECTORY e.g. trader/trader/trader.py
        ppd_ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # ../..
        with open(os.path.join(ppd_, 'config/config.json'), 'r') as json_file:
            config = json.load(json_file)
            key = config['key']
            secret = config['secret']
            acc_no = config['acc_no']
            key_mock = config['key_mock']
            secret_mock = config['secret_mock']
            acc_no_mock = config['acc_no_mock']

        self.broker = KoreaInvestment(api_key=key_mock, api_secret=secret_mock, acc_no=acc_no_mock, mock=True)
        # self.broker = KoreaInvestment(api_key=key, api_secret=secret, acc_no=acc_no, mock=False)
    
    def buy_at_price(self, code, price, quantity):
        resp = self.broker.create_limit_buy_order(
            symbol=code, 
            price=price,
            quantity=quantity
        )
        return resp

    def buy_at_market(self, code, quantity): 
        resp = self.broker.create_market_buy_order(
            ticker=code, 
            quantity=quantity
        )
        return resp
    
    def check_balance(self):
        resp = self.broker.fetch_balance()
        return resp
    
    def get_price(self, code): 
        resp = self.broker.fetch_price(code)
        return resp


trader = Trader()
r = trader.check_balance()
pprint(r)
#%% 
# trader.buy_at_price('005930', 54500, 10)
#%% 
r = trader.check_balance()
pprint(r)
#%% 
pprint(trader.get_price('005930'))
trader.buy_at_price('005930', 54500, 10)
#%% 
