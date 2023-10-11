# %% [markdown]
# Create a function to measure a financial health of a company 

# %%
import OpenDartReader 
import json

with open('../../config/config.json', 'r') as json_file:
    config = json.load(json_file)
    dart_api_1 = config['dart_api_1']
    dart_api_2 = config['dart_api_2']
    dart_api_3 = config['dart_api_3']
    dart_apis = [dart_api_1, dart_api_2, dart_api_3]


import pandas as pd
import datetime
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.dictionary import ACCOUNT_NAME_DICTIONARY, BS_ACCOUNTS, IS_ACCOUNTS

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

def collect_financial_reports(dart, code):
    # find initial report
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    quarter = month//3 + 1

    reprt_code_dict = {1: '11013', 2: '11012', 3: '11014', 4: '11011'}

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

    record = pd.DataFrame(columns=['stock_code', 'fs_div', 'sj_div', 'account_nm'])
    accounts = BS_ACCOUNTS + IS_ACCOUNTS

    for i in range(len(accounts)):
        record.loc[i] = [code, 'CFS', sj_div(accounts[i]), accounts[i]]  
    for i in range(len(accounts)):
        record.loc[i+len(accounts)] = [code, 'OFS', sj_div(accounts[i]), accounts[i]]  

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

    while len(rec)>0:
        data_term = 'FY'+str(y)
        # print(data_term)
        rec[data_term] = rec['thstrm_amount'].str.replace(',','').astype('Int64')
        record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', data_term]], how='outer', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])

        # check if there is data in prev year 
        prev_year_rec = dart.finstate(code, y-1, reprt_code=reprt_code_dict[4]) 
        prev_year_rec = post_process(prev_year_rec)
        if len(prev_year_rec) == 0: 
            prev_term = 'FY'+str(y-1)
            pprev_term = 'FY'+str(y-2)
            rec[prev_term] = rec['frmtrm_amount'].str.replace(',','').astype('Int64')
            rec[pprev_term] = rec['bfefrmtrm_amount'].str.replace(',','').astype('Int64')
            record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', prev_term, pprev_term]], how='outer', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])
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

    while len(rec)>0:
        data_term = str(y)+'_'+str(q)+'Q'
        # print(data_term)
        rec[data_term] = rec['thstrm_amount'].str.replace(',','').astype('Int64')
        record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', data_term]], how='outer', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])

        # adding 4Q data if 'thstr_add_amount' is available
        # NOTE:
        # some sj_div items are neither IS or BS, and None... 
        # which leaves, 4Q data as sum of 1-3Q... 
        # you may consider correct this in the future
        if q == 3 and 'thstrm_add_amount' in rec.columns:
            if 'FY'+str(y) in record.columns:
                q4_term = str(y)+'_4Q'
                rec.loc[rec['sj_div']=='IS', q4_term] = rec.loc[rec['sj_div']=='IS','thstrm_add_amount'].str.replace(',','').astype('Int64')
                record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', q4_term]], how='outer', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])
                record.loc[record['sj_div']=='IS', q4_term] = record.loc[record['sj_div']=='IS','FY'+str(y)]-record.loc[record['sj_div']=='IS', q4_term]
                record.loc[record['sj_div']=='BS', q4_term] = record.loc[record['sj_div']=='BS','FY'+str(y)]

        # check if there is data in the prev year, the same quarter
        prev_year_rec = dart.finstate(code, y-1, reprt_code=reprt_code_dict[q]) 
        prev_year_rec = post_process(prev_year_rec)
        if len(prev_year_rec) == 0 and 'frmtrm_amount' in rec.columns: 
            prev_term = str(y-1)+'_'+str(q)+'Q'
            # add only IS data
            rec.loc[rec['sj_div']=='IS', prev_term] = rec.loc[rec['sj_div']=='IS', 'frmtrm_amount'].str.replace(',','').astype('Int64')
            record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', prev_term]], how='outer', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])

            if q == 3 and 'frmtrm_add_amount' in rec.columns:
                if 'FY'+str(y-1) in record.columns:
                    last_q4_term = str(y-1)+'_4Q'
                    rec.loc[rec['sj_div']=='IS', last_q4_term] = rec.loc[rec['sj_div']=='IS','frmtrm_add_amount'].str.replace(',','').astype('Int64')
                    record = pd.merge(record, rec[['stock_code', 'fs_div', 'account_nm', last_q4_term]], how='outer', left_on=['stock_code', 'fs_div', 'account_nm'], right_on=['stock_code', 'fs_div', 'account_nm'])
                    record.loc[record['sj_div']=='IS', last_q4_term] = record.loc[record['sj_div']=='IS','FY'+str(y-1)]-record.loc[record['sj_div']=='IS', last_q4_term]
                    record.loc[record['sj_div']=='BS', last_q4_term] = record.loc[record['sj_div']=='BS','FY'+str(y-1)]

        y, q = get_prev_quarter_except_FY(y, q)
        rec = dart.finstate(code, y, reprt_code=reprt_code_dict[q])
        rec = post_process(rec)
    
    # post process
    record.rename(columns={'stock_code':'code', }, inplace=True)
    record['account'] = record['account_nm'].apply(lambda x: ACCOUNT_NAME_DICTIONARY[x] if x in ACCOUNT_NAME_DICTIONARY.keys() else x)
    static_columns = ['code', 'fs_div', 'sj_div', 'account_nm', 'account']
    record = pd.concat([record[static_columns], record[record.columns.difference(static_columns)].sort_index(axis=1)], axis=1)

    message = 'success'
    return record, message

# %%
import time

df_krx = pd.read_feather('data/df_krx.feather')
sector = df_krx.index

dart_ind = 0
dart = OpenDartReader(dart_apis[dart_ind])

financial_reports = pd.DataFrame()
save_file_name = 'data/financial_reports_upto_'+str(datetime.date.today())+'.feather'
log_fie = 'data/data_collection_log.txt'

with open(log_fie, 'w') as f:
    f.write('Financial data collection log\n')

current_target_indicator = 2611
error_trial = 0
error_trial_limit = 10
sleep_time = 5

while True:
    try:
        code = sector[current_target_indicator]
        current_progress = str(datetime.datetime.now()) + ', no: ' + str(current_target_indicator) + ', code ' + code+' in process / '+df_krx['Name'][code]
        print(current_progress)
        with open(log_fie, 'a') as f:
            f.write(current_progress+'\n')

        if dart.find_corp_code(code) == None: 
            current_progress = '----> no: ' + str(current_target_indicator) + ', code ' + code+' not in corp_code, and therefore data not available / '+df_krx['Name'][code]
            print(current_progress)
            with open(log_fie, 'a') as f:
                f.write(current_progress+'\n')
            current_target_indicator += 1
            continue
    
        record, message = collect_financial_reports(dart, code)
        if message == 'success':
            financial_reports = pd.concat([financial_reports, record], ignore_index=True)
            financial_reports.to_feather(save_file_name)
        elif message == 'Data Not Available':
            current_progress = '----> no: ' + str(current_target_indicator) + ', code ' + code+' data not available, could be a financial institution / '+df_krx['Name'][code]
            print(current_progress)
            with open(log_fie, 'a') as f:
                f.write(current_progress+'\n')
        elif message == 'Currency Not in KRW':
            current_progress = '----> no: ' + str(current_target_indicator) + ', code ' + code+' currency not in KRW, skipping / '+df_krx['Name'][code]
            print(current_progress)
            with open(log_fie, 'a') as f:
                f.write(current_progress+'\n')
        else:
            raise Exception('ERROR in execution loop')

        time.sleep(sleep_time)
        current_target_indicator += 1
        error_trial = 0 # reset

    except Exception as e:
        if error_trial < error_trial_limit:
            error_trial += 1
            dart_ind += 1
            dart = OpenDartReader(dart_apis[dart_ind%3])

        else:
            raise Exception('ERROR TRIAL LIMIT REACHED - Entire Process Halted')
            # break

        current_progress = '----> no: ' + str(current_target_indicator) + ', code ' + code+' unknown exception; process suspended and to be re-tried / '+df_krx['Name'][code]
        print(current_progress)
        print(e)
        with open(log_fie, 'a') as f:
            f.write(current_progress+'\n')

        time.sleep(sleep_time*error_trial)

# display(financial_reports)



