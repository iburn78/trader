#%% 
import numpy as np
import mplfinance as mpf
import yfinance as yf

# adds moving average and cross signals
# should have 'Close'
def add_ma_cs(price_ohlcv, window_n):
    ma_col = f"ma{window_n}"  # ma: moving average
    cs_col = f"cs{window_n}"  # cs: cross signal (of "Close")

    # Moving average
    price_ohlcv[ma_col] = price_ohlcv["Close"].rolling(window_n).mean()

    # State: above/below MA
    # if "Close" crosses ma: +1, -1
    diff = price_ohlcv["Close"] - price_ohlcv[ma_col]
    state = diff.where(diff.ne(0)).apply(np.sign).ffill()
    price_ohlcv[cs_col] = state.diff().apply(np.sign).fillna(0).astype(int)

    return price_ohlcv

# should have 'Open', 'High', 'Low', 'Close', 'Volume'
def ma_cs_plot(price_ohlcv, window_n, days_to_display = 0):
    price_ohlcv = add_ma_cs(price_ohlcv, window_n)[-days_to_display:]

    ma = f"ma{window_n}"
    cs = f"cs{window_n}"

    apds = [
        mpf.make_addplot(
            np.where(price_ohlcv[cs] == 1, 0, np.nan),
            panel = 2,
            type='scatter',
            marker='^',
            markersize=100,
            color='blue',
            secondary_y = False, 
        ),
        mpf.make_addplot(
            np.where(price_ohlcv[cs] == -1, 0, np.nan),
            panel = 2,
            type='scatter',
            marker='v',
            markersize=100,
            color='red',
            secondary_y = False, 
        ),

        mpf.make_addplot(
            price_ohlcv[ma],
            width = 1,
        ),
    ]

    mpf.plot(
        price_ohlcv, 
        figsize = (15, 10),
        type='candle', 
        addplot=apds,
        style='starsandstripes', # 'yahoo' 
        volume=True,
        panel_ratios = (4, 2, 1), 
    )

# -----------------------
# Usage
# -----------------------
prices = yf.Ticker("005930.KS").history(period='1y')
ma_cs_plot(prices, 10, 30)

