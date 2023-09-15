from filter import *
from trader import *

filter = Filter()
trader = Trader()

balance = trader.check_balance()

for code in filter.target_companies(): 
    print(trader.get_price(code)['output']['stck_prpr']) 
