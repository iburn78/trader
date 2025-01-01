#%%
# -----------------------------------------------------------------------------
# Utilizing the fn-guide quartelry result data - downloaded as Excel (ProResult.xlsx)
# -----------------------------------------------------------------------------
import pandas as pd
import os 

cd_ = os.path.dirname(os.path.abspath(__file__)) # .   
df = pd.read_excel(os.path.join(cd_, "data/ProResult.xlsx"), header=[0, 1])
new_column_names = {
    ('종목코드', 'Unnamed: 0_level_1'): 'Code',
    ('종목명', 'Unnamed: 1_level_1'): 'Name',
    ('실적이슈', 'Unnamed: 2_level_1'): 'Issue',
    ('Sector', 'Unnamed: 3_level_1'): 'Sector',
    ('시장', 'Unnamed: 4_level_1'): 'Market',
    ('결산', '구분'): 'Settle',
    ('연결', '구분'): 'Cons',
    ('분기실적(억원)', '매출액'): 'Q3Sales',
    ('분기실적(억원)', '영업이익'): 'Q3OP',
    ('분기실적(억원)', '순이익'): 'Q3NP',
    ('분기실적(억원)', '지배주주순이익'): 'QParentNP',
    ('전년동기대비(%)', '매출액'): 'Y3Sales_inc',
    ('전년동기대비(%)', '영업이익'): 'Y3OP_inc',
    ('전년동기대비(%)', '순이익'): 'Y3QNP_inc',
    ('전년동기대비(%)', '지배주주순이익'): 'QParentNetP_inc',
    ('발표', '구분'): 'Announce',
    ('공시일', 'Unnamed: 16_level_1'): 'DiscDate'
}
df.columns = list(new_column_names.values())
df = df.loc[df['Settle']=='3Q']
df = df.loc[~df['Name'].str.contains('스팩')]
mask = df.duplicated(subset='Name', keep=False) & (df['Cons'] == '별도')
df = df[~mask]

#%% 
up= df.loc[df['Issue']=='컨상']
down= df.loc[df['Issue']=='컨하']
print(df.groupby("Issue")['Name'].count())

#%% 
up = up.sort_values(by='Q3OP', ascending=False)
down = down.sort_values(by='Q3OP', ascending=False)
# display(up)
# display(down)

#%%
print(len(df))
opp = df.loc[df['Q3OP']>0]
print(len(opp))
opp_ = df.loc[df['Q3OP']<=0]
print(len(opp_))

opp['Y3OP_inc_n'] = pd.to_numeric(opp['Y3OP_inc'], errors='coerce')
oppp = opp.loc[opp['Y3OP_inc_n']>0]
oppn = opp.loc[opp['Y3OP_inc_n']<=0]
print(len(oppp), len(oppn))

#%% 
oppx = df.groupby('Y3OP_inc')['Name'].count().sort_values()[-100:]
# display(oppx)

#%% 
up_sector = up.groupby('Sector')['Name'].count()
# display(up_sector)
down_sector = down.groupby('Sector')['Name'].count()
# display(down_sector)

#%% 
temp = pd.merge(up_sector, down_sector, left_index=True, right_index=True, how='outer', suffixes=('_up', '_down'))
# display(temp)

#%% 
up['Y3OP_inc_n'] = pd.to_numeric(opp['Y3OP_inc'], errors='coerce')
down['Y3OP_inc_n'] = pd.to_numeric(opp['Y3OP_inc'], errors='coerce')
up = up.loc[up['Q3OP']>500].sort_values('Y3OP_inc_n', ascending=False)
down = down.loc[down['Q3OP']>500].sort_values('Y3OP_inc_n', ascending=True)

up.to_excel(os.path.join(cd_, 'data/temp_up.xlsx'))
down.to_excel(os.path.join(cd_, 'data/temp_down.xlsx')) 