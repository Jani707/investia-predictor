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
        # period="2y" es seguro para cubrir 365 + 200 días
        hist = ticker.history(period="2y")
        
        if hist.empty:
            return {"error": "No data found"}
            
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
            
            # COMPRA (Entry)
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
            
            # VENTA (Exit) - Lógica simple de salida
            # Vender si RSI sobrecomprado (>70) o Precio > Banda Superior (Ganancia rápida)
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
        
        return {
            "symbol": symbol,
            "initial_capital": initial_capital,
            "final_value": final_value,
            "return_pct": ((final_value - initial_capital) / initial_capital) * 100,
            "benchmark_return_pct": ((bh_final_value - initial_capital) / initial_capital) * 100,
            "trades": trades,
            "equity_curve": equity_curve,
            "benchmark_curve": bh_curve
        }
