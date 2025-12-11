import yfinance as yf
import pandas as pd
import ta
from app.config import ASSETS, ANALYSIS_CONFIG
from app.services.telegram_service import TelegramService
from app.services.watchlist_service import WatchlistService
from app.services.sentiment_service import SentimentService

class AnalysisService:
    @staticmethod
    def get_macro_context():
        """
        Obtiene indicadores macroeconómicos para ajustar la estrategia.
        """
        try:
            # VIX (Volatilidad)
            vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
            
            # 10-Year Treasury Yield (Riesgo libre)
            tnx = yf.Ticker("^TNX").history(period="5d")['Close'].iloc[-1]
            
            context = {
                "vix": vix,
                "tnx": tnx,
                "status": "neutral"
            }
            
            if vix > ANALYSIS_CONFIG["vix_threshold_extreme"]:
                context["status"] = "extreme_fear"
            elif vix > ANALYSIS_CONFIG["vix_threshold_high"]:
                context["status"] = "fear"
                
            print(f"🌍 Macro Context: VIX={vix:.2f}, 10Y Yield={tnx:.2f}, Status={context['status']}")
            return context
        except Exception as e:
            print(f"⚠️ Error fetching macro data: {e}")
            return {"vix": 20, "tnx": 4.0, "status": "neutral"} # Fallback

    @staticmethod
    def analyze_symbol(symbol: str, macro_context: dict = None):
        """
        Analiza un único activo usando lógica basada en reglas.
        """
        try:
            if macro_context is None:
                macro_context = AnalysisService.get_macro_context()
                
            # 1. Fetch Data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            if hist.empty: return None
            
            close = hist['Close']
            current_price = close.iloc[-1]
            
            # 2. Calculate Indicators
            rsi = ta.momentum.rsi(close, window=14).iloc[-1]
            
            bollinger = ta.volatility.BollingerBands(close, window=20, window_dev=ANALYSIS_CONFIG["bollinger_std_dev"])
            bb_lower = bollinger.bollinger_lband().iloc[-1]
            
            macd = ta.trend.MACD(close)
            macd_line = macd.macd().iloc[-1]
            macd_signal = macd.macd_signal().iloc[-1]
            
            sma_200 = ta.trend.sma_indicator(close, window=ANALYSIS_CONFIG["sma_slow"]).iloc[-1]
            
            # 3. Sentiment
            sentiment = SentimentService.analyze_sentiment(symbol)
            
            # 4. Scoring Logic
            score = 0
            reasons = []
            
            # RSI
            if rsi < ANALYSIS_CONFIG["rsi_threshold_low"]:
                score += 2
                reasons.append(f"RSI Oversold ({rsi:.1f})")
            elif rsi < 40:
                score += 0.5
            
            # Bollinger
            if current_price < bb_lower:
                score += 2
                reasons.append("Price below Lower BB")
            
            # MACD
            if macd_line > macd_signal:
                score += 1
                reasons.append("MACD Bullish Crossover")
            
            # Trend
            if current_price > sma_200:
                score += 0.5
                reasons.append("Above 200 SMA")
                
            # Macro
            if macro_context['status'] == 'fear' and score > 0:
                score -= 1
                reasons.append("Market Fear Penalty")
            elif macro_context['status'] == 'extreme_fear':
                score -= 2
                reasons.append("Extreme Fear Penalty")
                
            # Sentiment
            if sentiment['label'] == 'Bullish':
                score += 1
                reasons.append(f"Positive News ({sentiment['score']:.2f})")
            elif sentiment['label'] == 'Bearish':
                score -= 1
                reasons.append(f"Negative News ({sentiment['score']:.2f})")
            
            # Recommendation
            recommendation = "MANTENER"
            if score >= 2.5: recommendation = "COMPRAR"
            elif score <= -1: recommendation = "VENDER"
            
            return {
                "symbol": symbol,
                "name": symbol, # Placeholder
                "current_price": current_price,
                "recommendation": recommendation,
                "score": score,
                "reasons": reasons,
                "sentiment": sentiment,
                "risk": "medium"
            }
            
        except Exception as e:
            print(f"⚠️ Error analyzing {symbol}: {e}")
            return None

    @staticmethod
    def analyze_market():
        print("🔍 Analyzing market for opportunities...")
        opportunities = []
        
        macro = AnalysisService.get_macro_context()
        custom_symbols = WatchlistService.get_watchlist()
        all_symbols = list(set(ANALYSIS_CONFIG["tickers"] + custom_symbols))
        
        for symbol in all_symbols:
            result = AnalysisService.analyze_symbol(symbol, macro)
            if result and (result['recommendation'] != "MANTENER" or symbol in custom_symbols):
                opportunities.append(result)
                
        return opportunities
