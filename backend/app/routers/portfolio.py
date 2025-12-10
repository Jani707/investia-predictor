"""
Router de portafolio.
Endpoints para generar portafolios de inversión.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.config import ASSETS
from ml.predictor import Predictor

router = APIRouter()
predictor = Predictor()

class PortfolioRequest(BaseModel):
    risk_profile: str  # low, medium, high, mixed
    amount: float

@router.post("/portfolio/generate")
async def generate_portfolio(request: PortfolioRequest):
    """
    Genera una propuesta de portafolio basada en el perfil de riesgo.
    """
    risk = request.risk_profile.lower()
    amount = request.amount
    
    # Filtrar activos por riesgo
    candidates = []
    
    if risk == "mixed":
        # Incluir un mix balanceado
        candidates = list(ASSETS.keys())
    else:
        # Filtrar por nivel específico
        candidates = [s for s, data in ASSETS.items() if data["risk"] == risk]
    
    if not candidates:
        raise HTTPException(status_code=400, detail="Perfil de riesgo no válido")
        
    # Obtener predicciones (o usar datos base si no hay predicción)
    scored_candidates = []
    
    for symbol in candidates:
        # Intentar obtener predicción real
        prediction = predictor.predict(symbol)
        
        if prediction.get("success"):
            growth = prediction["average_change_percent"]
        else:
            # Si no hay modelo entrenado, usar un score base según el riesgo para demo
            # Esto permite que funcione inmediatamente sin entrenar todo
            base_scores = {"low": 2.0, "medium": 5.0, "high": 8.0}
            risk_level = ASSETS[symbol]["risk"]
            growth = base_scores.get(risk_level, 3.0)
            
        scored_candidates.append({
            "symbol": symbol,
            "name": ASSETS[symbol]["name"],
            "risk": ASSETS[symbol]["risk"],
            "growth": growth,
            "price": prediction.get("current_price", 100.0) # Precio dummy si falla
        })
    
    # Ordenar por potencial de crecimiento
    scored_candidates.sort(key=lambda x: x["growth"], reverse=True)
    
    # Seleccionar top 5 (o menos si hay pocos)
    selected = scored_candidates[:5]
    
    # Asignar pesos (simplificado: proporcional al ranking inverso)
    total_score = sum(range(1, len(selected) + 1))
    allocation = []
    remaining_amount = amount
    
    for i, asset in enumerate(selected):
        # Peso: el primero recibe más
        weight = (len(selected) - i) / total_score
        
        # Ajustar para mixed: asegurar diversificación
        if risk == "mixed" and asset["risk"] == "high" and weight > 0.3:
            weight = 0.3 # Cap riesgo alto en portafolio mixto
            
        invest_amt = round(amount * weight, 2)
        shares = invest_amt / asset["price"]
        
        allocation.append({
            "symbol": asset["symbol"],
            "name": asset["name"],
            "risk": asset["risk"],
            "percentage": round(weight * 100, 1),
            "amount": invest_amt,
            "shares": round(shares, 2),
            "expected_growth": asset["growth"],
            "recent_earnings": ASSETS[asset["symbol"]].get("recent_earnings", "N/A"),
            "investment_thesis": ASSETS[asset["symbol"]].get("investment_thesis", "N/A")
        })
        
    return {
        "risk_profile": risk,
        "total_amount": amount,
        "allocation": allocation,
        "diversity_score": "Alta" if len(allocation) >= 4 else "Media"
    }
