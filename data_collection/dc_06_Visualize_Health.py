#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *
import pandas as pd
import datetime

main_db_file = 'data/financial_reports_main.feather'
main_db = pd.read_feather(main_db_file)
all_codes = main_db['code'].unique()

update_db_file = 'data/financial_reports_update.feather'
update_db = pd.read_feather(update_db_file)
codes = update_db['code'].unique()

df_krx_file = 'data/df_krx.feather'
df_krx = pd.read_feather(df_krx_file)
display(df_krx)

# #%%
# log_file = 'dc_06_exception_errors_check.txt'
# for i, code in enumerate(except_list[:1]):
#     try:
#         print('-------------------')
#         print('{} | {}/{}'.format(code, i, l))
#         if code not in df_krx.index:
#             continue
#         path = 'plots/'+code+'.png'
#         plot_company_financial_summary(main_db, code, path)
#     except Exception as error:
#         final_ex_list.append(code)
#         log_print(log_file, code+' | '+str(error))

# log_print(log_file, 'Exception list: '+ str(final_ex_list))
    

#### To-do next #### 
# - generate images for all codes (check if any errors occur while generating images)
# - copy them to TNP server
# - make a overarching code to run dc_05 and dc_06
#     . may need to monitor the success of each code and display it to TNP webpage/dashboard
# - copy newly generated images to TNP server for update/replace

# %%
