#%%
from analysis_tools import *
from drawer import Drawer
import yfinance as yf

# Define tickers for global indices
indices = {
    'Dow Jones': '^DJI',       # USA
    'S&P 500': '^GSPC',        # USA
    'Nasdaq': '^IXIC',         # USA
    'Nikkei 225': '^N225',     # Japan
    'Hang Seng': '^HSI',       # Hong Kong
    'FTSE 100': '^FTSE',       # UK
    'DAX': '^GDAXI'            # Germany
}

# Fetch daily data for the last month
df_KS = fdr.DataReader('KS11')['Close'] # KOSPI 지수 (KRX)
df_KQ = fdr.DataReader('KQ11')['Close'] # KOSDAQ 지수 (KRX)
df_KS200 = fdr.DataReader('KS200')['Close'] # KOSPI 200 (KRX)
data = {name: yf.Ticker(ticker).history(period="3mo", interval="1d") for name, ticker in indices.items()}

#%% 
lim = -50
normalize_date = '2024-11-05'

KS = df_KS[lim:]
KS = KS/KS.loc[normalize_date]*100
KQ = df_KQ[lim:]
KQ = KQ/KQ.loc[normalize_date]*100
K2 = df_KS200[lim:]
K2 = K2/K2.loc[normalize_date]*100

dj = data['Dow Jones']['Close'][lim:]
dj = dj/dj.loc[normalize_date]*100
sp = data['S&P 500']['Close'][lim:]
sp = sp/sp.loc[normalize_date]*100
nq = data['Nasdaq']['Close'][lim:]
nq = nq/nq.loc[normalize_date]*100
nk = data['Nikkei 225']['Close'][lim:]
nk = nk/nk.loc[normalize_date]*100
hs = data['Hang Seng']['Close'][lim:]
hs = hs/hs.loc[normalize_date]*100
ft = data['FTSE 100']['Close'][lim:]
ft = ft/ft.loc[normalize_date]*100

#%% 
line_drawer = Drawer(
    figsize = (10, 10), 
    tick_text_size = 15,
    text_size = 20,
    lang = 'E', 
    eng_name = None
)
output_file = f'plots/index_KR.mp4'
line_drawer.triple_line_animate(KS.index, KS.values, K2.index, K2.values, KQ.index, KQ.values, output_file=output_file)
output_file = f'plots/index_us.mp4'
line_drawer.triple_line_animate(dj.index, dj.values, sp.index, sp.values, nq.index, nq.values, output_file=output_file)
output_file = f'plots/index_other.mp4'
line_drawer.triple_line_animate(nk.index, nk.values, hs.index, hs.values, ft.index, ft.values, output_file=output_file)
# yellow, red, orange
#%% 

from analysis_tools import *
from drawer import Drawer
import yfinance as yf

df_KS = fdr.DataReader('KS11')['Close'] # KOSPI 지수 (KRX)
display(df_KS)
#%% 
line_drawer = Drawer(
    figsize = (10, 10), 
    tick_text_size = 12,
    text_size = 20,
    lang = 'E', 
    eng_name = None
)
line_drawer.free_plot()
line_drawer.ax.plot(df_KS[-300:], color='w')