import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *

if __name__ == '__main__': 
    log_file = 'data/data_collection_log.txt'
    try: 
        generate_krx_data()
    except Exception as e:
        print('Generation of KRX data failed: '+str(e))
        with open(log_file, 'a') as f:
            f.write('-------------------------------'+'\n')
            f.write('Generation of KRX data failed: '+str(e)+'\n')
            f.write('-------------------------------'+'\n')

    main_db = pd.read_feather('data/financial_reports_main.feather')
    start_day = main_db['date_updated'].max()
    update_db = generate_update_db(log_file, None, start_day)

    if update_db != None: 
        main_db = merge_update(main_db, update_db)
        main_db.to_feather('data/financial_reports_main.feather')

        print('== update finished ==')