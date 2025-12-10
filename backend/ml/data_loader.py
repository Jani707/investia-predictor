"""
Módulo de carga de datos financieros.
Utiliza yfinance para obtener datos históricos de activos.
"""
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

import pandas as pd
import yfinance as yf

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import ASSETS, DATA_CONFIG, DATA_DIR


class DataLoader:
    """
    Carga datos financieros desde yfinance con caché local.
    """
    
    def __init__(self, cache_dir: Path = DATA_DIR):
        """
        Inicializa el DataLoader.
        
        Args:
            cache_dir: Directorio para almacenar caché de datos
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        
    def _get_cache_path(self, symbol: str) -> Path:
        """Obtiene la ruta del archivo de caché para un símbolo."""
        return self.cache_dir / f"{symbol}_data.pkl"
    
    def _is_cache_valid(self, symbol: str, max_age_hours: int = 24) -> bool:
        """
        Verifica si el caché es válido (no más antiguo que max_age_hours).
        
        Args:
            symbol: Símbolo del activo
            max_age_hours: Máxima edad del caché en horas
            
        Returns:
            True si el caché es válido, False si no
        """
        cache_path = self._get_cache_path(symbol)
        
        if not cache_path.exists():
            return False
            
        cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - cache_time
        
        return age < timedelta(hours=max_age_hours)
    
    def _load_from_cache(self, symbol: str) -> Optional[pd.DataFrame]:
        """Carga datos desde el caché local."""
        cache_path = self._get_cache_path(symbol)
        
        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def _save_to_cache(self, symbol: str, data: pd.DataFrame) -> None:
        """Guarda datos en el caché local."""
        cache_path = self._get_cache_path(symbol)
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    
    def fetch_data(
        self, 
        symbol: str, 
        period: str = None,
        interval: str = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Obtiene datos históricos para un símbolo.
        
        Args:
            symbol: Símbolo del activo (ej: 'VOO')
            period: Período de datos (ej: '2y', '1y', '6mo')
            interval: Intervalo de datos (ej: '1d', '1h')
            use_cache: Si usar caché local
            
        Returns:
            DataFrame con datos históricos (Open, High, Low, Close, Volume)
        """
        period = period or DATA_CONFIG["history_period"]
        interval = interval or DATA_CONFIG["interval"]
        
        # Intentar cargar desde caché
        if use_cache and self._is_cache_valid(symbol):
            cached_data = self._load_from_cache(symbol)
            if cached_data is not None:
                print(f"✓ Datos de {symbol} cargados desde caché")
                return cached_data
        
        # Descargar desde yfinance con retry
        print(f"⬇ Descargando datos de {symbol}...")
        
        max_retries = 3
        data = None
        
        for attempt in range(max_retries):
            try:
                # Método 1: Usar yf.download (más estable)
                import time
                if attempt > 0:
                    print(f"   Reintentando ({attempt + 1}/{max_retries})...")
                    time.sleep(2)  # Esperar antes de reintentar
                
                data = yf.download(
                    symbol, 
                    period=period, 
                    interval=interval,
                    progress=False,
                    auto_adjust=True,
                    threads=False
                )
                
                if not data.empty:
                    break
                    
                # Si está vacío, intentar con Ticker
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, interval=interval)
                
                if not data.empty:
                    break
                    
            except Exception as e:
                print(f"   ⚠ Intento {attempt + 1} falló: {str(e)[:50]}")
                if attempt == max_retries - 1:
                    raise
        
        if data is None or data.empty:
            # Intentar cargar caché antiguo como fallback
            cached_data = self._load_from_cache(symbol)
            if cached_data is not None:
                print(f"⚠ Usando caché antiguo para {symbol}")
                return cached_data
            raise ValueError(f"No se encontraron datos para {symbol}")
        
        # Limpiar datos
        data = self._clean_data(data)
        
        # Guardar en caché
        if use_cache:
            self._save_to_cache(symbol, data)
            print(f"✓ Datos de {symbol} guardados en caché")
        
        return data
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y prepara los datos.
        
        Args:
            data: DataFrame con datos crudos
            
        Returns:
            DataFrame limpio
        """
        # Remover filas con valores nulos
        data = data.dropna()
        
        # Asegurar que tenemos las columnas necesarias
        required_cols = DATA_CONFIG["features"]
        available_cols = [col for col in required_cols if col in data.columns]
        
        if not available_cols:
            raise ValueError("No se encontraron las columnas requeridas en los datos")
        
        data = data[available_cols]
        
        # Ordenar por fecha
        data = data.sort_index()
        
        return data
    
    def fetch_all_assets(self, use_cache: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Obtiene datos para todos los activos configurados.
        
        Args:
            use_cache: Si usar caché local
            
        Returns:
            Diccionario con símbolo -> DataFrame
        """
        all_data = {}
        
        for symbol in ASSETS.keys():
            try:
                all_data[symbol] = self.fetch_data(symbol, use_cache=use_cache)
            except Exception as e:
                print(f"⚠ No se pudieron obtener datos de {symbol}: {str(e)}")
        
        return all_data
    
    def get_latest_price(self, symbol: str) -> Dict:
        """
        Obtiene el precio más reciente de un activo.
        
        Args:
            symbol: Símbolo del activo
            
        Returns:
            Diccionario con información del precio actual
        """
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "symbol": symbol,
            "name": ASSETS.get(symbol, {}).get("name", symbol),
            "current_price": info.get("regularMarketPrice", 0),
            "previous_close": info.get("previousClose", 0),
            "change": info.get("regularMarketChange", 0),
            "change_percent": info.get("regularMarketChangePercent", 0),
            "volume": info.get("regularMarketVolume", 0),
            "market_cap": info.get("marketCap", 0),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test del módulo
    loader = DataLoader()
    
    print("\n=== Test de DataLoader ===\n")
    
    # Probar descarga de un activo
    data = loader.fetch_data("VOO")
    print(f"\nDatos de VOO:")
    print(f"  Período: {data.index[0]} a {data.index[-1]}")
    print(f"  Registros: {len(data)}")
    print(f"  Columnas: {list(data.columns)}")
    print(f"\nÚltimos 5 registros:")
    print(data.tail())
