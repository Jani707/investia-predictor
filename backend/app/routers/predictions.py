"""
Router de predicciones.
Endpoints para obtener predicciones del modelo LSTM.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.config import ASSETS
from ml.predictor import Predictor

router = APIRouter()

# Instancia global del predictor
predictor = Predictor()


from app.services.analysis_service import AnalysisService

@router.post("/predict/refresh")
async def refresh_predictions():
    """
    Fuerza una actualización de las predicciones (Real-Time).
    """
    try:
        print("🔄 Manual refresh triggered via API")
        predictions = AnalysisService.update_cache()
        return {
            "status": "success",
            "message": "Predicciones actualizadas correctamente",
            "count": len(predictions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/all")
async def predict_all():
    """
    Obtiene predicciones para todos los activos configurados.
    
    Returns:
        Lista de predicciones ordenadas por potencial de ganancia
    """
    # Usar caché para respuesta instantánea
    predictions = AnalysisService.get_cached_predictions()
    
    # Si la caché está vacía (primer arranque), devolver lista vacía pero con status 202 (Accepted)
    # O simplemente vacía para que el frontend no rompa, pero indicando que cargue de nuevo
    if not predictions:
        print("⚠️ Cache miss in /predict/all. Returning empty list.")
        return {
            "predictions": [],
            "failed": [],
            "total": 0,
            "successful_count": 0,
            "status": "loading"
        }
    
    successful = [p for p in predictions if p.get("success")]
    failed = [p for p in predictions if not p.get("success")]
    
    return {
        "predictions": successful,
        "failed": failed,
        "total": len(predictions),
        "successful_count": len(successful)
    }


@router.get("/predict/{symbol}")
async def predict_symbol(symbol: str):
    """
    Obtiene predicción para un activo específico.
    
    Args:
        symbol: Símbolo del activo (ej: VOO, VTI)
        
    Returns:
        Predicción detallada con recomendación
    """
    symbol = symbol.upper()
    
    if symbol not in ASSETS:
        raise HTTPException(
            status_code=404,
            detail=f"Activo '{symbol}' no encontrado. Disponibles: {list(ASSETS.keys())}"
        )
    
    prediction = predictor.predict(symbol)
    
    if not prediction.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar predicción: {prediction.get('error', 'Error desconocido')}"
        )
    
    return prediction


@router.get("/predict/{symbol}/summary")
async def predict_symbol_summary(symbol: str):
    """
    Obtiene un resumen simplificado de la predicción.
    
    Args:
        symbol: Símbolo del activo
        
    Returns:
        Resumen con precio actual, predicción y recomendación
    """
    symbol = symbol.upper()
    prediction = predictor.predict(symbol)
    
    if not prediction.get("success"):
        raise HTTPException(
            status_code=500,
            detail=prediction.get("error", "Error al generar predicción")
        )
    
    # Resumen simplificado
    return {
        "symbol": prediction["symbol"],
        "name": prediction["name"],
        "current_price": prediction["current_price"],
        "predicted_price_5d": prediction["predictions"][-1]["predicted_price"],
        "change_percent_5d": prediction["predictions"][-1]["change_percent"],
        "trend": prediction["trend"],
        "recommendation": prediction["recommendation"],
        "confidence_level": prediction["confidence"]["level"],
        "generated_at": prediction["generated_at"]
    }
