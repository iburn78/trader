import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *
import pandas as pd

main_db_file = 'data/financial_reports_main.feather'
main_db = pd.read_feather(main_db_file)

update_db_file = 'data/financial_reports_update.feather'
update_db = pd.read_feather(update_db_file)
codes = update_db['code'].unique()

for code in codes:
    print('-------------------')
    print(code)
    path = 'plots/'+code+'.png'
    plot_company_financial_summary(main_db, code, path)


#### To-do next #### 
# - generate images for all codes (check if any errors occur while generating images)
# - copy them to TNP server
# - make a overarching code to run dc_05 and dc_06
#     . may need to monitor the success of each code and display it to TNP webpage/dashboard
# - copy newly generated images to TNP server for update/replace
