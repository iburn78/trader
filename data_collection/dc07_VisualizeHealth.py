#%%
import sys, os
from trader.tools.tools import *
import pandas as pd
import numpy as np
import datetime

cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
main_db_file = os.path.join(cd_, 'data/financial_reports_main.feather')
main_db = pd.read_feather(main_db_file)

plot_gen_control_file = os.path.join(cd_, 'data/plot_gen_control.npy')
if not os.path.exists(plot_gen_control_file):
    raise FileNotFoundError('***** plot_gen_control.npy does not exist. *****')

price_db_file = os.path.join(cd_, 'data/price_DB.feather')
price_DB = pd.read_feather(price_db_file)

plot_ctrl = np.load(plot_gen_control_file, allow_pickle=True)
log_file = os.path.join(cd_, 'log/plot_gen_control_exceptions.log')

l = len(plot_ctrl)
for i, code in enumerate(plot_ctrl):
    print('{} | {}/{}'.format(code, i+1, l))
    path = os.path.join(cd_, 'plots/'+code+'.png')
    try:
        plot_company_financial_summary2(main_db, price_DB, code, path)
    except Exception as error:
        log_print(log_file, str(datetime.datetime.now())+' | '+code+' | '+str(error))
        if os.path.exists(path):
            os.remove(path)

os.remove(plot_gen_control_file)
