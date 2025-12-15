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
        Analiza un único activo. Intenta usar ML primero, luego reglas.
        """
        try:
            # Intentar usar Predictor (LSTM)
            from ml.predictor import Predictor
            predictor = Predictor()
            
            # Verificar si existe modelo entrenado
            if predictor.load_model(symbol):
                print(f"🤖 Using LSTM Model for {symbol}")
                prediction = predictor.predict(symbol)
                if prediction.get("success"):
                    # Enriquecer con contexto macro si es necesario
                    return prediction
            
            print(f"⚠️ No ML model for {symbol}, falling back to Rule-Based Analysis")
            
            if macro_context is None:
                macro_context = AnalysisService.get_macro_context()
                
            # 1. Fetch Data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            if hist.empty:
                raise Exception("No price data found (possibly delisted or IP blocked)")
            
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
            
            # Generar predicciones sintéticas basadas en el score
            daily_change = 0
            if score >= 2.5: daily_change = 0.005 # +0.5% diario
            elif score >= 1: daily_change = 0.002 # +0.2% diario
            elif score <= -2: daily_change = -0.005 # -0.5% diario
            elif score <= -1: daily_change = -0.002 # -0.2% diario
            
            predictions = []
            price = current_price
            
            for i in range(5):
                price = price * (1 + daily_change)
                change_pct = ((price - current_price) / current_price) * 100
                predictions.append({
                    "day": i + 1,
                    "predicted_price": price,
                    "change_percent": change_pct
                })
            
            return {
                "symbol": symbol,
                "name": symbol, # Placeholder
                "current_price": current_price,
                "recommendation": recommendation,
                "score": score,
                "reasons": reasons,
                "sentiment": sentiment,
                "risk": "medium",
                "is_ml": False,
                "success": True,
                "predictions": predictions,
                "average_change_percent": predictions[-1]["change_percent"],
                "trend": "bullish" if score > 0 else "bearish" if score < 0 else "neutral",
                "confidence": {
                    "score": 0.7 if abs(score) > 2 else 0.5,
                    "level": "medium"
                }
            }
            
        except Exception as e:
            print(f"⚠️ Error analyzing {symbol}: {e}")
            # Fallback: Generar datos sintéticos para demostración si falla la API
            print(f"⚠️ Using fallback mock data for {symbol}")
            import random
            base_price = 100.0
            if symbol == "VOO": base_price = 450.0
            elif symbol == "VTI": base_price = 230.0
            elif symbol == "BND": base_price = 75.0
            
            mock_price = base_price * (1 + random.uniform(-0.05, 0.05))
            # FIX: Score neutral (-2 a 2) en lugar de sesgado positivo (-1 a 3)
            mock_score = random.uniform(-2, 2)
            
            rec = "MANTENER"
            if mock_score >= 2: rec = "COMPRAR"
            elif mock_score <= -1: rec = "VENDER"
            
            # Generar predicciones sintéticas
            predictions = []
            price = mock_price
            daily_change = 0.003 if rec == "COMPRAR" else -0.003 if rec == "VENDER" else 0
            
            for i in range(5):
                price = price * (1 + daily_change)
                change_pct = ((price - mock_price) / mock_price) * 100
                predictions.append({
                    "day": i + 1,
                    "predicted_price": price,
                    "change_percent": change_pct
                })

            return {
                "symbol": symbol,
                "name": symbol,
                "current_price": mock_price,
                "recommendation": rec,
                "score": mock_score,
                "reasons": ["⚠️ Modo Simulación (API Error)", "Datos generados aleatoriamente"],
                "sentiment": {"label": "Neutral", "score": 0.0},
                "risk": "medium",
                "is_mock": True,
                "success": True,
                "predictions": predictions,
                "average_change_percent": predictions[-1]["change_percent"],
                "trend": "bullish" if mock_score > 0 else "bearish" if mock_score < 0 else "neutral",
                "confidence": {"score": 0.0, "level": "low"}
            }

    _cache = []
    _cache_file = "predictions_cache.json"

    @staticmethod
    def get_cached_predictions():
        """
        Devuelve las predicciones en caché. Si está vacía, intenta cargar de disco.
        """
        if not AnalysisService._cache:
            import json
            import os
            if os.path.exists(AnalysisService._cache_file):
                try:
                    with open(AnalysisService._cache_file, 'r') as f:
                        AnalysisService._cache = json.load(f)
                        print(f"📂 Loaded {len(AnalysisService._cache)} predictions from disk cache.")
                except Exception as e:
                    print(f"⚠️ Failed to load cache from disk: {e}")
        
        return AnalysisService._cache

    @staticmethod
    def update_cache():
        """
        Ejecuta el análisis y actualiza la caché.
        """
        print("🔄 Updating prediction cache...")
        predictions = AnalysisService.analyze_market(return_all=True)
        AnalysisService._cache = predictions
        
        # Guardar en disco
        try:
            import json
            with open(AnalysisService._cache_file, 'w') as f:
                json.dump(predictions, f)
            print("💾 Cache saved to disk.")
        except Exception as e:
            print(f"⚠️ Failed to save cache to disk: {e}")
            
        return predictions

    @staticmethod
    def analyze_market(return_all=False):
        print("🔍 Analyzing market for opportunities...")
        opportunities = []
        all_results = []
        
        macro = AnalysisService.get_macro_context()
        custom_symbols = WatchlistService.get_watchlist()
        all_symbols = list(set(ANALYSIS_CONFIG["tickers"] + custom_symbols))
        
        for symbol in all_symbols:
            result = AnalysisService.analyze_symbol(symbol, macro)
            if result:
                # Para la caché queremos todo, pero con un flag de "oportunidad"
                is_opportunity = (result['recommendation'] != "MANTENER" or symbol in custom_symbols)
                result['is_opportunity'] = is_opportunity
                
                all_results.append(result)
                
                if is_opportunity:
                    opportunities.append(result)
        
        if return_all:
            return all_results
            
        return opportunities
