import yfinance as yf
import pandas as pd

symbols = ['VIG', 'IWM', 'ARKK', 'SOXL']

print(f"Testing yfinance version: {yf.__version__}")

for symbol in symbols:
    print(f"\nDownloading {symbol}...")
    try:
        # Try downloading with the same parameters as the app
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="2y", interval="1d")
        
        if history.empty:
            print(f"❌ {symbol}: Empty dataframe returned")
        else:
            print(f"✅ {symbol}: Success! Got {len(history)} records")
            print(history.tail(2))
            
    except Exception as e:
        print(f"❌ {symbol}: Error - {str(e)}")
