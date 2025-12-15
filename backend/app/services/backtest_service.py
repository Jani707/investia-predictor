import yfinance as yf
import pandas as pd
import ta
from app.config import ANALYSIS_CONFIG

class BacktestService:
    @staticmethod
    def run_backtest(symbol: str, days: int = 365, initial_capital: float = 10000.0):
        """
        Simula la estrategia de inversión en datos históricos.
        Retorna la curva de equidad y la lista de operaciones.
        """
        print(f"⏳ Running backtest for {symbol} over {days} days...")
        
        # 1. Obtener datos históricos (con buffer para indicadores)
        buffer_days = 200 # Para SMA 200
        total_days = days + buffer_days
        ticker = yf.Ticker(symbol)
        # period="5y" es seguro para cubrir 730 + 200 días
        hist = ticker.history(period="5y")
        
        if hist.empty:
            raise ValueError(f"No historical data found for symbol {symbol}")
            
        # 2. Calcular Indicadores (Vectorizado para velocidad)
        close = hist['Close']
        
        # RSI
        hist['RSI'] = ta.momentum.rsi(close, window=14)
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(close, window=20, window_dev=ANALYSIS_CONFIG["bollinger_std_dev"])
        hist['BB_Lower'] = bollinger.bollinger_lband()
        hist['BB_Upper'] = bollinger.bollinger_hband()
        
        # MACD
        macd = ta.trend.MACD(close)
        hist['MACD'] = macd.macd()
        hist['MACD_Signal'] = macd.macd_signal()
        
        # SMA
        hist['SMA_200'] = ta.trend.sma_indicator(close, window=ANALYSIS_CONFIG["sma_slow"])
        
        # Recortar al periodo solicitado
        data = hist.iloc[-days:].copy()
        
        # 3. Simulación
        cash = initial_capital
        shares = 0
        equity_curve = []
        trades = []
        
        # Buy & Hold benchmark
        initial_price = data['Close'].iloc[0]
        bh_shares = initial_capital / initial_price
        bh_curve = []
        
        for i in range(len(data)):
            date = data.index[i]
            row = data.iloc[i]
            price = row['Close']
            
            # --- LÓGICA DE ESTRATEGIA (Misma que AnalysisService) ---
            score = 0
            
            # RSI Oversold
            if row['RSI'] < ANALYSIS_CONFIG["rsi_threshold_low"]: score += 2
            elif row['RSI'] < 40: score += 0.5
            
            # Bollinger Lower
            if price < row['BB_Lower']: score += 2
            
            # MACD Cross (Simplificado: MACD > Signal)
            if row['MACD'] > row['MACD_Signal']: score += 1
            
            # SMA Trend
            if price > row['SMA_200']: score += 0.5
            
            # --- DECISIONES ---
            
            # GESTIÓN DE RIESGO (Stop Loss / Take Profit)
            if shares > 0:
                # Calcular precio promedio de compra (simplificado, asumiendo una entrada)
                # En un sistema real, llevaríamos el Average Entry Price.
                # Aquí usaremos el precio de la última compra como referencia si no tenemos historial detallado,
                # pero para hacerlo bien, necesitamos trackear el precio de entrada.
                # Como el backtest actual compra todo de una vez (shares_to_buy = cash // price), 
                # el precio de entrada es el precio de la última compra.
                
                # Buscar la última compra en trades
                last_buy = next((t for t in reversed(trades) if t["type"] == "BUY"), None)
                if last_buy:
                    entry_price = last_buy["price"]
                    pct_change = (price - entry_price) / entry_price
                    
                    # Stop Loss: -7%
                    if pct_change <= -0.07:
                        revenue = shares * price
                        cash += revenue
                        trades.append({
                            "type": "SELL",
                            "date": date.strftime("%Y-%m-%d"),
                            "price": price,
                            "shares": shares,
                            "reason": "Stop Loss (-7%) 🛑"
                        })
                        shares = 0
                        continue # Salir del loop de este día
                        
                    # Take Profit: +15%
                    if pct_change >= 0.15:
                        revenue = shares * price
                        cash += revenue
                        trades.append({
                            "type": "SELL",
                            "date": date.strftime("%Y-%m-%d"),
                            "price": price,
                            "shares": shares,
                            "reason": "Take Profit (+15%) 💰"
                        })
                        shares = 0
                        continue

            # COMPRA (Entry)
            # Hacemos la estrategia un poco más exigente (Score > 2.5 -> Score >= 3)
            # O mantenemos 2.5 pero confiamos en el Stop Loss.
            if score >= 2.5 and cash > 0:
                # Comprar todo lo posible
                shares_to_buy = cash // price
                if shares_to_buy > 0:
                    cost = shares_to_buy * price
                    cash -= cost
                    shares += shares_to_buy
                    trades.append({
                        "type": "BUY",
                        "date": date.strftime("%Y-%m-%d"),
                        "price": price,
                        "shares": shares_to_buy,
                        "score": score
                    })
            
            # VENTA (Exit) - Señal Técnica
            elif shares > 0:
                should_sell = False
                reason = ""
                
                if row['RSI'] > 70:
                    should_sell = True
                    reason = "RSI Overbought"
                elif price > row['BB_Upper']:
                    should_sell = True
                    reason = "Upper Bollinger"
                    
                if should_sell:
                    revenue = shares * price
                    cash += revenue
                    trades.append({
                        "type": "SELL",
                        "date": date.strftime("%Y-%m-%d"),
                        "price": price,
                        "shares": shares,
                        "reason": reason
                    })
                    shares = 0
            
            # Registrar valor diario
            portfolio_value = cash + (shares * price)
            equity_curve.append({
                "time": date.strftime("%Y-%m-%d"),
                "value": portfolio_value
            })
            
            # Benchmark Value
            bh_curve.append({
                "time": date.strftime("%Y-%m-%d"),
                "value": bh_shares * price
            })
            
        # Métricas Finales
        final_value = equity_curve[-1]['value']
        bh_final_value = bh_curve[-1]['value']
        
        # Calcular Max Drawdown
        max_drawdown = 0
        peak = -999999
        
        for point in equity_curve:
            value = point['value']
            if value > peak:
                peak = value
            
            dd = (peak - value) / peak
            if dd > max_drawdown:
                max_drawdown = dd
        
        return {
            "symbol": symbol,
            "initial_capital": initial_capital,
            "final_value": final_value,
            "return_pct": ((final_value - initial_capital) / initial_capital) * 100,
            "benchmark_return_pct": ((bh_final_value - initial_capital) / initial_capital) * 100,
            "max_drawdown": max_drawdown * 100, # En porcentaje
            "trades": trades,
            "equity_curve": equity_curve,
            "benchmark_curve": bh_curve
        }
