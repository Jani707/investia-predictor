import yfinance as yf
import pandas as pd
import ta
from app.config import ASSETS, ANALYSIS_CONFIG
from app.services.telegram_service import TelegramService
from app.services.watchlist_service import WatchlistService

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
    def analyze_market():
        print("🔍 Analyzing market for opportunities...")
        opportunities = []
        
        # Obtener contexto macro
        macro = AnalysisService.get_macro_context()
        
        # Combinar tickers por defecto + Watchlist
        custom_symbols = WatchlistService.get_watchlist()
        all_symbols = list(set(ANALYSIS_CONFIG["tickers"] + custom_symbols))
        
        for symbol in all_symbols:
            try:
                # Descargar datos (6 meses para SMA 200 si fuera necesario, o al menos suficiente para MACD/Bollinger)
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1y") # Necesitamos más historia para SMA 200
                
                if hist.empty:
                    continue
                
                # --- CÁLCULO DE INDICADORES ---
                close = hist['Close']
                
                # 1. RSI
                hist['RSI'] = ta.momentum.rsi(close, window=14)
                current_rsi = hist['RSI'].iloc[-1]
                
                # 2. MACD
                macd = ta.trend.MACD(close)
                hist['MACD'] = macd.macd()
                hist['MACD_Signal'] = macd.macd_signal()
                current_macd = hist['MACD'].iloc[-1]
                current_signal = hist['MACD_Signal'].iloc[-1]
                
                # 3. Bollinger Bands
                bollinger = ta.volatility.BollingerBands(close, window=20, window_dev=ANALYSIS_CONFIG["bollinger_std_dev"])
                hist['BB_Lower'] = bollinger.bollinger_lband()
                current_bb_lower = hist['BB_Lower'].iloc[-1]
                current_price = close.iloc[-1]
                
                # 4. SMA (Tendencia)
                hist['SMA_50'] = ta.trend.sma_indicator(close, window=ANALYSIS_CONFIG["sma_fast"])
                hist['SMA_200'] = ta.trend.sma_indicator(close, window=ANALYSIS_CONFIG["sma_slow"])
                current_sma_200 = hist['SMA_200'].iloc[-1] if not pd.isna(hist['SMA_200'].iloc[-1]) else 0
                
                # 5. Volatilidad y Caída (Lógica anterior)
                recent_high = hist['High'].tail(5).max()
                price_drop = (recent_high - current_price) / recent_high
                daily_returns = close.pct_change()
                volatility = daily_returns.tail(14).std()
                
                # --- LÓGICA DE DECISIÓN ---
                reasons = []
                score = 0 # Sistema de puntuación
                
                # A. RSI (Sobreventa) - Fuerte señal de rebote
                if current_rsi < ANALYSIS_CONFIG["rsi_threshold_low"]:
                    reasons.append(f"📉 RSI Sobrevendido ({current_rsi:.2f})")
                    score += 2
                elif current_rsi < 40: # Casi sobrevendido
                    score += 0.5
                    
                # B. Bollinger Bands (Precio barato relativo a volatilidad)
                if current_price < current_bb_lower:
                    reasons.append(f"📉 Precio bajo Banda Bollinger Inferior")
                    score += 2
                    
                # C. MACD (Cambio de tendencia)
                # Detectar cruce alcista reciente (en los últimos 3 días)
                macd_cross = (hist['MACD'].iloc[-3:] > hist['MACD_Signal'].iloc[-3:]).any() and (hist['MACD'].iloc[-4] < hist['MACD_Signal'].iloc[-4])
                if macd_cross:
                    reasons.append(f"🔄 Cruce Alcista MACD")
                    score += 1.5
                
                # D. Caída Reciente (Dip)
                if price_drop > ANALYSIS_CONFIG["price_drop_threshold"]:
                    reasons.append(f"🔻 Caída fuerte reciente ({price_drop*100:.1f}%)")
                    score += 1
                    
                # E. Contexto Macro (Filtro de Seguridad)
                if macro['status'] == "fear":
                    # Si hay miedo extremo, exigimos más calidad (score más alto)
                    reasons.append(f"⚠️ Mercado con Miedo (VIX {macro['vix']:.2f})")
                    score -= 1 # Penalizamos para ser más conservadores, o exigimos score > 4
                
                # F. Tendencia de Largo Plazo (SMA 200)
                # Comprar en dips cuando la tendencia general es alcista es mejor
                if current_price > current_sma_200 and current_sma_200 > 0:
                    score += 0.5 # Bonificación por tendencia alcista de fondo
                
                # --- EVALUACIÓN FINAL ---
                # Umbral de Score: 2.5 (ajustable)
                # Significa que necesita al menos una señal muy fuerte (RSI o Bollinger) más algo de apoyo,
                # o varias señales medias.
                if score >= 2.5:
                     opportunities.append({
                        "symbol": symbol,
                        "name": info["name"],
                        "price": current_price,
                        "reasons": reasons,
                        "score": score
                    })
                    
            except Exception as e:
                print(f"⚠️ Error analyzing {symbol}: {e}")
                continue
                
        return opportunities
