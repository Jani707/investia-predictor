"""
Pipeline de entrenamiento para el modelo LSTM.
Coordina la carga de datos, preprocesamiento y entrenamiento.
"""
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import numpy as np

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import ASSETS, MODEL_CONFIG, MODELS_DIR, DATA_DIR
from ml.data_loader import DataLoader
from ml.preprocessor import DataPreprocessor
from ml.lstm_model import LSTMModel


class Trainer:
    """
    Coordina el entrenamiento de modelos LSTM para múltiples activos.
    """
    
    def __init__(self):
        """Inicializa el trainer."""
        self.loader = DataLoader()
        self.training_results = {}
        
    def train_symbol(
        self,
        symbol: str,
        epochs: int = None,
        force_download: bool = False
    ) -> Dict:
        """
        Entrena un modelo para un símbolo específico.
        
        Args:
            symbol: Símbolo del activo
            epochs: Número de épocas
            force_download: Si forzar descarga de datos nuevos
            
        Returns:
            Diccionario con resultados del entrenamiento
        """
        print(f"\n{'='*60}")
        print(f"🎯 ENTRENANDO MODELO PARA: {symbol}")
        print(f"   {ASSETS.get(symbol, {}).get('name', 'Desconocido')}")
        print(f"{'='*60}")
        
        try:
            # 1. Cargar datos
            # Para entrenamiento incremental, preferimos datos frescos
            # Si force_download es False, aún verificamos la caché (24h)
            # Pero para asegurar "tiempo real" como pidió el usuario, forzamos descarga si existe modelo
            should_force = force_download
            if not should_force:
                # Verificar si existe modelo previo, si es así, conviene actualizar datos
                if (MODELS_DIR / f"{symbol}_model.keras").exists():
                    print("   ℹ️ Modelo previo detectado: Forzando actualización de datos...")
                    should_force = True

            print("\n📥 Cargando datos...")
            data = self.loader.fetch_data(symbol, use_cache=not should_force)
            print(f"   Registros: {len(data)}")
            print(f"   Período: {data.index[0]} a {data.index[-1]}")
            
            # 2. Preprocesar datos
            print("\n🔄 Preprocesando datos...")
            preprocessor = DataPreprocessor()
            X_train, X_test, y_train, y_test = preprocessor.prepare_data(data)
            
            # Guardar scaler para uso posterior
            preprocessor.save_scaler(symbol)
            
            # 3. Crear o cargar modelo
            print("\n🧠 Configurando modelo...")
            model = LSTMModel(n_features=X_train.shape[2])
            
            # Intentar cargar modelo existente para entrenamiento incremental
            try:
                model.load(symbol)
                
                # Verificar compatibilidad de shapes (por si cambiaron los features)
                current_features = X_train.shape[2]
                model_features = model.model.input_shape[-1]
                
                if current_features != model_features:
                    print(f"   ⚠️ Cambio en arquitectura detectado (Features: {model_features} -> {current_features})")
                    print(f"   ✨ Reconstruyendo modelo desde cero...")
                    model.n_features = current_features
                    model.build()
                else:
                    print(f"   🔄 Modelo existente cargado. Se continuará el entrenamiento (Fine-tuning).")
                    
            except Exception:
                print(f"   ✨ No se encontró modelo previo (o error al cargar). Creando uno nuevo desde cero.")
                model.build()
            
            # 4. Entrenar
            history = model.train(
                X_train, y_train,
                X_val=X_test, y_val=y_test,
                symbol=symbol,
                epochs=epochs
            )
            
            # 5. Evaluar
            print("\n📈 Evaluando modelo...")
            metrics = model.evaluate(X_test, y_test)
            
            # 6. Guardar modelo final
            model.save(symbol)
            
            # 7. Guardar métricas
            results = {
                "symbol": symbol,
                "name": ASSETS.get(symbol, {}).get("name", symbol),
                "trained_at": datetime.now().isoformat(),
                "epochs_completed": len(history["loss"]),
                "final_loss": history["loss"][-1],
                "final_val_loss": history["val_loss"][-1] if "val_loss" in history else None,
                "metrics": metrics,
                "data_points": len(data),
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "incremental": True  # Flag para indicar que fue incremental
            }
            
            self._save_training_results(symbol, results)
            self.training_results[symbol] = results
            
            print(f"\n✅ Entrenamiento de {symbol} completado exitosamente!")
            
            return results
            
        except Exception as e:
            error_result = {
                "symbol": symbol,
                "error": str(e),
                "trained_at": datetime.now().isoformat(),
                "success": False
            }
            print(f"\n❌ Error al entrenar {symbol}: {str(e)}")
            return error_result
    
    def train_all(
        self,
        epochs: int = None,
        force_download: bool = False
    ) -> Dict[str, Dict]:
        """
        Entrena modelos para todos los activos configurados.
        
        Args:
            epochs: Número de épocas
            force_download: Si forzar descarga de datos nuevos
            
        Returns:
            Diccionario con resultados de todos los entrenamientos
        """
        print("\n" + "="*60)
        print("🚀 INICIANDO ENTRENAMIENTO DE TODOS LOS ACTIVOS")
        print("="*60)
        print(f"\nActivos a entrenar: {list(ASSETS.keys())}")
        print(f"Total: {len(ASSETS)} modelos")
        
        all_results = {}
        successful = 0
        failed = 0
        
        for symbol in ASSETS.keys():
            result = self.train_symbol(symbol, epochs, force_download)
            all_results[symbol] = result
            
            if result.get("error"):
                failed += 1
            else:
                successful += 1
        
        # Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN DE ENTRENAMIENTO")
        print("="*60)
        print(f"\n✅ Exitosos: {successful}/{len(ASSETS)}")
        print(f"❌ Fallidos: {failed}/{len(ASSETS)}")
        
        if successful > 0:
            print("\n📈 Métricas por activo:")
            for symbol, result in all_results.items():
                if "metrics" in result:
                    metrics = result["metrics"]
                    print(f"   {symbol}: MAE={metrics['mae']:.4f}, "
                          f"RMSE={metrics['rmse']:.4f}, "
                          f"Dir.Acc={metrics['directional_accuracy']:.1%}")
        
        return all_results
    
    def _save_training_results(self, symbol: str, results: Dict) -> None:
        """
        Guarda los resultados del entrenamiento en un archivo JSON.
        
        Args:
            symbol: Símbolo del activo
            results: Resultados del entrenamiento
        """
        results_path = MODELS_DIR / f"{symbol}_results.json"
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✓ Resultados guardados en {results_path}")
    
    def get_training_status(self) -> Dict:
        """
        Obtiene el estado de entrenamiento de todos los modelos.
        
        Returns:
            Diccionario con estado de cada modelo
        """
        status = {}
        
        for symbol in ASSETS.keys():
            model_path = MODELS_DIR / f"{symbol}_model.keras"
            best_path = MODELS_DIR / f"{symbol}_best.keras"
            results_path = MODELS_DIR / f"{symbol}_results.json"
            
            status[symbol] = {
                "model_exists": model_path.exists() or best_path.exists(),
                "results_exist": results_path.exists()
            }
            
            if results_path.exists():
                with open(results_path, 'r') as f:
                    results = json.load(f)
                status[symbol]["last_trained"] = results.get("trained_at")
                status[symbol]["metrics"] = results.get("metrics")
        
        return status


def main():
    """Función principal para ejecutar desde línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Entrenamiento de modelos LSTM para predicción financiera"
    )
    parser.add_argument(
        "--symbol", "-s",
        type=str,
        help="Símbolo específico a entrenar (ej: VOO)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Entrenar todos los activos"
    )
    parser.add_argument(
        "--epochs", "-e",
        type=int,
        default=MODEL_CONFIG["epochs"],
        help=f"Número de épocas (default: {MODEL_CONFIG['epochs']})"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Forzar descarga de datos nuevos"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Mostrar estado de los modelos"
    )
    
    args = parser.parse_args()
    trainer = Trainer()
    
    if args.status:
        status = trainer.get_training_status()
        print("\n📊 Estado de los modelos:\n")
        for symbol, info in status.items():
            status_icon = "✅" if info["model_exists"] else "❌"
            print(f"{status_icon} {symbol}: ", end="")
            if info["model_exists"]:
                print(f"Último entrenamiento: {info.get('last_trained', 'N/A')}")
            else:
                print("No entrenado")
        return
    
    if args.symbol:
        if args.symbol not in ASSETS:
            print(f"❌ Símbolo '{args.symbol}' no encontrado.")
            print(f"   Símbolos disponibles: {list(ASSETS.keys())}")
            return
        trainer.train_symbol(args.symbol, args.epochs, args.force)
        
    elif args.all:
        trainer.train_all(args.epochs, args.force)
        
    else:
        print("⚠️  Especifica --symbol SÍMBOLO o --all para entrenar")
        print("   Usa --help para ver todas las opciones")


if __name__ == "__main__":
    main()
