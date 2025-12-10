import yfinance as yf
import pandas as pd
import ta
from app.config import ASSETS, ANALYSIS_CONFIG

class AnalysisService:
    @staticmethod
    def analyze_market():
        """
        Analiza el mercado buscando oportunidades de compra basadas en:
        1. RSI bajo (sobreventa)
        2. Caída de precio reciente
        3. Volatilidad (proxy de factores externos)
        """
        opportunities = []
        
        print("🔍 Analyzing market for opportunities...")
        
        for symbol, info in ASSETS.items():
            try:
                # Descargar datos recientes (últimos 3 meses para tener suficiente para RSI)
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="3mo")
                
                if hist.empty:
                    continue
                
                # Calcular RSI
                hist['RSI'] = ta.momentum.rsi(hist['Close'], window=14)
                current_rsi = hist['RSI'].iloc[-1]
                
                # Calcular caída de precio (desde el máximo de los últimos 5 días)
                recent_high = hist['High'].tail(5).max()
                current_price = hist['Close'].iloc[-1]
                price_drop = (recent_high - current_price) / recent_high
                
                # Calcular volatilidad (desviación estándar de retornos diarios últimos 14 días)
                daily_returns = hist['Close'].pct_change()
                volatility = daily_returns.tail(14).std()
                
                # Criterios de oportunidad
                is_oversold = current_rsi < ANALYSIS_CONFIG["rsi_threshold_low"]
                is_dip = price_drop > ANALYSIS_CONFIG["price_drop_threshold"]
                is_volatile = volatility > ANALYSIS_CONFIG["volatility_threshold"]
                
                reasons = []
                if is_oversold:
                    reasons.append(f"RSI bajo ({current_rsi:.2f})")
                if is_dip:
                    reasons.append(f"Caída reciente de precio ({price_drop*100:.1f}%)")
                if is_volatile:
                    reasons.append(f"Alta volatilidad ({volatility*100:.1f}%) - Posible factor externo")
                
                # Si cumple al menos una condición fuerte (RSI o Dip grande) o combinación
                if is_oversold or (is_dip and is_volatile):
                     opportunities.append({
                        "symbol": symbol,
                        "name": info["name"],
                        "price": current_price,
                        "reasons": reasons
                    })
                    
            except Exception as e:
                print(f"⚠️ Error analyzing {symbol}: {e}")
                continue
                
        return opportunities
