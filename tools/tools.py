from .dictionary import *
from math import log10
import seaborn as sns
import matplotlib.pyplot as plt
import OpenDartReader 
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import datetime, time

def _collect_financial_reports(dart, code, duration=None): # duration as years

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
        # print(data_term)
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
        # print(data_term)
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
    static_columns = ['code', 'fs_div', 'sj_div', 'account_nm', 'account', 'date_updated']
    return pd.concat([reports[static_columns], reports[reports.columns.difference(static_columns)].sort_index(axis=1)], axis=1)

def _generate_financial_reports_set(sector, duration, log_file, save_file_name=None):
    dart_ind = 0
    dart = OpenDartReader(DART_APIS[dart_ind])

    financial_reports = pd.DataFrame()

    with open(log_file, 'a') as f:
        f.write('Financial data collection log\n')

    error_trial = 0
    error_trial_limit = 10
    sleep_time = 5

    for ix, code in enumerate(sector):
        try:
            current_progress = str(datetime.datetime.now()) + ', no: ' + str(ix) + ', code ' + code+' in process' # / '+df_krx['Name'][code]
            print(current_progress)
            with open(log_file, 'a') as f:
                f.write(current_progress+'\n')

            if dart.find_corp_code(code) == None: 
                current_progress = '----> no: ' + str(ix) + ', code ' + code+' not in corp_code, and therefore data not available' # / '+df_krx['Name'][code]
                print(current_progress)
                with open(log_file, 'a') as f:
                    f.write(current_progress+'\n')
                continue
    
            record, message = _collect_financial_reports(dart, code, duration)
            if message == 'success':
                financial_reports = pd.concat([financial_reports, record], ignore_index=True)
                if save_file_name != None:
                    financial_reports.to_feather(save_file_name)
            elif message == 'Data Not Available':
                current_progress = '----> no: ' + str(ix) + ', code ' + code+' data not available, could be a financial institution' # / '+df_krx['Name'][code]
                print(current_progress)
                with open(log_file, 'a') as f:
                    f.write(current_progress+'\n')
            elif message == 'Currency Not in KRW':
                current_progress = '----> no: ' + str(ix) + ', code ' + code+' currency not in KRW, skipping' # / '+df_krx['Name'][code]
                print(current_progress)
                with open(log_file, 'a') as f:
                    f.write(current_progress+'\n')
            else:
                raise Exception('ERROR in execution loop')

            time.sleep(sleep_time)
            error_trial = 0 # reset

        except Exception as e:
            if error_trial < error_trial_limit:
                error_trial += 1
                dart_ind += 1
                dart = OpenDartReader(DART_APIS[dart_ind%3])

            else:
                raise Exception('ERROR TRIAL LIMIT REACHED - Entire Process Halted')
                # break

            current_progress = '----> no: ' + str(ix) + ', code ' + code+' unknown exception; process suspended and to be re-tried' # / '+df_krx['Name'][code]
            print(current_progress)
            print(e)
            with open(log_file, 'a') as f:
                f.write(current_progress+'\n')

            time.sleep(sleep_time*error_trial)

    return _sort_columns_financial_reports(financial_reports)


def generate_update_db(log_file, days = None, start_day = None):
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    if days != None:
        start_day = (datetime.datetime.today() - datetime.timedelta(days = days)).strftime('%Y-%m-%d')
    dart = OpenDartReader(DART_APIS[0])
    ls = dart.list(start=start_day, end=today, kind='A')
    if len(ls) == 0:
        print('no new data to update')
        return None

    full_rescan_code = ls.loc[ls['report_nm'].str.contains(MODIFIED_REPORT)]['stock_code'].values
    full_rescan_code = np.unique(full_rescan_code[full_rescan_code.astype(bool)])
    partial_rescan_code = ls.loc[~ls['report_nm'].str.contains(MODIFIED_REPORT)]['stock_code'].values
    partial_rescan_code = np.unique(partial_rescan_code[partial_rescan_code.astype(bool)])
    status = '\nFull rescan codes are {} items: {}'.format(len(full_rescan_code), full_rescan_code) + '\nPartial rescan codes are {} items: {}'.format(len(partial_rescan_code), partial_rescan_code)
    status = '\n--------------------------\n'+str(datetime.datetime.today())+status
    with open(log_file, 'a') as f:
        f.write(status +'\n')
    print(status)

    db_f = _generate_financial_reports_set(full_rescan_code, None, log_file, None)
    db_p = _generate_financial_reports_set(partial_rescan_code, 1, log_file, None) # 1 year

    return _sort_columns_financial_reports(pd.concat([db_f, db_p], ignore_index=True))


def plot_company_financial_summary(db, code, path=None):
    quarter_cols= [s for s in db.columns.values if 'Q' in s]
    y = db.loc[(db['code']==code) & (db['fs_div']=='CFS'), ['account']+quarter_cols].set_index(['account'])
    date_updated = str(db.loc[(db['code']==code) & (db['fs_div']=='CFS'), 'date_updated'].values[0])
    y.columns = [s.replace('2020','XX').replace('20','').replace('XX','20').replace('_','.') for s in quarter_cols]
    yiu = y/KRW_UNIT 

    yiu.loc['opmargin', :] = yiu.loc['operating_income']/yiu.loc['revenue'].replace(0, pd.NA)*100   # sometimes, revenue entry is zero, then it computes to '+- np.inf'
    yiu.loc['liquid_asset_ratio', :] = yiu.loc['liquid_assets']/yiu.loc['assets']*100
    yiu.loc['liquid_debt_ratio', :] = yiu.loc['liquid_debts']/yiu.loc['debts']*100
    yiu.loc['debt_to_equity_ratio', :] = yiu.loc['debts']/yiu.loc['equity']*100

    f, ax = plt.subplots(4, 1, figsize=(20, 15), constrained_layout=True, gridspec_kw={'height_ratios': [5, 3, 3, 3]})
    f.set_constrained_layout_pads(w_pad=0, h_pad=0.1, hspace=0, wspace=0.)
    sns.set_theme(style="dark")
    sns.despine(left=True, bottom=False)
    _plot_barline(ax[0], yiu, 'revenue', 'operating_income', 'opmargin', 'profit_before_tax')
    _plot_barline(ax[1], yiu, 'assets', 'liquid_assets', 'liquid_asset_ratio')
    _plot_barline(ax[2], yiu, 'debts', 'liquid_debts', 'liquid_debt_ratio')
    _plot_barline(ax[3], yiu, 'equity', 'retained_earnings', 'debt_to_equity_ratio')

    df_krx = pd.read_feather('data/df_krx.feather')
    name = df_krx['Name'][code]

    kor_ft={'font':'Malgun Gothic'}
    f.suptitle('Consolidated Financial Statement Summary - company: '+name+'('+code+') updated on '+date_updated, fontsize=14, fontdict=kor_ft)
    if path==None: 
        plt.show()
    else: 
        plt.savefig(path)
        plt.close()

def _plot_barline(ax, data, y1, y2, y3, y4=None):
    axr = ax.twinx()
    if y4 != None:
        tx = data.loc[y1].isnull()*data.loc[y2].isnull().values*data.loc[y4].isnull().values
    else: 
        tx = data.loc[y1].isnull()*data.loc[y2].isnull().values
    x = [s for s in data.columns.values if not tx[s]]

    sns.set_color_codes("pastel")
    sns.barplot(x=x, y=data.loc[y1, x], ax = ax, label=y1, color="b")
    ax.ticklabel_format(axis='y', scilimits=[-3, 3])
    t_ = ax.get_yticklabels()[-1].get_position()[1] / float(ax.get_yticklabels()[-1].get_text())

    unit_list = ['uk_won','10 uk_won','100 uk_won','1,000 uk_won', 'jo_won', '10 jo_won', '100 jo_won']
    unit_exp = unit_list[int(log10(t_))]

    for index, value in enumerate(data.loc[y1, x]):
        try:
            v = str(round(value/t_, 1))
            ax.text(index, value, v)
        except: 
            pass

    sns.set_color_codes("muted")
    sns.barplot(x=x, y=data.loc[y2, x], ax = ax, label=y2, color="b")
    for index, value in enumerate(data.loc[y2, x]):
        try:
            v = str(round(value/t_, 1))
            ax.text(index, value, v)
        except: 
            pass

    if y4 != None:
        sns.lineplot(x=x, y=data.loc[y4, x], ax = ax, label=y4, color="k", marker='^')
        for index, value in enumerate(data.loc[y4, x]):
            try:
                v = str(round(value/t_, 1))
                ax.text(index, value, v)
            except: 
                pass

    ax.legend(ncol=1, loc="upper left", frameon=False)
    ax.set(ylabel=KRW_UNIT_STR)
    if y4 != None:
        ax.set_title(y1+', '+y2+', '+y4+', '+y3+' (unit: '+unit_exp+')')
    else: 
        ax.set_title(y1+', '+y2+', '+y3+' (unit: '+unit_exp+')')

    sns.lineplot(x=x, y=data.loc[y3, x], ax = axr, label=y3+'(%)', color="r", marker='o')
    for index, value in enumerate(data.loc[y3, x]):
        try:
            v = str(round(value, 1))
            axr.text(index, value, v)
        except: 
            pass

    axr.legend(ncol=1, loc="upper left", frameon=False, bbox_to_anchor=(0, 0.8))
    axr.set(ylabel="percent(%)")

    ax.set_xlim(-0.5, len(x) - 0.5)
    axr.set_xlim(-0.5, len(x) - 0.5)
    sns.despine(left=True, bottom=False)

# merge new data and update existing data
# usage:
# A = merge_update(A, B, ['col1', 'col2'])

def merge_update(A, B, index_cols=['code', 'fs_div', 'account_nm']):
    C = A.merge(B, on=index_cols, how='outer', suffixes=('_x', ''))
    for col in C.columns: 
        if col[-2:] == '_x':
            C[col[:-2]] = C[col[:-2]].fillna(C[col])
            C.drop(col, axis=1, inplace=True)
    return C

def generate_krx_data(): 
    df_krx_desc = fdr.StockListing('KRX-DESC')
    df_krx = fdr.StockListing('KRX')

    df_krx.drop(columns=['Close', 'ChangeCode', 'Changes', 'ChagesRatio', 'Open', 'High', 'Low', 'Volume', 'Amount'], inplace=True)
    cols_to_use = df_krx_desc.columns.difference(df_krx.columns).tolist()
    cols_to_use.append('Code')
    df_krx = df_krx.merge(df_krx_desc[cols_to_use], on='Code', how='left')
    df_krx = df_krx.set_index('Code')

    df_krx=df_krx[~df_krx['Dept'].str.contains('관리')]   # remove companies in trouble
    df_krx.to_feather('data/df_krx.feather')

    return None

def log_print(log_file, message):
    print(message)
    with open(log_file, 'a') as f: # a new file would be created if there is no log_file / otherwise it will append with "a" option
        f.write(str(message)+'\n')