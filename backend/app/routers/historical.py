"""
Router de datos históricos.
Endpoints para obtener datos históricos de activos.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.config import ASSETS
from ml.data_loader import DataLoader
from ml.predictor import Predictor

router = APIRouter()

# Instancias globales
loader = DataLoader()
predictor = Predictor()


@router.get("/historical/{symbol}")
async def get_historical(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365, description="Días de historial")
):
    """
    Obtiene datos históricos de un activo.
    
    Args:
        symbol: Símbolo del activo
        days: Número de días de historial (1-365)
        
    Returns:
        Datos históricos con OHLCV
    """
    symbol = symbol.upper()
    
    if symbol not in ASSETS:
        raise HTTPException(
            status_code=404,
            detail=f"Activo '{symbol}' no encontrado"
        )
    
    result = predictor.get_historical_comparison(symbol, days)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Error al obtener datos históricos")
        )
    
    return result


@router.get("/historical/{symbol}/chart")
async def get_chart_data(
    symbol: str,
    days: int = Query(default=60, ge=7, le=365)
):
    """
    Obtiene datos formateados para gráficos.
    
    Args:
        symbol: Símbolo del activo
        days: Días de datos
        
    Returns:
        Datos en formato para Chart.js
    """
    symbol = symbol.upper()
    
    if symbol not in ASSETS:
        raise HTTPException(
            status_code=404,
            detail=f"Activo '{symbol}' no encontrado"
        )
    
    try:
        data = loader.fetch_data(symbol)
        recent = data.tail(days)
        
        # Formatear para Chart.js
        chart_data = {
            "labels": [d.strftime("%Y-%m-%d") for d in recent.index],
            "datasets": {
                "close": [float(v) for v in recent["Close"].values],
                "volume": [float(v) for v in recent["Volume"].values],
                "high": [float(v) for v in recent["High"].values],
                "low": [float(v) for v in recent["Low"].values]
            },
            "symbol": symbol,
            "name": ASSETS[symbol]["name"],
            "days": len(recent)
        }
        
        # Agregar predicciones si el modelo está disponible
        prediction = predictor.predict(symbol)
        if prediction.get("success"):
            # Agregar predicciones al dataset
            future_dates = []
            future_prices = []
            
            from datetime import datetime, timedelta
            last_date = recent.index[-1]
            
            for pred in prediction["predictions"]:
                future_date = last_date + timedelta(days=pred["day"])
                future_dates.append(future_date.strftime("%Y-%m-%d"))
                future_prices.append(pred["predicted_price"])
            
            chart_data["predictions"] = {
                "labels": future_dates,
                "values": future_prices
            }
        
        return chart_data
        
    except Exception as e:
        print(f"⚠️ Error fetching chart data for {symbol}: {e}")
        # Fallback: Mock Historical Data for Charts
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        print(f"⚠️ Generating mock chart data for {symbol}")
        
        # Base price
        base_prices = {
            "VOO": 450.0, "VTI": 230.0, "BND": 75.0, "QQQ": 400.0,
            "AAPL": 180.0, "MSFT": 370.0, "GOOGL": 140.0, "TSLA": 240.0,
            "NVDA": 480.0, "AMD": 120.0
        }
        start_price = base_prices.get(symbol, 100.0)
        
        # Generate dates
        end_date = datetime.now()
        dates = [(end_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
        dates.reverse()
        
        # Generate random walk prices
        prices = [start_price]
        volatility = 0.02
        if symbol in ["TSLA", "NVDA", "AMD"]: volatility = 0.035
        
        for _ in range(days - 1):
            change = np.random.normal(0, volatility)
            prices.append(prices[-1] * (1 + change))
            
        chart_data = {
            "labels": dates,
            "datasets": {
                "close": [round(p, 2) for p in prices],
                "volume": [int(np.random.uniform(100000, 5000000)) for _ in range(days)],
                "high": [round(p * (1 + abs(np.random.normal(0, 0.01))), 2) for p in prices],
                "low": [round(p * (1 - abs(np.random.normal(0, 0.01))), 2) for p in prices]
            },
            "symbol": symbol,
            "name": ASSETS.get(symbol, {}).get("name", symbol),
            "days": days,
            "is_mock": True
        }
        
        return chart_data


@router.get("/historical/{symbol}/latest")
async def get_latest_price(symbol: str):
    """
    Obtiene el precio más reciente de un activo.
    
    Args:
        symbol: Símbolo del activo
        
    Returns:
        Información del precio actual
    """
    symbol = symbol.upper()
    
    if symbol not in ASSETS:
        raise HTTPException(
            status_code=404,
            detail=f"Activo '{symbol}' no encontrado"
        )
    
    try:
        price_info = loader.get_latest_price(symbol)
        return price_info
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener precio: {str(e)}"
        )
