"""
Módulo de preprocesamiento de datos para LSTM.
Incluye normalización, creación de secuencias y feature engineering.
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path
import pickle

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import MODEL_CONFIG, DATA_CONFIG, DATA_DIR


class DataPreprocessor:
    """
    Preprocesa datos financieros para entrenamiento de LSTM.
    """
    
    def __init__(self, sequence_length: int = None):
        """
        Inicializa el preprocesador.
        
        Args:
            sequence_length: Longitud de las secuencias para LSTM
        """
        self.sequence_length = sequence_length or MODEL_CONFIG["sequence_length"]
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.fitted = False
        
    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega indicadores técnicos como features adicionales.
        
        Args:
            data: DataFrame con datos OHLCV
            
        Returns:
            DataFrame con indicadores técnicos agregados
        """
        df = data.copy()
        
        # Media Móvil Simple (SMA)
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Media Móvil Exponencial (EMA)
        df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        # Asegurar que usamos una Serie, no un DataFrame (por si hay columnas duplicadas)
        close_prices = df['Close']
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]
            
        df['BB_Middle'] = close_prices.rolling(window=20).mean()
        bb_std = close_prices.rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # Volatilidad
        df['Volatility'] = df['Close'].rolling(window=20).std()
        
        # Retorno diario
        df['Daily_Return'] = df['Close'].pct_change()
        
        # Eliminar filas con NaN (debido a los indicadores)
        df = df.dropna()
        
        return df
    
    def fit_scaler(self, data: np.ndarray) -> None:
        """
        Ajusta el escalador a los datos.
        
        Args:
            data: Array numpy con los datos
        """
        self.scaler.fit(data)
        self.fitted = True
    
    def transform(self, data: np.ndarray) -> np.ndarray:
        """
        Transforma los datos usando el escalador ajustado.
        
        Args:
            data: Array numpy con los datos
            
        Returns:
            Datos normalizados
        """
        if not self.fitted:
            self.fit_scaler(data)
        return self.scaler.transform(data)
    
    def inverse_transform(self, data: np.ndarray) -> np.ndarray:
        """
        Revierte la transformación de los datos.
        
        Args:
            data: Datos normalizados
            
        Returns:
            Datos en escala original
        """
        return self.scaler.inverse_transform(data)
    
    def create_sequences(
        self, 
        data: np.ndarray, 
        target_col: int = 0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crea secuencias para entrenamiento de LSTM.
        
        Args:
            data: Array numpy con datos normalizados
            target_col: Índice de la columna objetivo (default: 0 = Close)
            
        Returns:
            Tupla (X, y) con secuencias de entrada y valores objetivo
        """
        X, y = [], []
        
        for i in range(self.sequence_length, len(data)):
            X.append(data[i - self.sequence_length:i])
            y.append(data[i, target_col])
        
        return np.array(X), np.array(y)
    
    def create_multistep_sequences(
        self, 
        data: np.ndarray, 
        prediction_days: int = None,
        target_col: int = 0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crea secuencias para predicción multi-paso.
        
        Args:
            data: Array numpy con datos normalizados
            prediction_days: Número de días a predecir
            target_col: Índice de la columna objetivo
            
        Returns:
            Tupla (X, y) con secuencias de entrada y valores objetivo
        """
        prediction_days = prediction_days or MODEL_CONFIG["prediction_days"]
        X, y = [], []
        
        for i in range(self.sequence_length, len(data) - prediction_days + 1):
            X.append(data[i - self.sequence_length:i])
            y.append(data[i:i + prediction_days, target_col])
        
        return np.array(X), np.array(y)
    
    def prepare_data(
        self, 
        df: pd.DataFrame,
        add_indicators: bool = True,
        multistep: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Pipeline completo de preparación de datos.
        
        Args:
            df: DataFrame con datos OHLCV
            add_indicators: Si agregar indicadores técnicos
            multistep: Si usar predicción multi-paso
            
        Returns:
            Tupla (X_train, X_test, y_train, y_test)
        """
        # Agregar indicadores técnicos
        if add_indicators:
            df = self.add_technical_indicators(df)
        
        # Seleccionar features para el modelo
        # Usamos Close como objetivo principal
        feature_cols = ['Close', 'Volume', 'SMA_10', 'SMA_20', 'RSI', 'MACD', 'Volatility']
        available_cols = [col for col in feature_cols if col in df.columns]
        
        if 'Close' not in available_cols:
            available_cols = ['Close'] + [c for c in available_cols if c != 'Close']
        
        data = df[available_cols].values
        
        # Normalizar datos
        scaled_data = self.transform(data)
        
        # Crear secuencias
        if multistep:
            X, y = self.create_multistep_sequences(scaled_data)
        else:
            X, y = self.create_sequences(scaled_data)
        
        # Dividir en train/test
        split_idx = int(len(X) * (1 - MODEL_CONFIG["validation_split"]))
        
        X_train = X[:split_idx]
        X_test = X[split_idx:]
        y_train = y[:split_idx]
        y_test = y[split_idx:]
        
        print(f"✓ Datos preparados:")
        print(f"  Train: {X_train.shape[0]} muestras")
        print(f"  Test: {X_test.shape[0]} muestras")
        print(f"  Features: {X_train.shape[2]} por paso temporal")
        print(f"  Secuencia: {X_train.shape[1]} pasos")
        
        return X_train, X_test, y_train, y_test
    
    def save_scaler(self, symbol: str, path: Path = None) -> None:
        """
        Guarda el escalador para uso posterior.
        
        Args:
            symbol: Símbolo del activo
            path: Directorio donde guardar
        """
        path = path or DATA_DIR
        scaler_path = path / f"{symbol}_scaler.pkl"
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"✓ Scaler guardado en {scaler_path}")
    
    def load_scaler(self, symbol: str, path: Path = None) -> None:
        """
        Carga un escalador guardado.
        
        Args:
            symbol: Símbolo del activo
            path: Directorio donde buscar
        """
        path = path or DATA_DIR
        scaler_path = path / f"{symbol}_scaler.pkl"
        
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        self.fitted = True
        print(f"✓ Scaler cargado desde {scaler_path}")


if __name__ == "__main__":
    # Test del módulo
    from data_loader import DataLoader
    
    print("\n=== Test de DataPreprocessor ===\n")
    
    loader = DataLoader()
    data = loader.fetch_data("VOO")
    
    preprocessor = DataPreprocessor()
    
    # Agregar indicadores
    data_with_indicators = preprocessor.add_technical_indicators(data)
    print(f"Columnas después de indicadores: {list(data_with_indicators.columns)}")
    
    # Preparar datos
    X_train, X_test, y_train, y_test = preprocessor.prepare_data(data)
    
    print(f"\nForma de X_train: {X_train.shape}")
    print(f"Forma de y_train: {y_train.shape}")
