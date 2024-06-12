#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *
import pandas as pd
import numpy as np
import datetime

main_db_file = 'data/financial_reports_main.feather'
main_db = pd.read_feather(main_db_file)

plot_gen_control_file = 'data/plot_gen_control.npy'
if not os.path.exists(plot_gen_control_file):
    sys.exit()

price_db_file = 'data/price_DB.feather'
price_DB = pd.read_feather(price_db_file)

plot_ctrl = np.load(plot_gen_control_file, allow_pickle=True)
log_file = 'log/plot_gen_control_exceptions.log'

l = len(plot_ctrl)
for i, code in enumerate(plot_ctrl):
    print('{} | {}/{}'.format(code, i+1, l))
    path = 'plots/'+code+'.png'
    try:
        plot_company_financial_summary2(main_db, price_DB, code, path)
    except Exception as error:
        log_print(log_file, str(datetime.datetime.now())+' | '+code+' | '+str(error))
        if os.path.exists(path):
            os.remove(path)

os.remove(plot_gen_control_file)
