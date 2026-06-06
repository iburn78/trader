# functions here are imported by files in prev
# originally in tools.py file

def _plot_company_financial_summary(db, code, path=None): # previous func 
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
    _plot_barline_prev(ax[0], yiu, 'revenue', 'operating_income', 'opmargin', 'profit_before_tax')
    _plot_barline_prev(ax[1], yiu, 'assets', 'liquid_assets', 'liquid_asset_ratio')
    _plot_barline_prev(ax[2], yiu, 'debts', 'liquid_debts', 'liquid_debt_ratio')
    _plot_barline_prev(ax[3], yiu, 'equity', 'retained_earnings', 'debt_to_equity_ratio')

    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .. 
    df_krx = pd.read_feather(os.path.join(pd_, 'data_collect/data/df_krx.feather'))
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

def _plot_barline_prev(ax, data, y1, y2, y3, y4=None):
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
    KRW_UNIT_STR = '10^8 KRW (uk-won)'
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

def get_df_krx():
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df_krx = pd.read_feather(os.path.join(pd_, 'data_collect/data/df_krx.feather'))
    return df_krx

def prev_quarter_start(date: pd.Timestamp = None) -> pd.Timestamp:
    if date == None: 
        date = pd.Timestamp.now()
    month = (date.month - 1) // 3 * 3 - 2
    year = date.year if month > 0 else date.year - 1
    month = month if month > 0 else month + 12
    return pd.Timestamp(year, month, 1)

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
    df_krx = pd.read_feather(os.path.join(pd_, 'data_collect/data/df_krx.feather'))
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
def get_listed():
    listing_db = fdr.StockListing('KRX-DESC')
    # sector information is no longer available
    # print(listing_db.Sector.unique())

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

    print(listed.loc[listed.Category.isna()])
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
        df_krx = pd.read_feather(os.path.join(pd_, 'data_collect/data/df_krx.feather'))
    if code not in df_krx.index:
        return 'Name_not_found'
    else: 
        return df_krx.loc[code, 'Name']

def get_market_and_rank(code, df_krx=None):
    if df_krx is None: 
        pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        df_krx = pd.read_feather(os.path.join(pd_, 'data_collect/data/df_krx.feather'))

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

def prev_quarter_str(date):
    y, q = date.year, (date.month - 1) // 3 + 1
    if q == 1:
        y -= 1
        q = 4
    else:
        q -= 1
    return f"{y}_{q}Q"

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

def get_dbs(check_time=True):
    if check_time:
        if not git_timestamp():
            raise Exception('git timestamp check failed')

    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    df_krx_file = os.path.join(pd_, 'data_collect/data/df_krx.feather') 
    qa_db_file = os.path.join(pd_, 'data_collect/data/qa_db.pkl') 

    main_db = get_main_financial_reports_db()
    df_krx = pd.read_feather(df_krx_file)
    try: 
        qa_db = pd.read_pickle(qa_db_file) # pickle format preserves exactly as it the dataframe was saved
    except:
        qa_db = None
    return main_db, df_krx, qa_db 

def get_price_db(): 
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    price_db_file = os.path.join(pd_, 'data_collect/data/price_DB.feather') 
    price_db = pd.read_feather(price_db_file)
    return price_db

def get_outshare_db():
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    outshare_DB_path = os.path.join(pd_, 'data_collect/data/outshare_DB.feather')
    outshare_DB = pd.read_feather(outshare_DB_path)
    return outshare_DB
    
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