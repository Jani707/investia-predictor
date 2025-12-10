"""
Arquitectura del modelo LSTM para predicción de precios.
"""
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import os

# Silenciar warnings de TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow import keras
from keras.models import Sequential, load_model
from keras.layers import LSTM, Dense, Dropout, BatchNormalization, Input
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import MODEL_CONFIG, MODELS_DIR


class LSTMModel:
    """
    Modelo LSTM para predicción de precios financieros.
    """
    
    def __init__(
        self,
        sequence_length: int = None,
        n_features: int = 7,
        prediction_days: int = None,
        lstm_units: int = None,
        dropout_rate: float = None
    ):
        """
        Inicializa el modelo LSTM.
        
        Args:
            sequence_length: Longitud de la secuencia de entrada
            n_features: Número de features por paso temporal
            prediction_days: Días a predecir
            lstm_units: Unidades en las capas LSTM
            dropout_rate: Tasa de dropout para regularización
        """
        self.sequence_length = sequence_length or MODEL_CONFIG["sequence_length"]
        self.n_features = n_features
        self.prediction_days = prediction_days or MODEL_CONFIG["prediction_days"]
        self.lstm_units = lstm_units or MODEL_CONFIG["lstm_units"]
        self.dropout_rate = dropout_rate or MODEL_CONFIG["dropout_rate"]
        
        self.model = None
        self.history = None
        
    def build(self) -> Sequential:
        """
        Construye la arquitectura del modelo LSTM.
        
        Returns:
            Modelo Keras compilado
        """
        model = Sequential([
            # Input Layer
            Input(shape=(self.sequence_length, self.n_features)),
            
            # Primera capa LSTM
            LSTM(
                units=self.lstm_units * 2,
                return_sequences=True,
                name='lstm_1'
            ),
            BatchNormalization(),
            Dropout(self.dropout_rate),
            
            # Segunda capa LSTM
            LSTM(
                units=self.lstm_units,
                return_sequences=True,
                name='lstm_2'
            ),
            BatchNormalization(),
            Dropout(self.dropout_rate),
            
            # Tercera capa LSTM
            LSTM(
                units=self.lstm_units // 2,
                return_sequences=False,
                name='lstm_3'
            ),
            BatchNormalization(),
            Dropout(self.dropout_rate),
            
            # Capas densas
            Dense(self.lstm_units, activation='relu', name='dense_1'),
            Dropout(self.dropout_rate / 2),
            
            Dense(self.lstm_units // 2, activation='relu', name='dense_2'),
            
            # Capa de salida (predicción para N días)
            Dense(self.prediction_days, name='output')
        ])
        
        # Compilar modelo
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model
    
    def summary(self) -> None:
        """Imprime el resumen del modelo."""
        if self.model is None:
            self.build()
        self.model.summary()
    
    def get_callbacks(self, symbol: str) -> list:
        """
        Obtiene los callbacks para entrenamiento.
        
        Args:
            symbol: Símbolo del activo para nombrar checkpoints
            
        Returns:
            Lista de callbacks
        """
        callbacks = [
            # Early stopping para evitar overfitting
            EarlyStopping(
                monitor='val_loss',
                patience=MODEL_CONFIG["early_stopping_patience"],
                restore_best_weights=True,
                verbose=1
            ),
            
            # Guardar mejor modelo
            ModelCheckpoint(
                filepath=str(MODELS_DIR / f"{symbol}_best.keras"),
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            ),
            
            # Reducir learning rate cuando se estanca
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001,
                verbose=1
            )
        ]
        
        return callbacks
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray = None,
        y_val: np.ndarray = None,
        symbol: str = "model",
        epochs: int = None,
        batch_size: int = None
    ) -> dict:
        """
        Entrena el modelo.
        
        Args:
            X_train: Datos de entrenamiento
            y_train: Etiquetas de entrenamiento
            X_val: Datos de validación (opcional)
            y_val: Etiquetas de validación (opcional)
            symbol: Símbolo del activo
            epochs: Número de épocas
            batch_size: Tamaño del batch
            
        Returns:
            Historial de entrenamiento
        """
        if self.model is None:
            # Actualizar n_features basado en datos reales
            self.n_features = X_train.shape[2]
            self.build()
        
        epochs = epochs or MODEL_CONFIG["epochs"]
        batch_size = batch_size or MODEL_CONFIG["batch_size"]
        
        # Preparar datos de validación
        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val, y_val)
        
        print(f"\n🚀 Iniciando entrenamiento de {symbol}...")
        print(f"   Épocas: {epochs}")
        print(f"   Batch size: {batch_size}")
        print(f"   Secuencia: {self.sequence_length} pasos")
        print(f"   Features: {self.n_features}")
        print(f"   Predicción: {self.prediction_days} días\n")
        
        self.history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=validation_data,
            callbacks=self.get_callbacks(symbol),
            verbose=1
        )
        
        return self.history.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Genera predicciones.
        
        Args:
            X: Datos de entrada
            
        Returns:
            Predicciones
        """
        if self.model is None:
            raise ValueError("El modelo no ha sido entrenado o cargado")
        
        return self.model.predict(X, verbose=0)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evalúa el modelo en datos de test.
        
        Args:
            X_test: Datos de test
            y_test: Etiquetas de test
            
        Returns:
            Diccionario con métricas
        """
        if self.model is None:
            raise ValueError("El modelo no ha sido entrenado o cargado")
        
        loss, mae = self.model.evaluate(X_test, y_test, verbose=0)
        
        # Calcular RMSE
        predictions = self.predict(X_test)
        rmse = np.sqrt(np.mean((predictions - y_test) ** 2))
        
        # Calcular accuracy direccional (si el precio sube o baja)
        if len(y_test.shape) > 1:
            # Para predicciones multi-día, usar primer día
            actual_direction = np.sign(y_test[:, 0] - np.roll(y_test[:, 0], 1))[1:]
            predicted_direction = np.sign(predictions[:, 0] - np.roll(predictions[:, 0], 1))[1:]
        else:
            actual_direction = np.sign(y_test - np.roll(y_test, 1))[1:]
            predicted_direction = np.sign(predictions.flatten() - np.roll(predictions.flatten(), 1))[1:]
        
        directional_accuracy = np.mean(actual_direction == predicted_direction)
        
        metrics = {
            "loss": float(loss),
            "mae": float(mae),
            "rmse": float(rmse),
            "directional_accuracy": float(directional_accuracy)
        }
        
        print(f"\n📊 Métricas del modelo:")
        print(f"   Loss (MSE): {loss:.6f}")
        print(f"   MAE: {mae:.6f}")
        print(f"   RMSE: {rmse:.6f}")
        print(f"   Accuracy direccional: {directional_accuracy:.2%}")
        
        return metrics
    
    def save(self, symbol: str, path: Path = None) -> None:
        """
        Guarda el modelo entrenado.
        
        Args:
            symbol: Símbolo del activo
            path: Directorio donde guardar
        """
        path = path or MODELS_DIR
        model_path = path / f"{symbol}_model.keras"
        
        self.model.save(model_path)
        print(f"✓ Modelo guardado en {model_path}")
    
    def load(self, symbol: str, path: Path = None) -> None:
        """
        Carga un modelo guardado.
        
        Args:
            symbol: Símbolo del activo
            path: Directorio donde buscar
        """
        path = path or MODELS_DIR
        model_path = path / f"{symbol}_model.keras"
        
        if not model_path.exists():
            # Intentar cargar el mejor modelo
            model_path = path / f"{symbol}_best.keras"
        
        if not model_path.exists():
            raise FileNotFoundError(f"No se encontró modelo para {symbol}")
        
        self.model = load_model(model_path)
        print(f"✓ Modelo cargado desde {model_path}")


if __name__ == "__main__":
    # Test del módulo
    print("\n=== Test de LSTMModel ===\n")
    
    model = LSTMModel(n_features=7)
    model.build()
    model.summary()
