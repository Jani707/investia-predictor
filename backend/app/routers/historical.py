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
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener datos: {str(e)}"
        )


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
