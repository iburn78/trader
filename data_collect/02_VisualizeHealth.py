#%%
import os
from trader.tools.dc_tools import get_main_financial_reports_db, plot_company_financial_summary, log_print
import pandas as pd
import numpy as np
import datetime

def create_plots_from_plot_gen_control(plot_gen_control_file):
    if not os.path.exists(plot_gen_control_file):
        print('----------------------------------------------------')
        print('no codelist to create plots (target file not exist).')
        print('----------------------------------------------------')
        # raise FileNotFoundError('***** no codelist to create plots (target file not exist). *****')
        return

    main_db = get_main_financial_reports_db()

    price_db_file = os.path.join(cd_, 'data/price_DB.feather')
    price_DB = pd.read_feather(price_db_file)

    plot_ctrl = np.load(plot_gen_control_file, allow_pickle=True)
    log_file = os.path.join(cd_, 'log/plot_gen_control_exceptions.log')

    # -----------------------------------------------------
    # in case to regenerate all plots use
    # codelist = fdr.StockListing('KRX')['Code'].tolist()
    # plot_ctrl = codelist
    # -----------------------------------------------------
    l = len(plot_ctrl)
    for i, code in enumerate(plot_ctrl):
        print('{} | {}/{}'.format(code, i+1, l))
        path = os.path.join(cd_, 'plots/'+code+'.png')
        try:
            plot_company_financial_summary(main_db, price_DB, code, path)
        except Exception as error:
            log_print(log_file, str(datetime.datetime.now())+' | '+code+' | '+str(error))
            if os.path.exists(path):
                os.remove(path)

    os.remove(plot_gen_control_file)

if __name__ == "__main__":
    cd_ = os.path.dirname(os.path.abspath(__file__)) # .
    plot_gen_control_file = os.path.join(cd_, 'data/plot_gen_control.npy')

    create_plots_from_plot_gen_control(plot_gen_control_file)