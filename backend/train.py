#!/usr/bin/env python3
"""
Script principal de entrenamiento.
Ejecutar desde la carpeta backend:
    python train.py --all
    python train.py --symbol VOO
"""
import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ml.trainer import main

if __name__ == "__main__":
    main()
