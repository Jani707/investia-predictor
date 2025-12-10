#!/bin/bash

# ============================================
# InvestIA Predictor - Launcher Script
# ============================================

echo "🚀 InvestIA Predictor - Iniciando..."
echo "============================================"

# Directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

# Verificar si el entorno virtual existe
VENV_DIR="$PROJECT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source "$VENV_DIR/bin/activate"

# Instalar dependencias si es necesario
if [ ! -f "$VENV_DIR/.installed" ]; then
    echo "📥 Instalando dependencias..."
    pip install -r "$BACKEND_DIR/requirements.txt"
    touch "$VENV_DIR/.installed"
fi

# Verificar si hay modelos entrenados
MODELS_DIR="$BACKEND_DIR/saved_models"
if [ ! -d "$MODELS_DIR" ] || [ -z "$(ls -A $MODELS_DIR 2>/dev/null)" ]; then
    echo ""
    echo "⚠️  No se encontraron modelos entrenados."
    echo "   Para entrenar los modelos, ejecuta:"
    echo "   cd backend && python train.py --all"
    echo ""
fi

# Iniciar el servidor FastAPI
echo ""
echo "🌐 Iniciando servidor API en http://localhost:8000"
echo "📊 Documentación disponible en http://localhost:8000/docs"
echo ""
echo "Para detener el servidor, presiona Ctrl+C"
echo "============================================"
echo ""

cd "$BACKEND_DIR"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
