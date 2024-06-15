#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.dictionary import ACCOUNT_NAME_DICTIONARY, BS_ACCOUNTS, IS_ACCOUNTS, DART_APIS, MODIFIED_REPORT
from tools.tools import *
import datetime

price_db_file = 'data/price_DB.feather'
pr_db = pd.read_feather(price_db_file)

fr_db_file = 'data/financial_reports_main.feather'
fr_db = pd.read_feather(fr_db_file)

codes = ['032830', '269620', '001720', '020180', '067010', '092440', '357430', '395400']
# path = 'plots/gen_{}.png'.format(code)
# plot_last_quarter_prices(pr_db, code, path)

log_file = 'log/plot_gen_control_exceptions.log'

l = len(codes)
for i, code in enumerate(codes):
    print('{} | {}/{}'.format(code, i+1, l))
    path = 'plots/'+code+'.png'
    try:
        plot_company_financial_summary2(fr_db, pr_db, code, path)
    except Exception as error:
        log_print(log_file, str(datetime.datetime.now())+' | '+code+' | '+str(error))
        if os.path.exists(path):
            os.remove(path)
