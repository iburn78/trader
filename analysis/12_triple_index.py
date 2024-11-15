#%% 
import FinanceDataReader as fdr
df = fdr.DataReader('USD/KRW') # 달러 원화
display(df)
#%% 
df = fdr.DataReader('US5YT')   # 5년 만기 미국국채 수익률
display(df)
#%% 
df = fdr.DataReader('US10YT') # 10년 만기 미국국채 수익률
display(df)
#%% 
df = fdr.DataReader('US30YT') # 30년 만기 미국국채 수익률
display(df)
#%% 
df = fdr.DataReader('KS11') # KOSPI 지수 (KRX)
display(df)
#%% 
df = fdr.DataReader('DJI') # 다우존스 지수 (DJI - Dow Jones Industrial Average)
display(df)
#%% 
df = fdr.DataReader('IXIC') # 나스닥 종합지수 (IXIC - NASDAQ Composite)
display(df)
#%% 
df = fdr.DataReader('S&P500') # S&P500 지수 (NYSE)
display(df)
#%% 
