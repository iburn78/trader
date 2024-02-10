#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *
import pandas as pd
import datetime

main_db_file = 'data/financial_reports_main.feather'
main_db = pd.read_feather(main_db_file)

plot_gen_control_file = 'data/plot_gen_control.npy'
if not os.path.exists(plot_gen_control_file):
    sys.exit()

plot_ctrl = np.load(plot_gen_control_file, allow_pickle=True)
log_file = 'data/plot_gen_control_execptions.txt'
l = len(plot_ctrl)

for i, code in enumerate(plot_ctrl):
    try:
        print('{} | {}/{}'.format(code, i, l))
        path = 'plots/'+code+'.png'
        plot_company_financial_summary(main_db, code, path)
    except Exception as error:
        log_print(log_file, str(datetime.datetime.now())+' | '+code+' | '+str(error))

os.remove(plot_gen_control_file)

#### To-do next #### 
# - generate images for all codes (check if any errors occur while generating images)
# - copy them to TNP server
# - make a overarching code to run dc_05 and dc_06
#     . may need to monitor the success of each code and display it to TNP webpage/dashboard
# - copy newly generated images to TNP server for update/replace
