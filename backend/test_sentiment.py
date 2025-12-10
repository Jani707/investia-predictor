import yfinance as yf
from textblob import TextBlob
import sys

def test_sentiment(symbol):
    print(f"📰 Fetching news for {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        if not news:
            print("❌ No news found.")
            return

        print(f"✅ Found {len(news)} articles.")
        
        total_polarity = 0
        count = 0
        
        for article in news:
            title = article.get('title', '')
            if not title: continue
            
            blob = TextBlob(title)
            polarity = blob.sentiment.polarity
            total_polarity += polarity
            count += 1
            
            print(f"   - [{polarity:.2f}] {title}")
            
        if count > 0:
            avg_sentiment = total_polarity / count
            print(f"\n📊 Average Sentiment for {symbol}: {avg_sentiment:.2f}")
            if avg_sentiment > 0.1: print("   🚀 Bullish Sentiment")
            elif avg_sentiment < -0.1: print("   🐻 Bearish Sentiment")
            else: print("   😐 Neutral Sentiment")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Install textblob if missing (just for this test script context)
    try:
        import textblob
    except ImportError:
        print("Installing textblob...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "textblob"])
        
    test_sentiment("AAPL")
    test_sentiment("TSLA")
