#%% 
import pandas as pd
import yfinance as yf
import json

# Example DataFrame with Tickers (you'll need to map CUSIPs to tickers)
datafile = 'data/usholdings.xlsx'
df = pd.read_excel(datafile)

tickers = [
    "TSLA", # TESLA INC
    "NVDA",  # NVIDIA CORP
    "AAPL",  # APPLE INC
    "MSFT",  # MICROSOFT CORP
    "QQQ",  # PROSHARES ULTRAPRO QQQ ETF
    "SOXX",  # DIREXION DAILY SEMICONDUCTORS BULL 3X SHS ETF
    "GOOGL",  # ALPHABET INC CL A
    "QQQ",  # INVESCO QQQ TRUST SRS 1 ETF
    "IONQ",  # IONQ INC
    "AMZN",  # AMAZON.COM INC
    "SPY",  # SPDR SP 500 ETF TRUST
    "SPY",  # VANGUARD SP 500 ETF SPLR 39326002188 US9229084135
    "SCHD",  # SCHWAB US DIVIDEND EQUITY ETF
    "TBF",  # DIREXION DAILY 20 YEAR PLUS DRX DLY 20+ YR TRE...
    "PLTR",  # PALANTIR TECHNOLOGIES INC CL A
    "TSLL",  # DIREXION DAILY TSLA BULL 2X SHARES
    "SQQQ",  # PROSHARES ULTRAPRO SHORT QQQ ETF
    "AVGO",  # BROADCOM INC EXOF 005644980 SG9999014823
    "MSTR",  # MICROSTRATEGY INC CL A
    "META",  # META PLATFORMS INC CL A
    "TSM",  # TAIWAN SEMICONDUCTOR MANUFACTURING CO LTD ADR
    "TLT",  # ISHARES 20+ YEAR TREASURY BOND ETF
    "GRNV",  # GRANITESHARES 2.0X LONG NVDA DAILY ETF
    "QQQ",  # PROSHARES ULTRA QQQ ETF
    "O",  # REALTY INCOME CORP
    "AMD",  # ADVANCED MICRO DEVICES INC
    "CPNG",  # COUPANG INC
    "BITO",  # 2X BITCOIN STRATEGY ETF
    "GOOG",  # ALPHABET INC CL C CHAN 39527405649 US38259P7069
    "BRK.B",  # BERKSHIRE HATHAWAY INC CL B
    "JEPI",  # JP MORGAN EQUITY PREMIUM INCOME ETF
    "SOXX",  # ISHARES SEMICONDUCTOR ETF
    "LLY",  # ELI LILLY & CO
    "ASML",  # ASML HOLDING NV ADR
    "INTC",  # INTEL CORP
    "SMR",  # NUSCALE POWER CORP CL A MRGR 009185329 KYG8377...
    "BRK.A",  # BERKSHIRE HATHAWAY INC CL A
    "HAS",  # HASBRO INC
    "IVV",  # ISHARES CORE SP 500 ETF
    "GRNV",  # GRNTSHR 2X ETF
    "GRAB",  # GRAB HOLDINGS LTD CL A MRGR 008779401 KYG0370L...
    "MU",  # MICRON TECHNOLOGY INC
    "JOBY",  # JOBY AVIATION INC EXOF 008448244 KYG7483N1117
    "QQQ",  # INVESCO NASDAQ 100 ETF
    "COIN",  # COINBASE GLOBAL INC
    "KO",  # THE COCA COLA COMPANY
    "BITO",  # PROSHARES ULTRA BITCOIN ETF
    "SMH",  # VANECK SEMICONDUCTOR ETF CHAN 39610601171 US57...
    "FNGU",  # MicroSectors FANG+ Index 3X Leveraged ETN
    "PFE"  # PFIZER INC
]


MarCaps = []
for ticker in tickers:
    stock = yf.Ticker(ticker)
    MarCaps.append(stock.info.get('marketCap', 'N/A'))

df['Ticker'] = tickers
df['MarCap'] = MarCaps
#%% 
df['MarCap'] = pd.to_numeric(df['MarCap'], errors='coerce')
df['보관금액'] = pd.to_numeric(df['보관금액'], errors='coerce')
df['KR'] = df['보관금액']/df['MarCap']*100
dfx  = df.dropna()

dfx['name'] = df['종목명'].apply(lambda x: x.split(' ')[0])
display(dfx)

#%% 
from analysis_tools import *
from drawer import Drawer


bar_drawer = Drawer(
    figsize = (6, 10), 
    tick_text_size = 14,
    text_size = 20,
    lang = 'E',
    )
bar_drawer.free_plot()
x = dfx['Ticker'].iloc[::-1]
y = dfx['보관금액'].iloc[::-1]/10**8
bars = bar_drawer.ax.barh(x,y)
for index, value in enumerate(y):
    bar_drawer.ax.text(value, index, " "+str(round(value)), va='center', fontsize=12)
bars[-1].set_color('orange')
bars[-2].set_color('gray')
bars[-3].set_color('gray')
#%% 

datafile = 'data/usholdings_1104.xlsx'
df_1104 = pd.read_excel(datafile)

display(df_1104)
#%% 
print(df["종목명"][:8].equals(df_1104["종목명"][:8])) 
dfc = pd.DataFrame()
dfc['a'] = df['종목명']
dfc['b'] = df_1104['종목명']
display(df_1104)
#%% 
# display(dfx)

bar_drawer2 = Drawer(
    figsize = (6, 10), 
    tick_text_size = 14,
    text_size = 20,
    lang = 'E',
    )
bar_drawer2.free_plot()
x = dfx['Ticker'].iloc[::-1]
y = dfx['KR'].iloc[::-1]
bars = bar_drawer2.ax.barh(x,y)
for index, value in enumerate(y):
    bar_drawer2.ax.text(value, index, " "+str(round(value,1)), va='center', fontsize=12)
bars[-1].set_color('orange')
bars[-2].set_color('orange')
bars[-6].set_color('red')
bars[-10].set_color('orange')
bars[-15].set_color('orange')
bars[-20].set_color('gray')
bars[-21].set_color('gray')
bars[-22].set_color('gray')
bars[-23].set_color('gray')
bars[-24].set_color('gray')
bars[-25].set_color('gray')

#%% 


datafile = 'data/reserve.xlsx'
df_res = pd.read_excel(datafile)
df_res['date'] = pd.to_datetime(df_res['date'], format='%Y/%m/%d')
df_res['value'] = df_res['value'].apply(lambda x: int(x.replace(",", "")))/1000000
display(df_res)
drawer3 = Drawer(
    figsize = (9, 5), 
    tick_text_size = 10,
    text_size = 20,
    lang = 'E',
)
drawer3.free_plot()
drawer3.ax.plot(df_res['date'], df_res['value'])