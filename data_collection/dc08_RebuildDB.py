# this is for rebuilding DBs for both price and financial records 
# be careful in setting up date_req and DAYS_ALLOWANCE
# DAYS_ALLOWANCE is for giving enough time for DART to update its API

#%% 
import datetime
import os
from trader.tools.dictionary import *
from trader.tools.tools import * 
from dc05_CompanyHealth import _generate_financial_reports_set, _sort_columns_financial_reports
from dc06_GenPriceDB import gen_price_DB

cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
log_file = os.path.join(cd_, 'log/rebuild.log')
price_db_file = os.path.join(cd_, 'data/price_DB.feather') 

date_req = '20240612'
df_krx = fdr.StockListing('KRX', date_req)
codelist = df_krx.Code.tolist()[:]

DAYS_ALLOWANCE = 2
end_day = (datetime.datetime.today() - datetime.timedelta(days=DAYS_ALLOWANCE)).strftime('%Y-%m-%d')
res = _generate_financial_reports_set(codelist, 1, log_file, end_day) # 1 year
res = _sort_columns_financial_reports(res)

main_db = get_main_financial_reports_db()
main_db = merge_update(main_db, res)
save_main_financial_reports_db(main_db)

gen_price_DB()
price_DB = pd.read_feather(price_db_file)

l = len(codelist)
for i, code in enumerate(codelist):
    print('{} | {}/{}'.format(code, i+1, l))
    path = os.path.join(cd_, 'plots/'+code+'.png')
    try:
        plot_company_financial_summary2(main_db, price_DB, code, path)
        pass
    except Exception as error:
        log_print(log_file, str(datetime.datetime.now())+' | '+code+' | '+str(error))
        if os.path.exists(path):
            os.remove(path)
