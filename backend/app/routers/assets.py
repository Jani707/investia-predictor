"""
Router de activos.
Endpoints para obtener información de activos disponibles.
"""
from fastapi import APIRouter
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.config import ASSETS

router = APIRouter()


@router.get("/assets")
async def get_all_assets():
    """
    Obtiene lista de todos los activos disponibles.
    
    Returns:
        Lista de activos con sus propiedades
    """
    assets_list = [
        {
            "symbol": symbol,
            **info
        }
        for symbol, info in ASSETS.items()
    ]
    
    return {
        "assets": assets_list,
        "total": len(assets_list)
    }


@router.get("/assets/{symbol}")
async def get_asset_info(symbol: str):
    """
    Obtiene información detallada de un activo.
    
    Args:
        symbol: Símbolo del activo
        
    Returns:
        Información del activo
    """
    symbol = symbol.upper()
    
    if symbol not in ASSETS:
        return {
            "error": True,
            "message": f"Activo '{symbol}' no encontrado",
            "available": list(ASSETS.keys())
        }
    
    return {
        "symbol": symbol,
        **ASSETS[symbol]
    }


@router.get("/assets/risk/{level}")
async def get_assets_by_risk(level: str):
    """
    Filtra activos por nivel de riesgo.
    
    Args:
        level: Nivel de riesgo (very_low, low, medium_low, medium)
        
    Returns:
        Activos filtrados por nivel de riesgo
    """
    level = level.lower()
    valid_levels = ["very_low", "low", "medium_low", "medium"]
    
    if level not in valid_levels:
        return {
            "error": True,
            "message": f"Nivel de riesgo inválido. Opciones: {valid_levels}"
        }
    
    filtered = [
        {"symbol": symbol, **info}
        for symbol, info in ASSETS.items()
        if info.get("risk") == level
    ]
    
    return {
        "risk_level": level,
        "assets": filtered,
        "total": len(filtered)
    }
