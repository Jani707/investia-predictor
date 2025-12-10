import yfinance as yf
from textblob import TextBlob

class SentimentService:
    @staticmethod
    def analyze_sentiment(symbol: str):
        """
        Analiza el sentimiento de las noticias recientes para un símbolo.
        Retorna un score (-1 a 1) y una etiqueta.
        """
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return {"score": 0, "label": "Neutral", "count": 0}
            
            total_polarity = 0
            count = 0
            
            for article in news:
                title = article.get('title', '')
                if not title: continue
                
                # Análisis simple con TextBlob
                blob = TextBlob(title)
                total_polarity += blob.sentiment.polarity
                count += 1
            
            if count == 0:
                return {"score": 0, "label": "Neutral", "count": 0}
                
            avg_score = total_polarity / count
            
            # Determinar etiqueta
            label = "Neutral"
            if avg_score > 0.1: label = "Bullish"
            elif avg_score < -0.1: label = "Bearish"
            
            return {
                "score": avg_score,
                "label": label,
                "count": count
            }
            
        except Exception as e:
            print(f"⚠️ Error analyzing sentiment for {symbol}: {e}")
            return {"score": 0, "label": "Error", "count": 0}
