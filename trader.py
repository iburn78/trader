from tools.koreainvest_module import * 
import json
from pprint import pprint

class Trader():
    def __init__(self):
        with open('../config/config.json', 'r') as json_file:
            config = json.load(json_file)
            key = config['key']
            secret = config['secret']
            acc_no = config['acc_no']
            key_mock = config['key_mock']
            secret_mock = config['secret_mock']
            acc_no_mock = config['acc_no_mock']

        # self.broker = mojito.KoreaInvestment(api_key=key, api_secret=secret, acc_no=acc_no, mock=False)
        self.broker = KoreaInvestment(api_key=key_mock, api_secret=secret_mock, acc_no=acc_no_mock, mock=True)
    
    def buy_at_price(self, code, price, quantity):
        resp = broker.create_limit_buy_order(
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

        


