"""
Router de métricas del modelo.
Endpoints para obtener métricas de precisión y rendimiento.
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.config import ASSETS, MODELS_DIR
from ml.trainer import Trainer

router = APIRouter()

# Instancia del trainer para acceder a estados
trainer = Trainer()


@router.get("/metrics/all")
async def get_all_metrics():
    """
    Obtiene métricas de todos los modelos entrenados.
    
    Returns:
        Métricas agregadas de todos los activos
    """
    status = trainer.get_training_status()
    
    metrics_list = []
    trained_count = 0
    
    for symbol, info in status.items():
        if info.get("model_exists"):
            trained_count += 1
            metrics_list.append({
                "symbol": symbol,
                "name": ASSETS[symbol]["name"],
                "last_trained": info.get("last_trained"),
                "metrics": info.get("metrics", {})
            })
    
    # Calcular promedios
    if metrics_list:
        avg_mae = sum(m["metrics"].get("mae", 0) for m in metrics_list) / len(metrics_list)
        avg_rmse = sum(m["metrics"].get("rmse", 0) for m in metrics_list) / len(metrics_list)
        avg_dir_acc = sum(m["metrics"].get("directional_accuracy", 0) for m in metrics_list) / len(metrics_list)
    else:
        avg_mae = avg_rmse = avg_dir_acc = 0
    
    return {
        "models": metrics_list,
        "summary": {
            "total_assets": len(ASSETS),
            "trained_models": trained_count,
            "untrained_models": len(ASSETS) - trained_count,
            "average_mae": avg_mae,
            "average_rmse": avg_rmse,
            "average_directional_accuracy": avg_dir_acc
        }
    }


@router.get("/metrics/{symbol}")
async def get_symbol_metrics(symbol: str):
    """
    Obtiene métricas detalladas de un modelo específico.
    
    Args:
        symbol: Símbolo del activo
        
    Returns:
        Métricas detalladas del modelo
    """
    symbol = symbol.upper()
    
    if symbol not in ASSETS:
        raise HTTPException(
            status_code=404,
            detail=f"Activo '{symbol}' no encontrado"
        )
    
    results_path = MODELS_DIR / f"{symbol}_results.json"
    
    if not results_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No hay métricas disponibles para {symbol}. El modelo no ha sido entrenado."
        )
    
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    return {
        "symbol": symbol,
        "name": ASSETS[symbol]["name"],
        "training_info": {
            "trained_at": results.get("trained_at"),
            "epochs_completed": results.get("epochs_completed"),
            "data_points": results.get("data_points"),
            "train_samples": results.get("train_samples"),
            "test_samples": results.get("test_samples")
        },
        "metrics": results.get("metrics", {}),
        "loss_history": {
            "final_loss": results.get("final_loss"),
            "final_val_loss": results.get("final_val_loss")
        }
    }


@router.get("/metrics/status")
async def get_training_status():
    """
    Obtiene el estado de entrenamiento de todos los modelos.
    
    Returns:
        Estado de cada modelo (entrenado/no entrenado)
    """
    status = trainer.get_training_status()
    
    return {
        "models": [
            {
                "symbol": symbol,
                "name": ASSETS[symbol]["name"],
                "trained": info.get("model_exists", False),
                "last_trained": info.get("last_trained"),
                "has_metrics": info.get("results_exist", False)
            }
            for symbol, info in status.items()
        ],
        "summary": {
            "total": len(status),
            "trained": sum(1 for info in status.values() if info.get("model_exists")),
            "pending": sum(1 for info in status.values() if not info.get("model_exists"))
        }
    }
