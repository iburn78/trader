#%% 
# CCA: Company Classification Analysis
import pandas as pd
import os
from html2image import Html2Image
from openai import OpenAI
import json

CONF_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config/config.json')

def get_qa_db(): 
    pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
    qa_db_file = os.path.join(pd_, 'data_collection/data/qa_db.pkl') 
    return pd.read_pickle(qa_db_file)

qa_db = get_qa_db()

def get_periods(qa_db=qa_db): 
    return [i for i in qa_db.columns if 'Q' in i]

# ----------------------------------------------------------
# BELOW: visualize datadict
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

def gen_qdata(code, period:str, qa_db = qa_db):
    data_dict = qa_db.loc[code, period]
    if pd.isna(data_dict) or len(data_dict) == 0:
        return "", None
    meta = qa_db.loc[code, 'meta']
    rv, stats, styled = _preprocess_showdata(data_dict)
    p = int(period.replace("Q", ""))

    desc = meta['name'] + ' ' + code + ' / period: ' + period + ' / LQ: ' + meta['last_quarter'] + '\n'
    desc += f'revenue growth:   {rv[0]} %' + '\n'
    desc += f'dip (times):      {rv[1]} ({int(rv[1]/p*100)}%)' + '\n'
    desc += f"op margin:        {stats.loc['opmargin', 'mean']} %" + '\n'
    desc += f"debt to equity:   {stats.loc['debt.to.equity', 'mean']} %" 

    return desc, styled

def gen_summary(code, period:str = None, qa_db = qa_db):
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
        # print('No data found for any period.')
        return

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
    
def gen_data_in_html(code, qa_db = qa_db): 
    summary_desc, summary_df = gen_summary(code)
    summary_desc = summary_desc.replace('\n', '<br>')
    summary_df = summary_df.to_html()

    qdata_desc_list = []
    qdata_df_list = []
    for period in get_periods():
        qdata_desc, qdata_df = gen_qdata(code, period)
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
    cd_ = os.path.dirname(os.path.abspath(__file__))
    temp_html = os.path.join(cd_, 'CCA/temp/temp.html')
    img_path = os.path.join(cd_, 'CCA/temp/')
    filename = 'temp.png'
    with open("CCA/temp/temp.html", "w", encoding="utf-8") as f:
        f.write(full_html)  

    hti = Html2Image(output_path=img_path)
    hti.screenshot(html_file=temp_html, save_as=filename, size=(1400, 900))
    os.remove(temp_html)

    return os.path.join(img_path, filename)


def openai_command(company_name, conf_file=CONF_FILE):
    with open(conf_file, 'r') as json_file:
        config = json.load(json_file)
        api_key = config['openai']

    client = OpenAI(api_key=api_key)
    content_command = f"{company_name} is a listed company in Korea. Give me brief description (1) what is this company's business, (2) why this company's performance is good for the last quarters, (3) what are the key 3 issues ths company is facing?"
    format_command = "Answer in Korean language, and use only plain text. Total length of answers should not exceed 500 words."

    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": (
                    content_command + " " + format_command
                )
            }
        ]
    )
    return chat_completion.choices[0].message.content
