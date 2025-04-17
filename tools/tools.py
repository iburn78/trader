#%%
from trader.tools.dictionary import *
from math import log10
import seaborn as sns
import matplotlib.pyplot as plt
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import sqlite3
from matplotlib import font_manager
import platform
import datetime

def plot_company_financial_summary(db, code, path=None):
    quarter_cols= [s for s in db.columns.values if 'Q' in s]
    quarter_cols.sort()
    y = db.loc[(db['code']==code) & (db['fs_div']=='CFS'), ['account']+quarter_cols].drop_duplicates().set_index(['account'])
    if y.isnull().all().all():
        y = db.loc[(db['code']==code) & (db['fs_div']=='OFS'), ['account']+quarter_cols].drop_duplicates().set_index(['account'])
    if y.isnull().all().all():
        raise Exception('quarterly data of {} is empty.'.format(code))

    date_updated = str(db.loc[(db['code']==code) & (db['fs_div']=='CFS'), 'date_updated'].values[0])
    y.columns = [s.replace('2020','XX').replace('20','').replace('XX','20').replace('_','.') for s in quarter_cols]
    yiu = y/KRW_UNIT 
    yiu=_choose_unique_rows(yiu, 'account')

    yiu.loc['opmargin', :] = yiu.loc['operating_income']/yiu.loc['revenue'].replace(0, pd.NA)*100   # sometimes, revenue entry is zero, then it computes to '+- np.inf'
    yiu.loc['liquid_asset_ratio', :] = yiu.loc['liquid_assets']/yiu.loc['assets']*100
    yiu.loc['liquid_debt_ratio', :] = yiu.loc['liquid_debts']/yiu.loc['debts']*100
    yiu.loc['debt_to_equity_ratio', :] = yiu.loc['debts']/yiu.loc['equity']*100

    plt.close('all')
    f, ax = plt.subplots(4, 1, figsize=(20, 15), constrained_layout=True, gridspec_kw={'height_ratios': [5, 3, 3, 3]})
    f.set_constrained_layout_pads(w_pad=0, h_pad=0.1, hspace=0, wspace=0.)
    sns.set_theme(style="dark")
    sns.despine(left=True, bottom=False)
    _plot_barline(ax[0], yiu, 'revenue', 'operating_income', 'opmargin', 'profit_before_tax')
    _plot_barline(ax[1], yiu, 'assets', 'liquid_assets', 'liquid_asset_ratio')
    _plot_barline(ax[2], yiu, 'debts', 'liquid_debts', 'liquid_debt_ratio')
    _plot_barline(ax[3], yiu, 'equity', 'retained_earnings', 'debt_to_equity_ratio')

    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .. 
    df_krx = pd.read_feather(os.path.join(pd_, 'data_collection/data/df_krx.feather'))
    try: 
        name = df_krx['Name'][code]
    except Exception as e: 
        raise Exception('{} not in df_krx'.format(code))

    set_KoreanFonts()
    f.suptitle('Consolidated Financial Statement Summary - company: '+name+'('+code+') updated on '+date_updated, fontsize=14)

    if path==None: 
        plt.show()
    else: 
        plt.savefig(path)
        plt.close()

def plot_company_financial_summary2(fr_db, pr_db, code, path=None):
    quarter_cols= [s for s in fr_db.columns.values if 'Q' in s]
    quarter_cols.sort()
    fs_div_mode = 'CFS'
    y = fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), ['account']+quarter_cols].drop_duplicates().set_index(['account'])
    if y.isnull().all().all():
        fs_div_mode = 'OFS'
        y = fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), ['account']+quarter_cols].drop_duplicates().set_index(['account'])
        CFS_mode = False
    if y.isnull().all().all():
        raise Exception('quarterly data of {} is empty.'.format(code))

    date_updated = str(fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), 'date_updated'].values[0])
    y.columns = [s.replace('2020','XX').replace('20','').replace('XX','20').replace('_','.').replace('Q','') for s in quarter_cols]
    yiu = y/KRW_UNIT 
    yiu=_choose_unique_rows(yiu, 'account')

    yiu.loc['opmargin', :] = yiu.loc['operating_income']/yiu.loc['revenue'].replace(0, pd.NA)*100   # sometimes, revenue entry is zero, then it computes to '+- np.inf'
    yiu.loc['liquid_asset_ratio', :] = yiu.loc['liquid_assets']/yiu.loc['assets']*100
    yiu.loc['liquid_debt_ratio', :] = yiu.loc['liquid_debts']/yiu.loc['debts']*100
    yiu.loc['debt_to_equity_ratio', :] = yiu.loc['debts']/yiu.loc['equity']*100

    plt.close('all')
    cmap = sns.color_palette("Blues", as_cmap=True)
    f, ax = plt.subplots(5, 1, figsize=(20, 18), constrained_layout=True, gridspec_kw={'height_ratios': [4, 5, 3, 3, 3]})
    f.set_constrained_layout_pads(w_pad=0, h_pad=0.1, hspace=0, wspace=0.)
    qprices = _get_quarterly_prices(fr_db, pr_db, code, fs_div_mode)
    _plot_priceline(ax[0], qprices)
    _plot_barline2(ax[1], yiu, 'revenue', 'operating_income', 'opmargin', 'net_income', cc1=cmap(0.25), cc2=cmap(0.7))
    _plot_barline2(ax[2], yiu, 'assets', 'liquid_assets', 'liquid_asset_ratio', cc1=cmap(0.25), cc2=cmap(0.65))
    _plot_barline2(ax[3], yiu, 'debts', 'liquid_debts', 'liquid_debt_ratio', cc1=cmap(0.25), cc2=cmap(0.60))
    _plot_barline2(ax[4], yiu, 'equity', 'retained_earnings', 'debt_to_equity_ratio', cc1=cmap(0.25), cc2=cmap(0.55))

    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .. 
    df_krx = pd.read_feather(os.path.join(pd_, 'data_collection/data/df_krx.feather'))
    try: 
        name = df_krx['Name'][code]
    except Exception as e: 
        raise Exception('{} not in df_krx'.format(code))

    set_KoreanFonts()
    f.suptitle('Consolidated Financial Statement Summary - company: '+name+'('+code+') updated on '+date_updated, fontsize=14)
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
    if ax.get_yticklabels()[-1].get_text() is None or float(ax.get_yticklabels()[-1].get_text())==0: 
        t_ = 1
    else: 
        t_ = ax.get_yticklabels()[-1].get_position()[1] / float(ax.get_yticklabels()[-1].get_text())

    unit_list = ['uk_won','10 uk_won','100 uk_won','1,000 uk_won', 'jo_won', '10 jo_won', '100 jo_won']
    try: 
        unit_exp = unit_list[int(round(log10(t_)))]
    except IndexError:
        unit_exp = 'DATA SCALE ERROR'

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

def _plot_barline2(ax, data, y1, y2, y3, y4=None, cc1='lightskyblue', cc2='steelblue', cc3='r', cc4='k'):
    axr = ax.twinx()
    if y4 != None:
        tx = data.loc[y1].isnull()*data.loc[y2].isnull().values*data.loc[y4].isnull().values
    else: 
        tx = data.loc[y1].isnull()*data.loc[y2].isnull().values
    x = [s for s in data.columns.values if not tx[s]]

    sns.barplot(x=x, y=data.loc[y1, x], ax = ax, label=y1, color=cc1)
    ax.ticklabel_format(axis='y', scilimits=[-3, 3])
    if ax.get_yticklabels()[-1].get_text() is None or float(ax.get_yticklabels()[-1].get_text())==0: 
        t_ = 1
    else: 
        t_ = ax.get_yticklabels()[-1].get_position()[1] / float(ax.get_yticklabels()[-1].get_text())

    unit_list = ['uk won','10 uk won','100 uk won','1,000 uk won', 'jo won', '10 jo won', '100 jo won']
    try: 
        unit_exp = unit_list[int(round(log10(t_)))]
    except IndexError:
        unit_exp = 'DATA SCALE ERROR'

    for index, value in enumerate(data.loc[y1, x]):
        try:
            v = str(round(value/t_, 1))
            ax.text(index, value, v)
        except: 
            pass

    sns.barplot(x=x, y=data.loc[y2, x], ax = ax, label=y2, color=cc2)
    for index, value in enumerate(data.loc[y2, x]):
        try:
            v = str(round(value/t_, 1))
            ax.text(index, value, v)
        except: 
            pass

    if y4 != None:
        sns.lineplot(x=x, y=data.loc[y4, x], ax = ax, label=y4, color=cc4, marker='^')
        for index, value in enumerate(data.loc[y4, x]):
            try:
                v = str(round(value/t_, 1))
                ax.text(index, value, v)
            except: 
                pass

    axl = ax.legend(loc='upper left')
    for text in axl.get_texts():
        text.set_text(text.get_text().replace('_',' '))
    axl._legend_box.align = "left"
    axl.set_frame_on(False)
    ax.set(ylabel='')
    ax.set_yticks([])

    if y4 != None:
        ax.set_title(y1.replace('_', ' ') +', '+y2.replace('_', ' ') +', '+y4.replace('_', ' ') +', '+y3.replace('_', ' ') +' ('+unit_exp+')')
    else: 
        ax.set_title(y1.replace('_', ' ') +', '+y2.replace('_', ' ') +', '+y3.replace('_', ' ') +' ('+unit_exp+')')

    sns.lineplot(x=x, y=data.loc[y3, x], ax = axr, label=y3+'(%)', color=cc3, marker='o')
    for index, value in enumerate(data.loc[y3, x]):
        try:
            v = str(round(value))
            axr.text(index, value, v)
        except: 
            pass

    axrl = axr.legend(loc='upper left')
    for text in axrl.get_texts():
        text.set_text(text.get_text().replace('_',' '))
    axrl.set_bbox_to_anchor((0, 0.8))
    axrl._legend_box.align = "left"
    axrl.set_frame_on(False)

    axr.set(ylabel='')
    axr.set_yticks([])

    ax.set_xlim(-0.5, len(x) - 0.5)
    axr.set_xlim(-0.5, len(x) - 0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    axr.spines['top'].set_visible(False)
    axr.spines['right'].set_visible(False)
    axr.spines['left'].set_visible(False)
    ax.set_facecolor('whitesmoke')

def _choose_unique_rows(df, index_name):
    df.reset_index(drop=False, inplace=True)
    idx = df.groupby(df[index_name]).apply(lambda gp: gp.count(axis=1).idxmax())
    return df.loc[idx].set_index(index_name, drop=True)

def _get_quarterly_prices(fr_db, pr_db, code, fs_div_mode = 'CFS'):
    fr_code = fr_db.loc[(fr_db.code == code) & (fr_db.fs_div == fs_div_mode)] 
    non_empty_columns = fr_code.columns[fr_code.notna().any()].tolist()
    quarters = [i for i in non_empty_columns if 'Q' in i]
    quarters.sort()
    if len(quarters) > 0:
        sq = quarters[0]
        eq = quarters[-1]
        sday = pd.Timestamp(year = int(sq[:4]), month = (int(sq[-2])-1)*3+1, day = 1)
        eday = pd.Timestamp(year = int(eq[:4]), month = (int(eq[-2])-1)*3+1, day = 1) + pd.DateOffset(months=2) + pd.offsets.MonthEnd(0)
    else: 
        sq = None
        eq = None
        sday = pd.Timestamp.now().normalize()
        eday = pd.Timestamp.now().normalize()

    qprices = pd.DataFrame(pr_db[code])
    qprices = qprices.loc[(qprices.index >= sday) & (qprices.index <= eday) ]
    qprices = qprices.rename(columns={code: 'price'})
    qprices['quarter'] = qprices.index.year.astype(str).str[-2:] + '.' + qprices.index.quarter.astype(str) 
    return qprices

def _plot_priceline(ax, qprices):
    sns.lineplot(x='quarter', y='price', data=qprices, ax = ax, color="k")
    qm = qprices.groupby('quarter').mean().sort_index()['price'].tolist()
    for yt in ax.get_yticks():
        ax.axhline(y=yt, color='white', linewidth=0.7)
    ref_points = [i  for i in range(1, len(qm)-1) if (((qm[i] - qm[i-1]) * (qm[i+1] - qm[i])) < 0 )]    
    if len(qm) > 0: 
        ref_points.append(len(qm)-1)
    for i in ref_points:
        value = qm[i]
        try:
            v = str("{:,}".format(round(value)))
            ax.text(i-0.005*len(qm), value*(1.02), v)
        except: 
            pass
    ax.set_title('quarterly average prices')
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_xlim(-0.5, qprices['quarter'].nunique() - 0.5)
    # ax.yaxis.tick_right()
    ax.yaxis.tick_left()
    ax.yaxis.set_label_position('left')
    ax.tick_params(axis='y', direction='in', pad=-30)
    # ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_facecolor('whitesmoke')

def plot_last_quarter_prices(pr_db, code, path=None):
    plt.close('all')
    sns.set_theme(style="darkgrid")
    f, ax = plt.subplots(1, 1, figsize=(20, 5), constrained_layout=True)
    f.set_constrained_layout_pads(w_pad=0, h_pad=0.1, hspace=0, wspace=0.)

    pr = pr_db.loc[pr_db.index>=prev_quarter_start(), code]
    if len(pr.index)>0:
        date_updated = pr.index[-1].strftime('%Y-%m-%d')
    else: 
        date_updated = ''

    sns.lineplot(data=pr, ax=ax, color='k')
    ax.set_title('recent price movement')
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.tick_params(axis='y', direction='in', pad=-40)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .. 
    df_krx = pd.read_feather(os.path.join(pd_, 'data_collection/data/df_krx.feather'))
    try: 
        name = df_krx['Name'][code]
    except Exception as e: 
        raise Exception('{} not in df_krx'.format(code))

    set_KoreanFonts()
    f.suptitle('General Analysis - company: '+name+'('+code+') updated on '+date_updated, fontsize=14)

    if path==None: 
        plt.show()
    else: 
        plt.savefig(path)
        plt.close()

# merge new data and update existing data
# usage:
# A = merge_update(A, B, ['col1', 'col2'])

# below is much more moemory inefficient, so changed to the below one
# def merge_update_prev(A, B, index_cols=['code', 'fs_div', 'account_nm']):
#     C = A.merge(B, on=index_cols, how='outer', suffixes=('_x', ''))
#     for col in C.columns: 
#         if col[-2:] == '_x':
#             C[col[:-2]] = C[col[:-2]].fillna(C[col])
#             C.drop(col, axis=1, inplace=True)
#     return C

# the below one is more memory efficient and even faster
# def merge_update_option(A, B, index_cols=['code', 'fs_div', 'account_nm']):
#     A = A.set_index(index_cols)
#     B = B.set_index(index_cols)

#     # Rows in both A and B (to update)
#     common_idx = A.index.intersection(B.index)
#     A.update(B.loc[common_idx])

#     # Rows in B but not in A (to append)
#     new_idx = B.index.difference(A.index)
#     B_only = B.loc[new_idx]

#     # Drop all-NA columns to avoid FutureWarning
#     B_only = B_only.dropna(axis=1, how='all')

#     # Append only new rows
#     result = pd.concat([A, B_only], axis=0)

#     return result.reset_index()

def merge_update(A, F, P=None, index_cols=['code', 'fs_div', 'account_nm']):
    if P is None: 
        P = pd.DataFrame(columns=A.columns)

    # Ensure all columns are included
    all_columns = A.columns.union(F.columns).union(P.columns)
    A[all_columns.difference(A.columns)] = np.nan

    # Set index
    A.set_index(index_cols, inplace=True)
    F.set_index(index_cols, inplace=True)
    P.set_index(index_cols, inplace=True)

    # 1. Update A with non-NA values from P where index matches
    A.update(P)

    # 2. Add new rows from P not in A
    new_idx_P = P.index.difference(A.index)
    A = pd.concat([A, P.loc[new_idx_P]], axis=0)

    # 3. Overwrite or insert all rows from F
    A.loc[F.index] = F
    A = A.reset_index()
    return A

def generate_krx_data(sql_db_creation=True): 
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .. 
    df_krx_desc = fdr.StockListing('KRX-DESC')
    df_krx = fdr.StockListing('KRX')

    df_krx.drop(columns=['Close', 'ChangeCode', 'Changes', 'ChagesRatio', 'Open', 'High', 'Low', 'Volume', 'Amount'], inplace=True)
    cols_to_use = df_krx_desc.columns.difference(df_krx.columns).tolist()
    cols_to_use.append('Code')
    df_krx = df_krx.merge(df_krx_desc[cols_to_use], on='Code', how='left')
    df_krx = df_krx.set_index('Code')
    df_krx = df_krx[df_krx['MarketId'] != 'KNX']

    # df_krx=df_krx[~df_krx['Dept'].str.contains('관리')]   # remove companies in trouble
    df_krx.to_feather(os.path.join(pd_, 'data_collection/data/df_krx.feather'))

    if sql_db_creation: 
        df_krx_sql = df_krx.copy()
        conn = sqlite3.connect(os.path.join(pd_, 'data_collection/data/df_krx.db'))
        df_krx_sql['ListingDate'] = df_krx_sql['ListingDate'].dt.strftime('%Y-%m-%d')
        df_krx_sql.to_sql('krx_data', conn, if_exists='replace')

        conn.commit()
        conn.close()

    return df_krx

def log_print(log_file, message):
    print(message)
    with open(log_file, 'a') as f: # a new file would be created if there is no log_file / otherwise it will append with "a" option
        f.write(str(message)+'\n')

def prev_quarter_start(date: pd.Timestamp = None) -> pd.Timestamp:
    if date == None: 
        date = pd.Timestamp.now()
    month = (date.month - 1) // 3 * 3 - 2
    year = date.year if month > 0 else date.year - 1
    month = month if month > 0 else month + 12
    return pd.Timestamp(year, month, 1)

def null_checker(main_db, n):  # check if there are no data in nth quarter before from now
    tg_qt = nth_quarter_before(n)
    codelist = main_db['code'].unique()

    # Keep only necessary columns
    df = main_db[['code', tg_qt]].copy()
    # Drop rows that are not in the active codelist
    df = df[df['code'].isin(codelist)]
    # Group by code and check if all values for tg_qt are NaN
    null_flags = df.groupby('code')[tg_qt].apply(lambda x: x.isna().all())
    # Return only codes where all values are NaN
    return null_flags[null_flags].index.tolist()

def get_listed():
    listing_db = fdr.StockListing('KRX-DESC')

    listed = listing_db.loc[listing_db.ListingDate.notna()].copy()
    category_dict = pd.read_excel('category.xlsx').set_index('Sector')['Category'].to_dict()

    for a in set(listed.Sector.unique())-set(category_dict.keys()):
        category_dict[str(a)] = 'Uncategorized'
    ts = pd.Series(category_dict)
    ts.index.name = 'Sector'
    ts.name = 'Category'
    ts.to_excel('category.xlsx')

    listed['Category'] = None
    for key, val in category_dict.items():
        listed.loc[listed['Sector'] == str(key), 'Category'] = val

    if len(listed.loc[listed.Category.isna()]) > 0: 
        raise Exception('--- Category mapping error ---')

    stock_info = fdr.StockListing('KRX')
    mc = pd.to_numeric(stock_info['Marcap'], errors='coerce')
    cl = pd.to_numeric(stock_info['Close'], errors='coerce')
    stock_info['SharesOuts'] = mc/cl.replace(0, pd.NA)
    listed = pd.merge(listed, stock_info[['Code', 'SharesOuts']], on='Code', how='left')
    listed = listed.loc[listed.SharesOuts.notna()]
    if len(listed.loc[listed.SharesOuts.isna()]) > 0: 
        raise Exception('--- SharesOutstanding calculation error ---')

    listed = listed.drop(['Representative', 'HomePage', 'Region'], axis=1)
    return listed

def get_pr_changes(price_db_file):
    pr_db = pd.read_feather(price_db_file)

    def _calc_change(cur_date, prev_date):
        cp = pr_db.loc[pr_db.index >= cur_date].iloc[0]
        pp = pr_db.loc[pr_db.index >= prev_date].iloc[0]
        return cp/pp - 1

    pr_changes = pd.DataFrame(columns = pr_db.columns)

    cur_day = pr_db.index[-1]
    last_day = pr_db.index[-2]
    last_week = last_day - pd.Timedelta(weeks=1)
    last_month = last_day - pd.DateOffset(months=1)
    last_quarter = last_day - pd.DateOffset(months=3)
    last_year = last_day - pd.DateOffset(months=12)
    pr_changes.loc['cur_price'] = pr_db.iloc[-1]
    pr_changes.loc['last_day'] = _calc_change(cur_day, last_day)
    pr_changes.loc['last_week'] = _calc_change(cur_day, last_week)
    pr_changes.loc['last_month'] = _calc_change(cur_day, last_month)
    pr_changes.loc['last_quarter'] = _calc_change(cur_day, last_quarter)
    pr_changes.loc['last_year'] = _calc_change(cur_day, last_year)

    pr_changes = pr_changes.transpose()
    pr_changes.index.name = 'Code'

    return pr_changes, cur_day

def set_KoreanFonts():
    if platform.system() == 'Windows':
        # plt.rcParams['font.family'] = ['DejaVu Sans', 'Noto Sans KR', 'NanumGothic']
        plt.rcParams['font.family'] = ['DejaVu Sans', 'NanumGothic']
        # plt.rcParams['font.weight'] = 'bold'
    elif platform.system() == 'Linux':
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Noto Sans CJK JP']
        # font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
        # font_prop = font_manager.FontProperties(fname=font_path)
        # plt.rcParams['font.family'] = font_prop.get_name()
        # plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
    else:
        raise Exception("Running on another OS")
    return None

def nearest_midnight(offset=0):
    current_time_kst = pd.Timestamp.now(tz='Asia/Seoul')

    # Determine the nearest midnight date based on current time
    if current_time_kst.hour < 12:  # If before noon
        nearest_midnight_date = current_time_kst.normalize().date()  # Today's date
    else:
        nearest_midnight_date = (current_time_kst + pd.Timedelta(days=1)).normalize().date()  # Tomorrow's date

    # Adjust for the offset
    adjusted_date = nearest_midnight_date + pd.Timedelta(days=offset)

    return adjusted_date

def get_krx_unique_update_list(dart, start, end):
    res = dart.list(start=start, end=end, kind='A') # works only withn three month gap between start_day and end_day
    if len(res) >0 :
        res = res['stock_code'].unique()
        res = res[res.astype(bool)].tolist()
    else: 
        res = []
    return res

def get_name_from_code(code, df_krx=None): 
    if df_krx is None: 
        pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        df_krx = pd.read_feather(os.path.join(pd_, 'data_collection/data/df_krx.feather'))
    if code not in df_krx.index:
        return 'Name_not_found'
    else: 
        return df_krx.loc[code, 'Name']

def get_market_and_rank(code, df_krx=None):
    if df_krx is None: 
        pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        df_krx = pd.read_feather(os.path.join(pd_, 'data_collection/data/df_krx.feather'))

    market = df_krx.loc[code, 'Market']
    tdf_ = df_krx.loc[df_krx['Market'] == market].reset_index()
    rank = tdf_.sort_values(by='Marcap', ascending=False).loc[tdf_['Code'] == code].index[0]+1
    return market, rank

def lookup_names_from_codelist(codelist, df_krx):
    res = []
    for x in codelist:
        if x in df_krx.index:
            res.append(df_krx.loc[x]['Name'])
        else: 
            res.append(f'delisted {x}')
    return res

def return_list_within_rank(codelist, RNK_LIM, df_krx):
    df_sorted = df_krx.sort_values(by='Marcap', ascending=False)
    return [i for i in codelist if i in df_sorted.index[:RNK_LIM]] 

def code_desc(pr_DB, code, range): 
    pr_date = pr_DB[code].index[-1]
    price = pr_DB.loc[pr_date, [code]].values[0]
    lb, ub = range
    if (price >= lb) and (price <= ub):
        status = f'price with in range ({lb}, {ub})'
    elif lb > price: 
        status = f'price LOWER than {lb}: need attention!'
    elif price > ub:
        status = f'price HIGHER than {ub}: check'
    else:
        status = f'error - range ({lb}, {ub})' 
    return pr_date.strftime('%Y-%m-%d'), status

def nth_quarter_before(n: int = 0):
    t_ = pd.Timestamp.now()-pd.DateOffset(months=3*n)
    return f'{t_.year}_{t_.quarter}Q'

def rank_counter(n, lang='E'):
    if lang=='E': 
        if 11 <= n % 100 <= 13:  # Special case for 11th, 12th, 13th
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"
    if lang=='K':
        return f"{n}위"

def git_timestamp():
    import subprocess

    timestamp = int(subprocess.check_output(["git", "log", "-1", "--format=%ct"]))
    commit_time = datetime.datetime.fromtimestamp(timestamp)
    now = datetime.datetime.now()
    if now - commit_time > datetime.timedelta(hours=24):
        print("####### CHECK DATA #######")
        print("Last git-commit was older than 24 hours.")
        print("Last commit time:", commit_time.strftime("%Y-%m-%d %H:%M:%S"))
        return False
    else:
        return True

def get_main_financial_reports_db():
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    # main_db_file = os.path.join(pd_, 'data_collection/data/financial_reports_main.feather') 
    main_db_file1 = os.path.join(pd_, 'data_collection/data/financial_reports_main1.feather') 
    main_db_file2 = os.path.join(pd_, 'data_collection/data/financial_reports_main2.feather') 
    main_db_file3 = os.path.join(pd_, 'data_collection/data/financial_reports_main3.feather') 
    
    # main_db = pd.read_feather(main_db_file)
    main_db1 = pd.read_feather(main_db_file1)
    main_db2 = pd.read_feather(main_db_file2)
    main_db3 = pd.read_feather(main_db_file3)

    main_db = pd.concat([main_db1, main_db2, main_db3], axis=0)
    return main_db

def save_main_financial_reports_db(main_db):
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    main_db_file1 = os.path.join(pd_, 'data_collection/data/financial_reports_main1.feather') 
    main_db_file2 = os.path.join(pd_, 'data_collection/data/financial_reports_main2.feather') 
    main_db_file3 = os.path.join(pd_, 'data_collection/data/financial_reports_main3.feather') 

    CHUNK_SIZE = int(len(main_db)/3)
    main_db1 = main_db.iloc[:CHUNK_SIZE]
    main_db2 = main_db.iloc[CHUNK_SIZE:CHUNK_SIZE*2]
    main_db3 = main_db.iloc[CHUNK_SIZE*2:]
    
    main_db1.to_feather(main_db_file1)
    main_db2.to_feather(main_db_file2)
    main_db3.to_feather(main_db_file3)
    return True

def get_dbs(check_time=True):
    if check_time:
        if not git_timestamp():
            raise Exception('git timestamp check failed')

    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    # price_db_file = os.path.join(pd_, 'data_collection/data/price_DB.feather') 
    df_krx_file = os.path.join(pd_, 'data_collection/data/df_krx.feather') 
    qa_db_file = os.path.join(pd_, 'data_collection/data/qa_db.pkl') 

    main_db = get_main_financial_reports_db()
    # price_db = pd.read_feather(price_db_file)
    df_krx = pd.read_feather(df_krx_file)
    try: 
        qa_db = pd.read_pickle(qa_db_file) # pickle format preserves exactly as it the dataframe was saved
    except:
        qa_db = None
    return main_db, df_krx, qa_db #, price_db
    
def get_quarterly_data(code, fr_db, unit=KRW_UNIT):  # fr_db = main_db or financial_reports_main
    quarter_cols= [s for s in fr_db.columns.values if 'Q' in s]
    quarter_cols.sort()
    fs_div_mode = 'CFS'
    y = fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), ['account']+quarter_cols].drop_duplicates().set_index(['account'])
    if y.isnull().all().all():
        fs_div_mode = 'OFS'
        y = fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), ['account']+quarter_cols].drop_duplicates().set_index(['account'])
    if y.isnull().all().all():
        return None

    # date_updated = str(fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), 'date_updated'].values[0])
    y.columns = [s.replace('2020','XX').replace('20','').replace('XX','20').replace('_','.').replace('Q','') for s in quarter_cols]
    yiu = y/unit
    yiu=_choose_unique_rows(yiu, 'account')
    yiu.loc['opmargin', :] = yiu.loc['operating_income']/yiu.loc['revenue'].replace(0, pd.NA)*100   # sometimes, revenue entry is zero, then it computes to '+- np.inf'
    yiu.loc['liquid_asset_ratio', :] = yiu.loc['liquid_assets']/yiu.loc['assets']*100
    yiu.loc['liquid_debt_ratio', :] = yiu.loc['liquid_debts']/yiu.loc['debts']*100
    yiu.loc['debt_to_equity_ratio', :] = yiu.loc['debts']/yiu.loc['equity']*100
    yiu.replace(0, np.nan, inplace=True)   # works both for int and float, and there is no truly zero value in financial data
    return yiu #, date_updated

def slope_and_acc(series: pd.Series):
    series = series.dropna().astype(float)
    x = np.arange(len(series))
    y = series.values

    if len(y) < 2:
        return np.nan, np.nan

    mean = np.mean(y)
    slope = np.polyfit(x, y, 1)[0]
    if len(x) > 2:
        acc = np.polyfit(x, y, 2)[0]
    else:
        acc = np.nan

    # "increasing" if slope > 0 else "decreasing" if slope < 0 else "flat",
    # "accelerating upward" if a > 0 else "accelerating downward" if a < 0 else "no acceleration"
    return slope, acc

def rounder(x):
    if x is None or pd.isna(x) or np.isinf(x):
        return np.nan
    elif isinstance(x, str):
        return x
    elif isinstance(x, (int, np.integer)):
        return x 
    elif isinstance(x, (float, np.floating)):
        if abs(x) >= 100: 
            return int(x)
        else:
            return round(x, 2)

def basic_stats(series: pd.Series):
    mean = series.mean()
    std = series.std()
    slope, acc = slope_and_acc(series)
    cv = std / mean if pd.notna(mean) and mean != 0 else np.nan
    lst = [mean, cv, slope, acc]
    return [rounder(x) for x in lst]
