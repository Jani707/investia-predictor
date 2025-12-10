#!/usr/bin/env python3
"""
Genera datos de demostración para pruebas cuando yfinance no está disponible.
Esto permite probar el sistema completo sin dependencia de Yahoo Finance.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.config import ASSETS, DATA_DIR

# Precios base aproximados para cada ETF
BASE_PRICES = {
    "VOO": 430,
    "VTI": 240,
    "BND": 72,
    "SCHD": 78,
    "VNQ": 88,
    "GLD": 190
}

def generate_realistic_prices(symbol: str, days: int = 500) -> pd.DataFrame:
    """
    Genera precios realistas con tendencia y volatilidad.
    """
    base_price = BASE_PRICES.get(symbol, 100)
    
    # Parámetros de simulación
    volatility = 0.015  # Volatilidad diaria
    trend = 0.0002  # Tendencia ligeramente alcista
    
    # Generar fechas
    end_date = datetime.now()
    dates = [end_date - timedelta(days=i) for i in range(days)]
    dates.reverse()
    
    # Generar retornos aleatorios con tendencia
    np.random.seed(42 + hash(symbol) % 1000)  # Seed consistente por símbolo
    returns = np.random.normal(trend, volatility, days)
    
    # Calcular precios
    prices = [base_price]
    for r in returns[1:]:
        new_price = prices[-1] * (1 + r)
        prices.append(max(new_price, base_price * 0.5))  # Mínimo 50% del precio base
    
    prices = np.array(prices)
    
    # Generar OHLCV
    high = prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
    low = prices * (1 - np.abs(np.random.normal(0, 0.01, days)))
    open_prices = low + (high - low) * np.random.random(days)
    volume = np.random.randint(1000000, 10000000, days)
    
    # Crear DataFrame
    df = pd.DataFrame({
        'Open': open_prices,
        'High': high,
        'Low': low,
        'Close': prices,
        'Volume': volume
    }, index=pd.DatetimeIndex(dates))
    
    return df

def generate_and_save_demo_data():
    """
    Genera y guarda datos de demostración para todos los activos.
    """
    DATA_DIR.mkdir(exist_ok=True)
    
    print("🎲 Generando datos de demostración...")
    print(f"   Directorio: {DATA_DIR}")
    print()
    
    for symbol in ASSETS.keys():
        print(f"   Generando {symbol}...", end=" ")
        
        df = generate_realistic_prices(symbol)
        
        # Guardar en caché (mismo formato que data_loader)
        cache_path = DATA_DIR / f"{symbol}_data.pkl"
        with open(cache_path, 'wb') as f:
            pickle.dump(df, f)
        
        print(f"✓ ({len(df)} registros, ${df['Close'].iloc[-1]:.2f})")
    
    print()
    print("✅ Datos de demostración generados exitosamente!")
    print()
    print("Ahora puedes entrenar los modelos con:")
    print("   python train.py --all")

if __name__ == "__main__":
    generate_and_save_demo_data()
