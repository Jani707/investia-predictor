"""
Módulo de predicción para generar predicciones con modelos entrenados.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import ASSETS, MODEL_CONFIG, MODELS_DIR, DATA_DIR
from ml.data_loader import DataLoader
from ml.preprocessor import DataPreprocessor
from ml.lstm_model import LSTMModel


class Predictor:
    """
    Genera predicciones utilizando modelos LSTM entrenados.
    """
    
    def __init__(self):
        """Inicializa el predictor."""
        self.loader = DataLoader()
        self.models = {}
        self.preprocessors = {}
        self.loaded_symbols = set()
        
    def load_model(self, symbol: str) -> bool:
        """
        Carga un modelo entrenado y su scaler.
        
        Args:
            symbol: Símbolo del activo
            
        Returns:
            True si se cargó exitosamente, False si no
        """
        if symbol in self.loaded_symbols:
            return True
        
        try:
            # Cargar modelo
            model = LSTMModel()
            model.load(symbol)
            self.models[symbol] = model
            
            # Cargar scaler
            preprocessor = DataPreprocessor()
            preprocessor.load_scaler(symbol)
            self.preprocessors[symbol] = preprocessor
            
            self.loaded_symbols.add(symbol)
            return True
            
        except Exception as e:
            print(f"⚠️ No se pudo cargar modelo para {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def predict(self, symbol: str) -> Dict:
        """
        Genera predicción para un símbolo.
        
        Args:
            symbol: Símbolo del activo
            
        Returns:
            Diccionario con predicción y metadatos
        """
        # Asegurar que el modelo está cargado
        if not self.load_model(symbol):
            print(f"⚠️ Model for {symbol} not found. Falling back to Rule-Based Analysis.")
            return self._predict_rule_based(symbol)
        
        try:
            # Obtener datos recientes
            data = self.loader.fetch_data(symbol)
            
            # Preprocesar
            preprocessor = self.preprocessors[symbol]
            data_with_indicators = preprocessor.add_technical_indicators(data)
            
            # Seleccionar features
            feature_cols = ['Close', 'Volume', 'SMA_10', 'SMA_20', 'RSI', 'MACD', 'Volatility']
            available_cols = [col for col in feature_cols if col in data_with_indicators.columns]
            
            features = data_with_indicators[available_cols].values
            
            # Normalizar
            scaled_data = preprocessor.transform(features)
            
            # Crear secuencia para predicción (últimos N días)
            sequence_length = MODEL_CONFIG["sequence_length"]
            X = scaled_data[-sequence_length:].reshape(1, sequence_length, -1)
            
            # Generar predicción
            model = self.models[symbol]
            prediction_scaled = model.predict(X)[0]
            
            # Desnormalizar predicción
            # Creamos un array con la forma correcta para inverse_transform
            prediction_full = np.zeros((len(prediction_scaled), len(available_cols)))
            prediction_full[:, 0] = prediction_scaled  # Close está en posición 0
            
            prediction_prices = preprocessor.inverse_transform(prediction_full)[:, 0]
            
            # Obtener precio actual
            current_price = float(data['Close'].iloc[-1])
            
            # Calcular cambios porcentuales
            predicted_changes = []
            for i, pred_price in enumerate(prediction_prices):
                change_pct = ((pred_price - current_price) / current_price) * 100
                predicted_changes.append({
                    "day": i + 1,
                    "predicted_price": float(pred_price),
                    "change_percent": float(change_pct)
                })
            
            # Obtener confianza del modelo
            confidence = self._calculate_confidence(symbol)
            
            # Determinar tendencia
            avg_change = np.mean([p["change_percent"] for p in predicted_changes])
            if avg_change > 1:
                trend = "bullish"
                recommendation = "COMPRAR"
            elif avg_change < -1:
                trend = "bearish"
                recommendation = "VENDER"
            else:
                trend = "neutral"
                recommendation = "MANTENER"
            
            result = {
                "symbol": symbol,
                "name": ASSETS.get(symbol, {}).get("name", symbol),
                "description": ASSETS.get(symbol, {}).get("description", ""),
                "current_price": current_price,
                "predictions": predicted_changes,
                "average_change_percent": float(avg_change),
                "trend": trend,
                "recommendation": recommendation,
                "confidence": confidence,
                "generated_at": datetime.now().isoformat(),
                "prediction_days": MODEL_CONFIG["prediction_days"],
                "success": True
            }
            
            return result
            
        except Exception as e:
            return {
                "symbol": symbol,
                "error": str(e),
                "success": False
            }
    
    def predict_all(self) -> List[Dict]:
        """
        Genera predicciones para todos los activos.
        
        Returns:
            Lista de predicciones
        """
        predictions = []
        
        for symbol in ASSETS.keys():
            prediction = self.predict(symbol)
            predictions.append(prediction)
        
        # Ordenar por cambio porcentual esperado (mejores primero)
        predictions.sort(
            key=lambda x: x.get("average_change_percent", -999),
            reverse=True
        )
        
        return predictions
    
    def _calculate_confidence(self, symbol: str) -> Dict:
        """
        Calcula la confianza del modelo basada en métricas de entrenamiento.
        
        Args:
            symbol: Símbolo del activo
            
        Returns:
            Diccionario con métricas de confianza
        """
        results_path = MODELS_DIR / f"{symbol}_results.json"
        
        if not results_path.exists():
            return {
                "score": 0.5,
                "level": "medium",
                "details": "Sin datos de entrenamiento disponibles"
            }
        
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        metrics = results.get("metrics", {})
        directional_acc = metrics.get("directional_accuracy", 0.5)
        
        # Calcular score de confianza (0-1)
        confidence_score = min(1.0, directional_acc * 1.2)  # Boost ligeramente
        
        if confidence_score >= 0.7:
            level = "high"
        elif confidence_score >= 0.5:
            level = "medium"
        else:
            level = "low"
        
        return {
            "score": float(confidence_score),
            "level": level,
            "directional_accuracy": float(directional_acc),
            "mae": metrics.get("mae"),
            "rmse": metrics.get("rmse")
        }
    
    def get_historical_comparison(self, symbol: str, days: int = 30) -> Dict:
        """
        Compara predicciones pasadas con valores reales.
        
        Args:
            symbol: Símbolo del activo
            days: Días a comparar
            
        Returns:
            Diccionario con comparación histórica
        """
        try:
            data = self.loader.fetch_data(symbol)
            
            # Obtener últimos N días
            recent_data = data.tail(days)
            
            historical = []
            for date, row in recent_data.iterrows():
                historical.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"])
                })
            
            return {
                "symbol": symbol,
                "historical_data": historical,
                "days": len(historical),
                "success": True
            }
            
        except Exception as e:
            return {
                "symbol": symbol,
                "error": str(e),
                "success": False
            }


    def _predict_rule_based(self, symbol: str) -> Dict:
        """
        Genera una predicción basada en reglas (fallback cuando no hay modelo ML).
        """
        from app.services.analysis_service import AnalysisService
        
        analysis = AnalysisService.analyze_symbol(symbol)
        
        if not analysis:
            return {
                "symbol": symbol,
                "error": "No se pudo analizar el activo (Datos insuficientes)",
                "success": False
            }
            
        # Generar predicciones sintéticas basadas en el score
        current_price = analysis["current_price"]
        score = analysis["score"]
        
        # Factor de proyección (muy simplificado)
        daily_change = 0
        if score >= 2.5: daily_change = 0.005 # +0.5% diario
        elif score >= 1: daily_change = 0.002 # +0.2% diario
        elif score <= -2: daily_change = -0.005 # -0.5% diario
        elif score <= -1: daily_change = -0.002 # -0.2% diario
        
        predictions = []
        price = current_price
        
        for i in range(5):
            price = price * (1 + daily_change)
            change_pct = ((price - current_price) / current_price) * 100
            predictions.append({
                "day": i + 1,
                "predicted_price": price,
                "change_percent": change_pct
            })
            
        return {
            "symbol": symbol,
            "name": ASSETS.get(symbol, {}).get("name", symbol),
            "description": ASSETS.get(symbol, {}).get("description", "Análisis Técnico"),
            "current_price": current_price,
            "predictions": predictions,
            "average_change_percent": predictions[-1]["change_percent"], # Cambio a 5 días
            "trend": "bullish" if score > 0 else "bearish" if score < 0 else "neutral",
            "recommendation": analysis["recommendation"],
            "confidence": {
                "score": 0.7 if abs(score) > 2 else 0.5,
                "level": "medium",
                "directional_accuracy": 0.0, # No aplica
                "details": "Basado en Análisis Técnico (RSI, MACD, Sentimiento)"
            },
            "sentiment": analysis.get("sentiment"),
            "generated_at": datetime.now().isoformat(),
            "prediction_days": 5,
            "success": True,
            "is_fallback": True
        }


if __name__ == "__main__":
    # Test del módulo
    print("\n=== Test de Predictor ===\n")
    
    predictor = Predictor()
    
    # Probar con un símbolo
    result = predictor.predict("VOO")
    
    if result.get("success"):
        print(f"Símbolo: {result['symbol']}")
        print(f"Precio actual: ${result['current_price']:.2f}")
        print(f"Tendencia: {result['trend']}")
        print(f"Recomendación: {result['recommendation']}")
        print(f"\nPredicciones:")
        for p in result['predictions']:
            print(f"  Día {p['day']}: ${p['predicted_price']:.2f} ({p['change_percent']:+.2f}%)")
    else:
        print(f"Error: {result.get('error')}")
