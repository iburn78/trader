#%% 
import pandas as pd
from yahooquery import Ticker
import time

# Step 1: Get Nasdaq-100 tickers from Wikipedia
def get_nasdaq_100_tickers():
    url = "https://en.wikipedia.org/wiki/NASDAQ-100"
    tables = pd.read_html(url)
    df = tables[4]
    tickers = df['Ticker'].tolist()
    return [t.replace('.', '-') for t in tickers]

# Step 2: Fetch PE and Company Name
def get_pe_and_name(ticker):
    try:
        stock = Ticker(ticker)
        stats = stock.key_stats.get(ticker, {})
        summary = stock.quote_type.get(ticker, {})

        # trailing_pe = stats.get("trailingPE")
        forward_pe = stats.get("forwardPE")
        company_name = summary.get("longName") or summary.get("shortName")

        return company_name, forward_pe
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None

# Step 3: Process each ticker
tickers = get_nasdaq_100_tickers()
pe_data = []

for i, ticker in enumerate(tickers):
    name, pe = get_pe_and_name(ticker)
    print(f"{i+1:03d}/{len(tickers)} {name} ({ticker}): PE = {pe}")
    pe_data.append((name, ticker, pe))
    time.sleep(0.5)

# Step 4: Save to CSV
df = pd.DataFrame(pe_data, columns=["Company Name", "Ticker", "PE (Forward)"])
df.to_csv("nasdaq100_pe_with_names.csv", index=False)

#%% 
from datetime import datetime, timedelta

# Load your tickers
df = pd.read_csv("nasdaq100_pe_with_names.csv")
df = df.dropna(subset=["PE (Forward)"])
tickers = df["Ticker"].tolist()

# Define date range
end = datetime.now().date()
start = end - timedelta(days=10)  # 10 days to account for weekends

def get_5_day_change(ticker):
    try:
        t = Ticker(ticker)
        hist = t.history(period="7d")  # 7 days to capture 5 trading days
        if isinstance(hist, pd.DataFrame):
            hist = hist.reset_index()
            hist = hist[hist['symbol'] == ticker]  # needed when multiple tickers used
            if len(hist) >= 5:
                old_price = hist['close'].iloc[-5]
                new_price = hist['close'].iloc[-1]
                return round((new_price - old_price) / old_price * 100, 2)
    except Exception as e:
        print(f"{ticker}: Error - {e}")
    return None

# Collect changes
weekly_changes = []
for t in tickers:
    change = get_5_day_change(t)
    print(f"{t}: {change}%")
    weekly_changes.append(change)

# Add to DataFrame
df["5-Day Change (%)"] = weekly_changes

# Save or display
df = df.sort_values("5-Day Change (%)")
df.to_csv("nasdaq100_pe_with_5day_change.csv", index=False)
print(df[["Company Name", "Ticker", "PE (Forward)", "5-Day Change (%)"]])

#%% 
import pandas as pd
import matplotlib.pyplot as plt

# Load cleaned data
df = pd.read_csv("nasdaq100_pe_with_5day_change.csv")

# Filter out negative or missing PE
df = df.dropna(subset=["PE (Forward)", "5-Day Change (%)"])
df = df[df["PE (Forward)"] > 0]
df = df[df["PE (Forward)"] < 30]

# Shorten company names to first 2 words
def short_name(name):
    return " ".join(name.split()[:2])

df["Short Name"] = df["Company Name"].apply(short_name)

# Plot
plt.figure(figsize=(12, 12))
plt.scatter(df["PE (Forward)"], df["5-Day Change (%)"], color='dodgerblue', alpha=0.7)

# Add labels
for _, row in df.iterrows():
    plt.text(row["PE (Forward)"], row["5-Day Change (%)"], row["Short Name"],
             fontsize=8, alpha=0.8)

plt.xlabel("PE Ratio (Forward)", fontsize=12)
plt.ylabel("5-Day Price Change (%)", fontsize=12)
plt.title("Scatter Plot: PE vs. 5-Day Price Change (NASDAQ-100)", fontsize=14)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()

#%% 
import yfinance as yf
import pandas as pd
import time

# List of NASDAQ-100 tickers (sample; ensure it’s 100 tickers in practice)
nasdaq_100_tickers = [
    'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'PYPL', 'ADBE', 'NFLX',
    'CSCO', 'INTC', 'PEP', 'COST', 'CMCSA', 'AMGN', 'TMUS', 'TXN', 'QCOM', 'HON',
    'CHTR', 'SBUX', 'INTU', 'ISRG', 'GILD', 'AMD', 'BKNG', 'MDLZ', 'FISV', 'ADP',
    'ROST', 'KDP', 'MAR', 'ORLY', 'LRCX', 'ASML', 'KLAC', 'SNPS', 'CDNS', 'NXPI',
    'CRWD', 'PANW', 'WDAY', 'TEAM', 'DDOG', 'ZS', 'FTNT', 'MRNA', 'BIIB', 'DXCM',
    'EBAY', 'IDXX', 'ILMN', 'KHC', 'LULU', 'MELI', 'MNST', 'ODFL', 'PCAR', 'REGN',
    'SGEN', 'SIRI', 'SWKS', 'VRSK', 'VRTX', 'WBA', 'XEL', 'ZM', 'AEP', 'ALGN',
    'ANSS', 'CEG', 'CPRT', 'CSGP', 'CTAS', 'DLTR', 'EA', 'ENPH', 'EXC', 'FAST',
    'GEHC', 'GFS', 'IQV', 'JD', 'LCID', 'LNT', 'MTCH', 'OKTA', 'PAYX', 'PTON',
    'ROKU', 'SPLK', 'TTD', 'VRSN', 'WBD', 'ZBRA'
]

# Function to get trailing P/E ratio
def get_trailing_pe(tickers):
    pe_data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            pe = stock.info.get('trailingPE', None)  # Trailing P/E from yfinance
            if pe is not None and pe != float('inf'):  # Filter out invalid/infinite values
                pe_data[ticker] = round(pe, 2)
            else:
                pe_data[ticker] = "N/A"
        except Exception as e:
            pe_data[ticker] = f"Error: {str(e)}"
        time.sleep(0.5)  # Avoid overwhelming the API
    return pe_data

# Fetch the data
print("Fetching trailing P/E ratios for NASDAQ-100 stocks...")
pe_ratios = get_trailing_pe(nasdaq_100_tickers)

# Convert to DataFrame for better readability
pe_df = pd.DataFrame(list(pe_ratios.items()), columns=['Ticker', 'Trailing P/E'])
pe_df = pe_df.sort_values(by='Trailing P/E', ascending=True, na_position='last')

# Display the results
print("\nTrailing P/E Ratios for NASDAQ-100 Stocks (Sorted):")
print(pe_df)

# Optionally save to CSV
pe_df.to_csv('nasdaq_100_trailing_pe.csv', index=False)
print("\nData saved to 'nasdaq_100_trailing_pe.csv'")