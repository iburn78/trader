#%% 
# CA: Classification Analysis
from dataclasses import dataclass, asdict, field, fields
import pandas as pd
import numpy as np
import os
from html2image import Html2Image
from datetime import datetime

from trader.tools.dc_tools import _choose_unique_rows
from trader.tools.dictionary import KRW_UNIT

# ----------------------------------------------------------
# gen quartely data related
# ----------------------------------------------------------
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

def prev_quarter_str(date):
    y, q = date.year, (date.month - 1) // 3 + 1
    if q == 1:
        y -= 1
        q = 4
    else:
        q -= 1
    return f"{y}_{q}Q"
# ----------------------------------------------------------
# Classification Logic
# ----------------------------------------------------------
cv_threshold_prime = 0.4
cv_threshold = 1.0
criteria_dict = {
    'revenue_growth': [(15,7), 0.3], # percent (yoy), # count (e.g., 0.2 = 20% of quarters: to be multiplied by period)
    'revenue_stats': [np.nan, cv_threshold_prime, 0, np.nan], # size
    'opincome_stats': [np.nan, cv_threshold_prime, 0, np.nan], # size
    'opmargin_stats': [(20,10), cv_threshold_prime, 0, np.nan], # percent
    'nopincome_stats': [np.nan, cv_threshold, np.nan, np.nan], # size
    'asset_stats': [np.nan, cv_threshold, 0, np.nan], # size
    'debt_stats': [np.nan, cv_threshold, np.nan, np.nan], # size
    'equity_stats': [np.nan, cv_threshold, 0, np.nan], # size
    'liquid_asset_ratio_stats': [np.nan, cv_threshold, np.nan, np.nan], # percent
    'liquid_debt_ratio_stats': [np.nan, cv_threshold, np.nan, np.nan], # percent
    'debt_to_equity_ratio_stats': [200, cv_threshold, np.nan, np.nan] # percent
}
weight = [5, 2, 2, 5, 1, 1, 1, 1, 1, 1, 1] # weights for each criteria
top_N = 50 # top to add

# ----------------------------------------------------------
# Data Structure
# ----------------------------------------------------------
pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
df_krx_file = os.path.join(pd_, 'data_collect/data/df_krx.feather') 
df_krx = pd.read_feather(df_krx_file)

qa_db_file = os.path.join(pd_, 'data_collect/data/qa_db.pkl') 
qa_db = pd.read_pickle(qa_db_file)
info_db_file = os.path.join(pd_, 'data_collect/data/info_db.xlsx')

@dataclass
class StockInfo: 
    code: str 
    name: str = "" 
    GPT_response: str = "" 
    industry: str = "" 
    business_model: str = "" 
    products: str = "" 
    competitors: str = "" 
    issue1: str = "" 
    issue2: str = "" 
    issue3: str = "" 
    issue4: str = "" 
    issue5: str = "" 
    note: str = "" 
    updated: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def __str__(self):
        lines = []
        for field_ in fields(self):
            value = getattr(self, field_.name)
            if value is not None:
                if isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"{field_.name:<15}: {value}")
        return "\n".join(lines)

    def get_issues(self) -> str:
        issues = [self.issue1, self.issue2, self.issue3, self.issue4, self.issue5]
        return "\n".join(issue for issue in issues if issue)

class Info_DB:
    def __init__(self):
        self.load_from_disk()
    
    def load_from_disk(self):
        if os.path.exists(info_db_file):
            self.db = pd.read_excel(info_db_file, index_col="code", engine='openpyxl', dtype={'code':str})
        else:
            self.db = pd.DataFrame(columns=[f.name for f in fields(StockInfo)])
            self.db.set_index("code", inplace=True)
        self.db = self.db.fillna("").astype(str)

    def save_to_disk(self):
        self.db.to_excel(info_db_file, engine='openpyxl')

    def add_company(self, s: StockInfo):
        s.name = df_krx.loc[s.code, "Name"]
        s.updated = datetime.now().strftime("%Y-%m-%d")
        self.db.loc[s.code] = asdict(s)

    def read_company(self, code: str) -> StockInfo:
        if code in self.db.index:
            row_dict = self.db.loc[code].to_dict()
            row_dict['code'] = code
            return StockInfo(**row_dict)
        else: 
            return StockInfo(code)

def get_company_issues(code):
    idb = Info_DB()
    s = idb.read_company(code)
    issues = s.get_issues()
    prev = s.GPT_response
    date_updated = s.updated
    return issues, prev, date_updated

def save_GPT_response(code, response):
    idb = Info_DB()
    s = idb.read_company(code)
    s.GPT_response = response
    idb.add_company(s) # date_updated updated
    idb.save_to_disk()

# -------------------------------------------------------------
# pipeline: data → tables → HTML → image
# -------------------------------------------------------------
# Takes stock/quarter data from qa_db
# Calculates a few metrics (growth, margins, debt, etc.)
# Formats and colors them like a report
# Builds an HTML page with tables
# Takes a screenshot of that HTML
# Saves it as a PNG image

def get_periods(qa_db=qa_db): 
    return [i for i in qa_db.columns if 'Q' in i]

def _compare_logic(data_dict, criteria_dict, period:str):
    key = list(data_dict.keys())
    if key != list(criteria_dict.keys()):
        raise ValueError("Key mismatch between data_dict and criteria_dict")

    score = [0] * len(data_dict.keys())
    comment = [''] * len(data_dict.keys())

    # revenue growth
    idx = 0
    data = data_dict[key[idx]]
    crit = criteria_dict[key[idx]] 
    p = int(period.replace('Q',''))
    conditions = [
        data[1] <= int(p*crit[1]), 
    ]
    if all(conditions):
        if data[0] >= crit[0][0]:
            score[idx] = weight[idx]
        elif data[0] >= crit[0][1]:
            score[idx] = round(weight[idx]*(data[0]-crit[0][1])/(crit[0][0]-crit[0][1]), 1)
        else:
            score[idx] = 0
    if data[1] == 0:
        comment[idx] += 'N' # No negative growth'

    # revenue stats, opincome stats, asset stats, equity stats
    for idx in [1, 2, 5, 7]: 
        data = data_dict[key[idx]]
        crit = criteria_dict[key[idx]] 
        conditions = [
            data[1] <= crit[1], # cv
            data[2] >= crit[2], # slope
        ]
        if all(conditions):
            score[idx] = weight[idx]
        if data[3] >= 0:
            comment[idx] += 'A' # Acceration

    # opmargin stats
    for idx in [3]:
        data = data_dict[key[idx]]
        crit = criteria_dict[key[idx]] 
        conditions = [
            data[1] <= crit[1], # cv
            data[2] >= crit[2], # slope
        ]
        if all(conditions):
            if data[0] >= crit[0][0]:
                score[idx] = weight[idx]
            elif data[0] >= crit[0][1]:
                score[idx] = round(weight[idx]*(data[0]-crit[0][1])/(crit[0][0]-crit[0][1]), 1)
            else:
                score[idx] = 0
        if data[3] >= 0:
            comment[idx] += 'A' # Acceration

    # nopincome stats, debt stats, liquid_asset_ratio_stats, liquid_debt_ratio_stats
    for idx in [4, 6, 8, 9]:
        data = data_dict[key[idx]]
        crit = criteria_dict[key[idx]] 
        conditions = [
            data[1] <= crit[1], # cv
        ]
        if all(conditions):
            score[idx] = weight[idx]

    # debt_to_equity_ratio_stats
    for idx in [10]:
        data = data_dict[key[idx]]
        crit = criteria_dict[key[idx]] 
        conditions = [
            data[0] <= crit[0], # mean
            data[1] <= crit[1], # cv
        ]
        if all(conditions):
            score[idx] = weight[idx]
        if data[2] >= 0:
            comment[idx] += 'I' # Increasing
    
    return score, comment

def _classify_companies(codelist, criteria_dict, period:str, qa_db=qa_db):
    selected_companies = []
    scores_dict = {}
    for code in codelist:
        data_dict = qa_db.loc[code, period]
        if pd.isna(data_dict) == False:
            scores, comment = _compare_logic(data_dict, criteria_dict, period)
            if scores.count(0) == 0:
                selected = True
                selected_companies.append(code)
                # print(code, selected, sum(scores), scores, comment)
            else: 
                selected = False
                pass
            # print(code, selected, sum(scores), scores, comment)
            scores_dict[code] = {
                'selected': selected,
                'score': sum(scores),
                'result': scores,
                'comment': comment
            }
    scores_df = pd.DataFrame.from_dict(scores_dict, orient='index')
    scores_df = scores_df.sort_values(by='score', ascending=False) 
    return selected_companies, scores_df

def get_score_trend(criteria_dict = criteria_dict, df_krx = df_krx, qa_db = qa_db, top_N = top_N):
    codelist = qa_db.index.tolist()
    periods = get_periods(qa_db)

    all_selected_companies = []
    all_scores_dict = {}
    for period in periods:
        selected_companies, scores_df  = _classify_companies(codelist, criteria_dict, period)
        all_selected_companies += selected_companies
        all_scores_dict[period] = scores_df

    top_codes = []
    for period in periods: 
        top_codes += all_scores_dict[period].index[:top_N].tolist()

    codelist = list(set(all_selected_companies + top_codes))

    score_trend_df = pd.DataFrame(index = codelist, columns = ['name', 'selected', 'top'+str(top_N)]+periods)
    for code in score_trend_df.index:
        score_trend_df.loc[code, 'name'] = df_krx.loc[code, 'Name']
        selected = ''
        top = ''
        for period in periods:
            if code in all_scores_dict[period].index:
                score_trend_df.loc[code, period] = all_scores_dict[period].loc[code, 'score']
                selected += 'T' if all_scores_dict[period].loc[code, 'selected'] else '-'
                top += 'Y' if code in all_scores_dict[period].index[:top_N] else '-'
            else:
                selected += ' '
                top += ' '
        score_trend_df.loc[code, 'selected'] = selected
        score_trend_df.loc[code, 'top'+str(top_N)] = top

    score_trend_df['avg'] = pd.to_numeric(score_trend_df[periods].mean(axis=1)).round(2)
    score_trend_df = score_trend_df.sort_values(by='avg', ascending=False)
    return score_trend_df, all_scores_dict

# ----------------------------------------------------------
# Visualize datadict
# ----------------------------------------------------------
def _preprocess_showdata(data_dict):
    data_dict = data_dict.copy()
    rv = data_dict['revenue_growth']
    del data_dict['revenue_growth']

    stats = pd.DataFrame(data_dict, index = ['mean', 'cv', 'slope', 'acc']).T
    stats.index = stats.index.str.replace('_stats', '')
    stats.index = stats.index.str.replace('_ratio', '')
    stats.index = stats.index.str.replace('_', '.')

    # formatting
    stats['slope'] = stats['slope']/stats['mean'].abs()*100
    stats['acc'] = stats['acc']/stats['mean'].abs()*100

    def format_value(val):
        if pd.isna(val):
            return "–"
        return f"{int(val):,}" if abs(val) > 100 else f"{val:.2f}"

    def set_cv_color(val):
        if pd.isna(val):
            return "color: gray"
        if abs(val) >= 0.5:
            return "color: red; font-weight: bold"
        if abs(val) >= 0.2:
            return "color: gray; font-weight: bold"
        else:
            return "color: black; font-weight: bold"
    
    def set_sa_color(val):
        if pd.isna(val):
            return "color: gray"
        if val >= 2:
            return "color: black; font-weight: bold"
        elif val >= 0:
            return "color: gray; font-weight: bold"
        else:
            return "color: red; font-weight: bold" 

    styled = stats[['cv', 'slope', 'acc']].style.format(format_value).map(set_sa_color, subset=['slope', 'acc']).map(set_cv_color, subset=['cv'])
    return rv, stats, styled

def _gen_qdata(code, period:str, qa_db = qa_db):
    data_dict = qa_db.loc[code, period]
    if pd.isna(data_dict) or len(data_dict) == 0:
        return "", None
    meta = qa_db.loc[code, 'meta']
    rv, stats, styled = _preprocess_showdata(data_dict)
    p = int(period.replace("Q", ""))
    try:
        pct = round(rv[1]/p*100, 1)
    except:
        pct = "err"
    desc = meta['name'] + ' ' + code + ' / period: ' + period + ' / LQ: ' + meta['last_quarter'] + '\n'
    desc += f'revenue growth:   {rv[0]} %' + '\n'
    desc += f'dip (times):      {rv[1]} ({pct}%)' + '\n'
    desc += f"op margin:        {stats.loc['opmargin', 'mean']} %" + '\n'
    desc += f"debt to equity:   {stats.loc['debt.to.equity', 'mean']} %" 

    return desc, styled

def _gen_summary(code, period:str | None = None, qa_db = qa_db):
    if period is None:
        periods = get_periods()
    else: 
        periods = [period]
    meta = qa_db.loc[code, 'meta']
    
    summary = []  # collect rows of data across periods
    for period in periods:
        data_dict = qa_db.loc[code, period]
        if pd.isna(data_dict) or len(data_dict) == 0:
            continue
        rv, stats, _ = _preprocess_showdata(data_dict)
        p = int(period.replace("Q", ""))
        try:
            pct = round(rv[1]/p*100, 1)
        except:
            pct = "err"
        row = {
            'period': period,
            'revenue_growth': rv[0],
            'dip': f"{rv[1]} {pct}%",
            'opmargin': stats.loc['opmargin', 'mean'],
            'debt.to.equity': stats.loc['debt.to.equity', 'mean']
        }
        summary.append(row)

    if len(summary) == 0:
        # print('No data found for any period.')
        return '', pd.DataFrame()

    summary_df = pd.DataFrame(summary).set_index('period')

    def format_cell(val):
        if pd.isna(val):
            return "–"
        return f"{val:.2f}" if isinstance(val, float) else str(val)

    def highlight_negative(val):
        if isinstance(val, float) and val < 0:
            return "color: red"
        return "color: black"

    styled = summary_df.style.format(format_cell).map(highlight_negative)
    desc = f"{meta['name']} ({code})" + '\n' + f"Latest Quarter: {meta['last_quarter']}"

    return desc, styled
    
def gen_data_in_html(code):
    summary_desc, summary_df = _gen_summary(code)
    summary_desc = summary_desc.replace('\n', '<br>')
    summary_df = summary_df.to_html()

    qdata_desc_list = []
    qdata_df_list = []
    for period in get_periods():
        qdata_desc, qdata_df = _gen_qdata(code, period)
        if qdata_df != None: 
            qdata_desc_list.append(qdata_desc.replace('\n', '<br>'))
            qdata_df_list.append(qdata_df.to_html())
    
    left_html = summary_desc + "<br>" + summary_df + "<br>"
    center_html = ''
    right_html = ''
    for a, b in zip(qdata_desc_list[:1], qdata_df_list[:1]):
        left_html += a + "<br>" + b + "<br>"
    for a, b in zip(qdata_desc_list[1:3], qdata_df_list[1:3]):
        center_html += a + "<br>" + b + "<br>"
    for a, b in zip(qdata_desc_list[3:], qdata_df_list[3:]):
        right_html += a + "<br>" + b + "<br>"

    full_html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial; font-size: 14px; margin: 0; padding: 1px; background: white; }}
        table {{ border-collapse: collapse; }}
        th, td {{ border: 1px solid #ccc; padding: 2px 4px; text-align: center;}}
    </style>
    </head>
    <body>
    <div style="display: flex;">
        <div style="flex: 1; padding: 10px; border: 1px solid #ccc;">
            <p>{left_html}</p>
        </div>
        <div style="flex: 1; padding: 10px; border: 1px solid #ccc;">
            <p>{center_html}</p>
        </div>
        <div style="flex: 1; padding: 10px; border: 1px solid #ccc;">
            <p>{right_html}</p>
        </div>
    </div>
    </body>
    </html>
    """
    img_path = os.path.join(pd_, 'data_collect/cca/temp/')
    temp_html = os.path.join(img_path, 'temp.html')
    os.makedirs(img_path, exist_ok=True)
    filename = 'temp.png'
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(full_html)  

    hti = Html2Image(output_path=img_path)
    hti.screenshot(html_file=temp_html, save_as=filename, size=(1400, 900))
    os.remove(temp_html)

    return os.path.join(img_path, filename)

def styled_df_to_image(df):
    # Apply conditional formatting: negative numbers in bold red
    def style_negative(v):
        if isinstance(v, (int, float)) and v < 0:
            return 'color: red; font-weight: bold;'
        return ''

    styled_df = df.style.map(style_negative) \
    .format(lambda x: ('{0}'.format(x)).rstrip('0').rstrip('.') if isinstance(x, float) else x) \
    .set_table_attributes('border="1" class="dataframe"') \
    .set_table_styles([
        {'selector': 'th', 'props': [('font-size', '12px'), ('text-align', 'center')]},
        {'selector': 'td', 'props': [('font-size', '12px'), ('text-align', 'center')]},
    ])

    # Convert styled DataFrame to HTML
    full_html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial; font-size: 12px; margin: 0; padding: 5px; background: white; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; padding: 2px; text-align: center; }}
    </style>
    </head>
    <body>
        {styled_df.to_html()}
        <br>
        Run as of {datetime.now().strftime("%Y-%m-%d_%H:%M")}. <br>
        Note: If the databases have not been updated, PER, PBR, market cap, etc., may reflect the values as of the last database update (usually last night). Only the price shown in this table reflects the current run-time value.
    </body>
    </html>
    """

    img_path = os.path.join(pd_, 'data_collect/cca/temp/')
    temp_html = os.path.join(img_path, 'temp.html')
    os.makedirs(img_path, exist_ok=True)
    filename = 'temp.png'
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(full_html)  

    hti = Html2Image(output_path=img_path)
    hti.screenshot(html_file=temp_html, save_as=filename, size=(900, 1200))
    os.remove(temp_html)

    return os.path.join(img_path, filename)
