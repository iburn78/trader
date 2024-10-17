import FinanceDataReader as fdr
import json
from datetime import datetime

periodic_update_file = '~/tnp/public/andy/periodic_update.json'
pud = dict()

def code_desc_current(pr, code, range):
    stock_info = pr[pr['Code'] == code]
    price = int(stock_info['Close'].values[0])
    high = int(stock_info['High'].values[0])
    low = int(stock_info['Low'].values[0])
    vol = int(stock_info['Volume'].values[0])

    lb, ub = range
    if lb <= price <= ub:
        status = f'price within range ({lb}, {ub})'
    elif price < lb:
        status = f'price LOWER than {lb}: need attention!'
    else:
        status = f'price HIGHER than {ub}: check'

    if high >= ub:
        status += f'\n\nhigh value {high} hit over {ub}'
    if low <= lb:
        status += f'\n\nlow value {low} hit under {lb}'

    return status

pr = fdr.StockListing('KRX')
current_time = datetime.now()

# Define stock codes and price ranges
code1 = '011200'  # HMM
code1_range = (16000, 18000)
code2 = '294090'  # 25f
code2_range = (5500, 10000)

# Get statuses
status1 = code_desc_current(pr, code1, code1_range)
status2 = code_desc_current(pr, code2, code2_range)

# Prepare the output data
pud['Gen time'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
pud['# 1'] = "---"
pud['Code 1 status'] = status1
pud['# 2'] = "---"
pud['Code 2 status'] = status2

# Write to JSON file
with open(periodic_update_file, mode='w') as pdf:
    json.dump(pud, pdf, indent=4)
