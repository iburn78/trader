import FinanceDataReader as fdr
import OpenDartReader 
import json

df_krx = fdr.StockListing('KRX')

print(df_krx)

# First of all, let's collect SEC data, and do the valuation...
with open('../config/config.json', 'r') as json_file:
    config = json.load(json_file)
    dart_api = config['dart_api']

dart = OpenDartReader(dart_api)

