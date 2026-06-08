#%%
# -----------------------------------------------------------------------------
# Utilizing the fn-guide quartelry result data - downloaded as Excel (ProResult.xlsx)
# https://www.fnguide.com/Home/PopPerformanceNews
# login required: i/a
# -----------------------------------------------------------------------------
import pandas as pd
import os 

cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
df = pd.read_excel(os.path.join(cd_, "data/ProResult.xlsx"), header=[8, 9])
df.columns = [
    c[0] if 'Unnamed' in str(c[1])
    else f'{c[0]}_{c[1]}'
    for c in df.columns
]
new_column_names = {
    '종목명': 'name',
    '실적이슈': 'issue',
    '결산': 'YE', # 결산분기
    '회계기준': 'acc', # 연결 vs 별도
    '분기실적(억원)_매출액': 'qrev',
    '분기실적(억원)_영업이익': 'qop',
    '분기실적(억원)_순이익': 'qnet',
    '분기실적(억원)_순이익(지배)': 'qowners_net',
    '전년동기대비(%)_매출액': 'yrev_perc',
    '전년동기대비(%)_영업이익': 'yop_perc',
    '전년동기대비(%)_순이익': 'ynet_perc',
    '전년동기대비(%)_순이익(지배)': 'yowners_net_perc',
    '발표': 'confirmed', # 확정 vs 잠정
    '공시일': 'disclosure' 
}
df = df.rename(columns=new_column_names)

# --------------------------------------------
# usage examples 
# --------------------------------------------
# 1) only 연결
# 2) recent disclosures
# 3) owners share
# 4) increament over last year
