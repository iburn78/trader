#%%
# Create a function to measure a financial health of a company 

import OpenDartReader 
import os
from trader.tools.dictionary import ACCOUNT_NAME_DICTIONARY, BS_ACCOUNTS, IS_ACCOUNTS, DART_APIS, MODIFIED_REPORT
from trader.tools.tools import * 
import pandas as pd
import numpy as np
import datetime, time
import warnings
import gc

def _collect_financial_reports(dart, code, duration=None, date_updated=None): # duration as years

    def sj_div(account_nm):
        if account_nm in BS_ACCOUNTS:
            return 'BS'
        elif account_nm in IS_ACCOUNTS:
            return 'IS'
        else:
            raise Exception('No BS, IS account exception')

    def post_process(rec): 
        if len(rec) > 0:
            # in some cases, certain data is '-'
            rec.replace('-', pd.NA, inplace=True)
            # add more logic for post_process if needed
            # ...
            return rec
        else: 
            return rec

    def get_prev_quarter(yr, qtr): # qtr in [1, 2, 3, 4]
        if qtr == 1: 
            return yr-1, 4 
        else: 
            return yr, qtr-1 

    def get_prev_quarter_except_FY(yr, qtr): # qtr in [1, 2, 3, 4]
        if qtr == 1:
            return yr-1, 3 
        else: 
            return yr, qtr-1 

    # find initial report
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    quarter = month//3 + 1

    reprt_code_dict = {1: '11013', 2: '11012', 3: '11014', 4: '11011'}

    y = year
    q = quarter
    ind = 0

    while True:
        ind += 1
        y, q = get_prev_quarter(y, q)
        rec = dart.finstate(code, y, reprt_code=reprt_code_dict[q])
        if len(rec) > 0:
            break
        if ind == 8: # search initial data within last 8 quarters
            # raise Exception('Data not available for code:', code) 
            return pd.DataFrame(), 'Data Not Available'

    record = pd.DataFrame(columns=['stock_code', 'fs_div', 'sj_div', 'account_nm', 'date_updated'])
    accounts = BS_ACCOUNTS + IS_ACCOUNTS
    if date_updated == None:
        date_updated = datetime.datetime.today().strftime('%Y-%m-%d')

    for i in range(len(accounts)):
        record.loc[i] = [code, 'CFS', sj_div(accounts[i]), accounts[i], date_updated]  
    for i in range(len(accounts)):
        record.loc[i+len(accounts)] = [code, 'OFS', sj_div(accounts[i]), accounts[i], date_updated]  

    if rec['currency'][0] != 'KRW':
        # raise Exception('Currency is not in KRW for code: ', code)
        return pd.DataFrame(), 'Currency Not in KRW'

    y_init = y
    q_init = q

    # data collection method
    # Step 1. collect annual data (and for the last report, collect y-1 and y-2 data)
    # Step 2. collect quarterly data (and if data for the same quarter in the last year), and add 4Q quarterly data column if possible (i.e., if full year data is available) 
    #     note that for BS items, no need to collect previous year data in quarterly data collecting (not provided in Dart)

    # Step 1:
    if q_init != 4: 
        y = y_init-1
    rec = dart.finstate(code, y, reprt_code=reprt_code_dict[4])
    rec = post_process(rec)

    if duration == None or duration <= 0:
        duration = 10000 # a large number enough

    ind = 0
    while len(rec)>0:
        data_term = 'FY'+str(y)
        rec[data_term] = rec['thstrm_amount'].str.replace(',','').astype('Int64')
        record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', data_term]], how='left', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])

        ind += 1
        if ind == duration:
            break

        # check if there is data in prev year 
        prev_year_rec = dart.finstate(code, y-1, reprt_code=reprt_code_dict[4]) 
        prev_year_rec = post_process(prev_year_rec)
        if len(prev_year_rec) == 0: 
            prev_term = 'FY'+str(y-1)
            pprev_term = 'FY'+str(y-2)
            rec[prev_term] = rec['frmtrm_amount'].str.replace(',','').astype('Int64')
            rec[pprev_term] = rec['bfefrmtrm_amount'].str.replace(',','').astype('Int64')
            record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', prev_term, pprev_term]], how='left', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])
            break
        else: 
            y = y-1
            rec = prev_year_rec

    # Step 2:
    if q_init == 4: 
        y = y_init
        q = 3
    else: 
        y = y_init
        q = q_init
    rec = dart.finstate(code, y, reprt_code=reprt_code_dict[q])
    rec = post_process(rec)

    ind = 0
    while len(rec)>0:
        data_term = str(y)+'_'+str(q)+'Q'
        rec[data_term] = rec['thstrm_amount'].str.replace(',','').astype('Int64')
        record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', data_term]], how='left', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])

        # adding 4Q data if 'thstr_add_amount' is available
        # NOTE:
        # some sj_div items are neither IS or BS, and None... 
        # which leaves, 4Q data as sum of 1-3Q... 
        # you may consider correct this in the future
        if q == 3 and 'thstrm_add_amount' in rec.columns:
            if 'FY'+str(y) in record.columns:
                q4_term = str(y)+'_4Q'
                rec.loc[rec['sj_div']=='IS', q4_term] = rec.loc[rec['sj_div']=='IS','thstrm_add_amount'].str.replace(',','').astype('Int64')
                record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', q4_term]], how='left', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])
                record.loc[record['sj_div']=='IS', q4_term] = record.loc[record['sj_div']=='IS','FY'+str(y)]-record.loc[record['sj_div']=='IS', q4_term]
                record.loc[record['sj_div']=='BS', q4_term] = record.loc[record['sj_div']=='BS','FY'+str(y)]

        ind += 1
        if ind == duration*3:
            break

        # check if there is data in the prev year, the same quarter
        prev_year_rec = dart.finstate(code, y-1, reprt_code=reprt_code_dict[q]) 
        prev_year_rec = post_process(prev_year_rec)
        if len(prev_year_rec) == 0 and 'frmtrm_amount' in rec.columns: 
            prev_term = str(y-1)+'_'+str(q)+'Q'
            # add only IS data
            rec.loc[rec['sj_div']=='IS', prev_term] = rec.loc[rec['sj_div']=='IS', 'frmtrm_amount'].str.replace(',','').astype('Int64')
            record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', prev_term]], how='left', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])

            if q == 3 and 'frmtrm_add_amount' in rec.columns:
                if 'FY'+str(y-1) in record.columns:
                    last_q4_term = str(y-1)+'_4Q'
                    rec.loc[rec['sj_div']=='IS', last_q4_term] = rec.loc[rec['sj_div']=='IS','frmtrm_add_amount'].str.replace(',','').astype('Int64')
                    record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', last_q4_term]], how='left', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])
                    record.loc[record['sj_div']=='IS', last_q4_term] = record.loc[record['sj_div']=='IS','FY'+str(y-1)]-record.loc[record['sj_div']=='IS', last_q4_term]
                    record.loc[record['sj_div']=='BS', last_q4_term] = record.loc[record['sj_div']=='BS','FY'+str(y-1)]

        y, q = get_prev_quarter_except_FY(y, q)
        rec = dart.finstate(code, y, reprt_code=reprt_code_dict[q])
        rec = post_process(rec)
    
    # post process
    record.rename(columns={'stock_code':'code', }, inplace=True)
    record['account'] = record['account_nm'].apply(lambda x: ACCOUNT_NAME_DICTIONARY[x] if x in ACCOUNT_NAME_DICTIONARY.keys() else x)

    message = 'success'
    return record, message

def _sort_columns_financial_reports(reports):
    if len(reports) == 0: 
        return pd.DataFrame()
    static_columns = ['code', 'fs_div', 'sj_div', 'account_nm', 'account', 'date_updated']
    return pd.concat([reports[static_columns], reports[reports.columns.difference(static_columns)].sort_index(axis=1)], axis=1)

def _generate_financial_reports_set(sector, duration, log_file, date_updated):
    dart_ind = 0
    dart = OpenDartReader(DART_APIS[dart_ind])

    financial_reports = []
    log_print(log_file, 'Financial data collection log >> ')

    error_trial = 0
    error_trial_limit = 10
    sleep_time = 5 # seconds
    for ix, code in enumerate(sector):
        retry_required = True
        API_change_tried = False
        while retry_required:
            try:
                current_progress = str(datetime.datetime.now()) + ', no: ' + str(ix) + ', code ' + code+' in process' # / '+df_krx['Name'][code]
                log_print(log_file, current_progress)

                if dart.find_corp_code(code) == None: 
                    current_progress = '----> no: ' + str(ix) + ', code ' + code+' not in corp_code, and therefore data not available' # / '+df_krx['Name'][code]
                    log_print(log_file, current_progress)
                    retry_required = False
                    continue # skip the rest of the code
    
                record, message = _collect_financial_reports(dart, code, duration, date_updated)
                if message == 'success':
                    financial_reports.append(record)
                elif message == 'Data Not Available':
                    current_progress = '----> no: ' + str(ix) + ', code ' + code+' data not available, could be a financial institution' # / '+df_krx['Name'][code]
                    log_print(log_file, current_progress)
                    if not API_change_tried:
                        dart_ind += 1
                        dart = OpenDartReader(DART_APIS[dart_ind%3])
                        API_change_tried = True
                        continue
                elif message == 'Currency Not in KRW':
                    current_progress = '----> no: ' + str(ix) + ', code ' + code+' currency not in KRW, skipping' # / '+df_krx['Name'][code]
                    log_print(log_file, current_progress)
                else:
                    raise Exception('ERROR in execution loop')

                time.sleep(sleep_time)
                error_trial = 0 # reset
                retry_required = False

            except Exception as e:
                current_progress = '----> no: ' + str(ix) + ', code ' + code+' unknown exception; process suspended and to be re-tried' # / '+df_krx['Name'][code]
                log_print(log_file, current_progress)
                log_print(log_file, e)

                if error_trial < error_trial_limit:
                    error_trial += 1
                    dart_ind += 1
                    dart = OpenDartReader(DART_APIS[dart_ind%3])
                    log_print(log_file, '** API-changed **')
                else:
                    log_print(log_file, '** ERROR TRIAL LIMIT REACHED - Entire Process Halted **')
                    raise Exception('ERROR TRIAL LIMIT REACHED - Entire Process Halted')  # no catch, thus propagates to halt the program. 

                time.sleep(sleep_time*error_trial)

    if len(financial_reports) == 0:
        return pd.DataFrame()
    final = pd.concat(financial_reports, ignore_index=True)
    return final

def _generate_update_codelist(log_file, start_day, end_day): 
    dart = OpenDartReader(DART_APIS[2])
    log_print(log_file, 'Updating between dates: '+ str(start_day) + ' / ' + str(end_day))
    ls = dart.list(start=start_day, end=end_day, kind='A') # works only withn three month gap between start_day and end_day
    if len(ls) == 0: 
        log_print(log_file, 'No new data to update')
        return [], []

    full_rescan_code = ls.loc[ls['report_nm'].str.contains(MODIFIED_REPORT)]['stock_code'].values
    full_rescan_code = np.unique(full_rescan_code[full_rescan_code.astype(bool)]).tolist()
    partial_rescan_code = ls.loc[~ls['report_nm'].str.contains(MODIFIED_REPORT)]['stock_code'].values
    partial_rescan_code = np.unique(partial_rescan_code[partial_rescan_code.astype(bool)]).tolist()

    return full_rescan_code, partial_rescan_code

def _update_code_checker(log_file, main_db, df_krx, full_rescan_code, partial_rescan_code):
    # include codes that does not have 2 quarters previous data, while have 3 quarters data
    cp2 = null_checker(main_db, 2)
    cp3 = null_checker(main_db, 3)
    to_add_partially = [i for i in cp2 if i not in cp3]
    partial_rescan_code = list(set(partial_rescan_code) | set(to_add_partially)) # union

    # exclude codes that are already scanned
    tg_qt = nth_quarter_before(1)  # last quarter 
    if tg_qt in main_db.columns:
        # Filter main_db once to get which codes are completely NaN for last quarter
        valid_codes = main_db.groupby('code')[tg_qt].apply(lambda x: x.isna().all())
        # Keep only codes that are either not in main_db or have all NaN for tg_qt
        partial_rescan_code = [
            c for c in partial_rescan_code
            if c not in valid_codes.index or valid_codes[c]
        ] 

    # exclude codes that are not in df_krx
    df_krx_index_set = set(df_krx.index)  # O(1) search while df_krx.index is O(log n) search (not much meaningful if n is less than 10000 for example)
    full_rescan_code = [c for c in full_rescan_code if c in df_krx_index_set]
    partial_rescan_code = [c for c in partial_rescan_code if c in df_krx_index_set]

    if full_rescan_code:
        log_print(log_file, '\nFull rescan codes are {} items: \n{}'.format(len(full_rescan_code), full_rescan_code))
    else: 
        log_print(log_file, 'No new full rescan code to update')

    if partial_rescan_code:
        log_print(log_file, '\nPartial rescan codes are {} items: \n{}'.format(len(partial_rescan_code), partial_rescan_code))
    else: 
        log_print(log_file, 'No new partial rescan code to update')

    return full_rescan_code, partial_rescan_code

def _plot_ctrl(plot_gen_control_file, code_list):
    if plot_gen_control_file is None: return 
    if os.path.exists(plot_gen_control_file):
        code_list = np.unique(np.concatenate((code_list, np.load(plot_gen_control_file, allow_pickle=True))))
    np.save(plot_gen_control_file, code_list)

def update_main_db(log_file, main_db, df_krx, plot_gen_control_file=None):
    log_print(log_file, 'Company health data collection initiated at '+str(datetime.datetime.today()))
    try: 
        log_print(log_file, 'Updating KRX data...')
        warnings.filterwarnings("ignore")
        df_krx = generate_krx_data()
        warnings.resetwarnings()
    except Exception as e:
        log_print(log_file, 'Generation of KRX data failed: '+str(e))
        raise Exception('Generation of KRX data failed: '+str(e))

    # removing codes that are not in df_krx : removing delisted
    main_db = main_db[main_db['code'].isin(df_krx.index)]

    start_day = main_db['date_updated'].max()
    start_day = (pd.to_datetime(start_day) - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    end_day = datetime.datetime.today().strftime('%Y-%m-%d')
    # to manually assign the period: (up to three months)
    # start_day = '2023-11-14'
    # end_day = '2023-11-15'

    full_rescan_code, partial_rescan_code = _generate_update_codelist(log_file, start_day, end_day)
    full_rescan_code, partial_rescan_code = _update_code_checker(log_file, main_db, df_krx, full_rescan_code, partial_rescan_code)

    if not full_rescan_code and not partial_rescan_code:
        log_print(log_file, '** Nothing to update - main_db not updated **')
        _plot_ctrl(plot_gen_control_file, [])
        return None

    BATCH_SIZE = 100

    for i in range(0, len(full_rescan_code), BATCH_SIZE):
        log_print(log_file, f"full_rescan batch operation: {i}")
        batch_codes = full_rescan_code[i:i+BATCH_SIZE]
        db_f = _generate_financial_reports_set(batch_codes, None, log_file, end_day)
        main_db = merge_update(main_db, db_f, None) 
        main_db = _sort_columns_financial_reports(main_db)
        save_main_financial_reports_db(main_db)
        _plot_ctrl(plot_gen_control_file, batch_codes)

        del db_f
        gc.collect()

    for i in range(0, len(partial_rescan_code), BATCH_SIZE):
        log_print(log_file, f"partial_rescan batch operation: {i}")
        batch_codes = partial_rescan_code[i:i+BATCH_SIZE]
        db_p = _generate_financial_reports_set(batch_codes, 2, log_file, end_day) # 2 years
        main_db = merge_update(main_db, None, db_p)
        main_db = _sort_columns_financial_reports(main_db)
        save_main_financial_reports_db(main_db)
        _plot_ctrl(plot_gen_control_file, batch_codes)

        del db_p
        gc.collect()

    log_print(log_file, '== Update finished ==')


def single_company_data_collect(code, fs_div=None):
    dart = OpenDartReader(DART_APIS[1])
    record, message = _collect_financial_reports(dart, code)
    if fs_div != None:
        record = record.loc[record['fs_div']==fs_div]
    return _sort_columns_financial_reports(record)

if __name__ == '__main__': 
    cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
    log_file = os.path.join(cd_, 'log/data_collection.log')
    plot_gen_control_file = os.path.join(cd_, 'data/plot_gen_control.npy')
    main_db = get_main_financial_reports_db()
    df_krx = get_df_krx()

    update_main_db(log_file, main_db, df_krx, plot_gen_control_file)
