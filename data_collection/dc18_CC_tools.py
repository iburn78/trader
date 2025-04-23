#%% 
import pandas as pd
import numpy as np
import os

pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
qa_db_file = os.path.join(pd_, 'data_collection/data/qa_db.pkl') 
qa_db = pd.read_pickle(qa_db_file)

# visualize datadict (Only works in jupyter notebook)
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
            return "color: white; font-weight: bold"
    
    def set_sa_color(val):
        if pd.isna(val):
            return "color: gray"
        if val >= 2:
            return "color: white; font-weight: bold"
        elif val >= 0:
            return "color: gray; font-weight: bold"
        else:
            return "color: red; font-weight: bold" 

    styled = stats[['cv', 'slope', 'acc']].style.format(format_value).map(set_sa_color, subset=['slope', 'acc']).map(set_cv_color, subset=['cv'])
    return rv, stats, styled

# visualize datadict (Only works in jupyter notebook)
def show_qdata(code, period:str, only:bool = False, qa_db = qa_db):
    data_dict = qa_db.loc[code, period]
    if pd.isna(data_dict) or len(data_dict) == 0:
        # print('No data for', period)
        return None
    meta = qa_db.loc[code, 'meta']
    rv, stats, styled = _preprocess_showdata(data_dict)
    p = int(period.replace("Q", ""))

    if only == False:
        print(meta['name'], code, '/', 'period', period, '/', 'LQ:', meta['last_quarter'])
        print(f'revenue growth:   {rv[0]} %') 
        print(f'dip (times):      {rv[1]} ({int(rv[1]/p*100)}%)')
        print(f"op margin:        {stats.loc['opmargin', 'mean']} %")
        print(f"debt to equity:   {stats.loc['debt.to.equity', 'mean']} %")
    display(styled)
    return None

def get_periods(qa_db = qa_db): 
    return [i for i in qa_db.columns if 'Q' in i]

def show_summary_data(code, period:str = None, qa_db = qa_db):
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
        row = {
            'period': period,
            'revenue_growth': rv[0],
            'dip': f"{rv[1]} ({int(rv[1]/p*100)}%)",
            'opmargin': stats.loc['opmargin', 'mean'],
            'debt.to.equity': stats.loc['debt.to.equity', 'mean']
        }
        summary.append(row)

    if len(summary) == 0:
        print('No data found for any period.')
        return

    summary_df = pd.DataFrame(summary).set_index('period')

    def format_cell(val):
        if pd.isna(val):
            return "–"
        return f"{val:.2f}" if isinstance(val, float) else str(val)

    def highlight_negative(val):
        if isinstance(val, float) and val < 0:
            return "color: red"
        return "color: white"

    styled = summary_df.style.format(format_cell).map(highlight_negative)

    print(f"{meta['name']} ({code})")
    print(f"Latest Quarter: {meta['last_quarter']}")
    display(styled)
    
# visualize datadict (Only works in jupyter notebook)
def show_data(code, period:str = None, qa_db = qa_db): 
    if period is None:
        show_summary_data(code)
        for period in get_periods():
            print('period:', period)
            show_qdata(code, period, only = True)
    else:
        show_qdata(code, period)



