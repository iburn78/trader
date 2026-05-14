#%% 
import numpy as np
import mplfinance as mpf
import yfinance as yf

def add_ma_cs(price_df, window_n):
    """
    adds moving average and cross signals
    - ma
    - cs
    - pcs
    - scs
    """
    ma_col = f"ma{window_n}"  # ma: moving average
    cs_col = f"cs{window_n}"  # cs: cross
    passthrough_cs_col = f"pcs{window_n}"
    strict_cs_col = f"scs{window_n}"

    # Moving average
    price_df[ma_col] = price_df["Close"].rolling(window_n).mean()

    # State: above/below MA
    # if "Close" crosses ma: +1, -1
    diff = price_df["Close"] - price_df[ma_col]
    state = diff.where(diff.ne(0)).apply(np.sign).ffill()
    price_df[cs_col] = state.diff().apply(np.sign).fillna(0).astype(int)

    ma = price_df[ma_col]
    prev_ma = ma.shift(1)
    prev_low = price_df["Low"].shift(1)
    prev_high = price_df["High"].shift(1)

    # passthrough: body cross
    passthrough_cs_up = (price_df["Open"] <= ma) & (price_df["Close"] > ma)
    passthrough_cs_down = (price_df["Open"] >= ma) & (price_df["Close"] < ma)

    # strict: if "High" and "Low" crosses ma: +1, -1
    strict_cs_up = (prev_low <= prev_ma) & (price_df["Low"] > ma)
    strict_cs_down = (prev_high >= prev_ma) & (price_df["High"] < ma)

    price_df[passthrough_cs_col] = 0
    price_df.loc[passthrough_cs_up, passthrough_cs_col] = 1
    price_df.loc[passthrough_cs_down, passthrough_cs_col] = -1

    price_df[strict_cs_col] = 0
    price_df.loc[strict_cs_up, strict_cs_col] = 1
    price_df.loc[strict_cs_down, strict_cs_col] = -1

    return price_df

def ma_cs_plot(price_df, window_n, to_display = 0):
    price_df = add_ma_cs(price_df, window_n)[-to_display:]

    ma = f"ma{window_n}"
    cs = f"cs{window_n}"
    pcs = f"pcs{window_n}"
    scs = f"scs{window_n}"

    apds = [
        mpf.make_addplot(
            np.where(price_df[cs] == 1, 1, np.nan),
            panel = 2,
            type='scatter',
            marker='^',
            markersize=100,
            color='blue',
            secondary_y = False, 
        ),
        mpf.make_addplot(
            np.where(price_df[cs] == -1, 1, np.nan),
            panel = 2,
            type='scatter',
            marker='v',
            markersize=100,
            color='red',
            secondary_y = False, 
        ),

        mpf.make_addplot(
            np.where(price_df[pcs] == 1, 0, np.nan),
            panel = 2,
            type='scatter',
            marker='^',
            markersize=100,
            color='blue',
            secondary_y = False, 
        ),
        mpf.make_addplot(
            np.where(price_df[pcs] == -1, 0, np.nan),
            panel = 2,
            type='scatter',
            marker='v',
            markersize=100,
            color='red',
            secondary_y = False, 
        ),

        mpf.make_addplot(
            np.where(price_df[scs] == 1, -1, np.nan),
            panel = 2,
            type='scatter',
            marker='^',
            markersize=100,
            color='blue',
            secondary_y = False, 
        ),
        mpf.make_addplot(
            np.where(price_df[scs] == -1, -1, np.nan),
            panel = 2,
            type='scatter',
            marker='v',
            markersize=100,
            color='red',
            secondary_y = False, 
        ),
        mpf.make_addplot(
            price_df[ma],
            width = 1,
        ),
    ]

    mpf.plot(
        price_df,
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
tk = yf.Ticker("005930.KS")
tkpr = tk.history(period="1y")
ma_cs_plot(tkpr, 10, 30)

