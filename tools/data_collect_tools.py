#%%
from trader.tools.dictionary import KRW_UNIT
from math import log10
import seaborn as sns
import matplotlib.pyplot as plt
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import sqlite3
import platform
import datetime
import os
import io

def plot_company_financial_summary(fr_db, pr_db, code, path=None, start_quarter='2016_1Q'): # use 2016 1Q as start quarter (dart api data starts from 2015 anyway)
    quarter_cols= [s for s in fr_db.columns.values if 'Q' in s]
    quarter_cols.sort()
    if start_quarter != None:
        quarter_cols = [q for q in quarter_cols if q >= start_quarter]
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
    f.get_layout_engine().set(w_pad=0, h_pad=0.1, hspace=0, wspace=0.)
    qprices = _get_quarterly_prices(fr_db, pr_db, code, fs_div_mode)
    _plot_priceline(ax[0], qprices)
    _plot_barline(ax[1], yiu, 'revenue', 'operating_income', 'opmargin', 'net_income', cc1=cmap(0.25), cc2=cmap(0.7))
    _plot_barline(ax[2], yiu, 'assets', 'liquid_assets', 'liquid_asset_ratio', cc1=cmap(0.25), cc2=cmap(0.65))
    _plot_barline(ax[3], yiu, 'debts', 'liquid_debts', 'liquid_debt_ratio', cc1=cmap(0.25), cc2=cmap(0.60))
    _plot_barline(ax[4], yiu, 'equity', 'retained_earnings', 'debt_to_equity_ratio', cc1=cmap(0.25), cc2=cmap(0.55))

    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .. 
    df_krx = pd.read_feather(os.path.join(pd_, 'data_collect/data/df_krx.feather'))
    try: 
        name = df_krx['Name'][code]
    except Exception as e: 
        raise Exception('{} not in df_krx'.format(code))

    set_KoreanFonts()
    f.suptitle('Consolidated Financial Statement Summary - company: '+name+'('+code+') updated on '+date_updated, fontsize=14)
    if path==None: 
        # plt.show()
        img_stream = io.BytesIO()
        plt.savefig(img_stream, format='png', bbox_inches='tight')
        plt.close(f)
        img_stream.seek(0)
        return img_stream
    else: 
        plt.savefig(path)
        plt.close()

def _plot_barline(ax, data, y1, y2, y3, y4=None, cc1='lightskyblue', cc2='steelblue', cc3='r', cc4='k'):

    if y4 != None:
        tx = data.loc[y1].isnull() & data.loc[y2].isnull() & data.loc[y4].isnull()
    else: 
        tx = data.loc[y1].isnull() & data.loc[y2].isnull()
    x = [s for s in data.columns.values if not tx[s]]

    if not x:
        ax.set_title("No financial data available")

        ax.set_xticks([])
        ax.set_yticks([])

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.set_facecolor('whitesmoke')
        return

    axr = ax.twinx()

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
    # to be deprecated: groupby().apply()
    # idx = df.groupby(df[index_name]).apply(lambda gp: gp.count(axis=1).idxmax())
    valid_count = df.notna().sum(axis=1)
    idx = valid_count.groupby(df[index_name]).idxmax()
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

def get_quarterly_data(code, fr_db, unit=KRW_UNIT, native=False):  # fr_db = main_db or financial_reports_main
    quarter_cols= [s for s in fr_db.columns.values if 'Q' in s]
    quarter_cols.sort()
    fs_div_mode = 'CFS'
    y = fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), ['account']+quarter_cols].drop_duplicates().set_index(['account'])
    if y.isnull().all().all():
        fs_div_mode = 'OFS'
        y = fr_db.loc[(fr_db['code']==code) & (fr_db['fs_div']==fs_div_mode), ['account']+quarter_cols].drop_duplicates().set_index(['account'])
    if y.isnull().all().all():
        return None
    if native: 
        return y.dropna(axis=1, how='all')

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

def merge_update(A, F=None, P=None, index_cols=['code', 'fs_div', 'account_nm']):
    if F is None: 
        F = pd.DataFrame(columns=A.columns)
    if P is None: 
        P = pd.DataFrame(columns=A.columns)
    
    if len(F) == 0 and len(P) == 0: return A

    # Ensure all columns are included
    all_columns = A.columns.union(F.columns).union(P.columns)
    A[all_columns.difference(A.columns)] = np.nan

    # Set index
    A.set_index(index_cols, inplace=True)
    
    if not P.empty:
        P.set_index(index_cols, inplace=True)
        # Update A with non-NA values from P where index matches
        A.update(P)

        # Add new rows from P not in A
        new_idx_P = P.index.difference(A.index)
        A = pd.concat([A, P.loc[new_idx_P]], axis=0)

    if not F.empty:
        F.set_index(index_cols, inplace=True)
        # Overwrite or insert all rows from F

        # (Step 1) Drop rows from A that are being replaced
        A = A.drop(F.index.intersection(A.index), errors='ignore')

        # (Step 2) Append F — it will insert or replace
        # make sure to drop all-NA columns to avoid FutureWarning
        F_filtered = F.dropna(axis=1, how='all')
        if not F_filtered.empty:
            A = pd.concat([A, F_filtered])

    # Reset index to make it a regular DataFrame
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
    df_krx.to_feather(os.path.join(pd_, 'data_collect/data/df_krx.feather'))

    # this db is used in TNP project for code search in node
    if sql_db_creation: 
        df_krx_sql = df_krx.copy()
        plots_dir = os.path.join(pd_, 'data_collect/plots') 
        os.makedirs(plots_dir, exist_ok=True)
        conn = sqlite3.connect(os.path.join(plots_dir, 'df_krx.db'))
        df_krx_sql['ListingDate'] = df_krx_sql['ListingDate'].dt.strftime('%Y-%m-%d')
        df_krx_sql.to_sql('krx_data', conn, if_exists='replace')

        conn.commit()
        conn.close()

        # also, leave a timestamp for TNP project 
        with open(os.path.join(plots_dir, 'update_info.txt'), 'w') as f:
            f.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    return df_krx

def log_print(log_file, message):
    print(message)
    # a new file would be created if there is no log_file / otherwise it will append with "a" option
    # should create target dir (e.g., "/log")
    with open(log_file, 'a') as f: 
        f.write(str(message)+'\n')

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

def set_KoreanFonts():
    os_ = platform.system()
    if os_ == 'Windows':
        plt.rcParams['font.family'] = ['DejaVu Sans', 'NanumGothic']
    elif os_ == 'Linux':
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Noto Sans CJK JP']
    elif os_ == 'Darwin':   # macOS
        plt.rcParams['font.family'] = ['DejaVu Sans', 'AppleGothic']
    else:
        raise Exception(f"Unsupported OS: {os_}")
    return None

def nth_quarter_before(n: int = 0):
    t_ = pd.Timestamp.now()-pd.DateOffset(months=3*n)
    return f'{t_.year}_{t_.quarter}Q'

def get_main_financial_reports_db():
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    # # main_db_file = os.path.join(pd_, 'data_collect/data/financial_reports_main.feather') 
    # main_db_file1 = os.path.join(pd_, 'data_collect/data/financial_reports_main1.feather') 
    # main_db_file2 = os.path.join(pd_, 'data_collect/data/financial_reports_main2.feather') 
    # main_db_file3 = os.path.join(pd_, 'data_collect/data/financial_reports_main3.feather') 
    
    # # main_db = pd.read_feather(main_db_file)
    # main_db1 = pd.read_feather(main_db_file1)
    # main_db2 = pd.read_feather(main_db_file2)
    # main_db3 = pd.read_feather(main_db_file3)

    # main_db = pd.concat([main_db1, main_db2, main_db3], axis=0)

    # git file size limit ~100Mb, so need to compress better using parquet
    # with parquet, no need to split (yet)
    main_db_file = os.path.join(pd_, 'data_collect/data/financial_reports_main.parquet') 
    main_db = pd.read_parquet(main_db_file)

    return main_db

def save_main_financial_reports_db(main_db: pd.DataFrame):
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    # main_db_file1 = os.path.join(pd_, 'data_collect/data/financial_reports_main1.feather') 
    # main_db_file2 = os.path.join(pd_, 'data_collect/data/financial_reports_main2.feather') 
    # main_db_file3 = os.path.join(pd_, 'data_collect/data/financial_reports_main3.feather') 

    # CHUNK_SIZE = int(len(main_db)/3)
    # main_db1 = main_db.iloc[:CHUNK_SIZE]
    # main_db2 = main_db.iloc[CHUNK_SIZE:CHUNK_SIZE*2]
    # main_db3 = main_db.iloc[CHUNK_SIZE*2:]
    
    # main_db1.to_feather(main_db_file1)
    # main_db2.to_feather(main_db_file2)
    # main_db3.to_feather(main_db_file3)

    main_db_file = os.path.join(pd_, 'data_collect/data/financial_reports_main.parquet') 
    main_db.to_parquet(main_db_file, compression='zstd') 

    return True

def create_plots_from_plot_gen_control(plot_gen_control_file):
    # need to have price_db
    # need to create 'plots' directory 

    if not os.path.exists(plot_gen_control_file):
        print('----------------------------------------------------')
        print('no codelist to create plots (target file not exist).')
        print('----------------------------------------------------')
        # raise FileNotFoundError('***** no codelist to create plots (target file not exist). *****')
        return
    plot_ctrl = np.load(plot_gen_control_file, allow_pickle=True)

    main_db = get_main_financial_reports_db()
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .. 
    price_dbfile = os.path.join(pd_, 'data_collect/data/price_db.feather') 
    price_db = pd.read_feather(price_dbfile)

    # -----------------------------------------------------
    # in case to regenerate all plots use
    # codelist = fdr.StockListing('KRX')['Code'].tolist()
    # plot_ctrl = codelist
    # -----------------------------------------------------
    l = len(plot_ctrl)
    for i, code in enumerate(plot_ctrl):
        print('{} | {}/{}'.format(code, i+1, l))
        path = os.path.join(pd_, 'data_collect/plots/'+code+'.png')
        try:
            plot_company_financial_summary(main_db, price_db, code, path)
        except Exception as error:
            print(str(datetime.datetime.now())+' | '+code+' | '+str(error))
            if os.path.exists(path):
                os.remove(path)

    os.remove(plot_gen_control_file)
