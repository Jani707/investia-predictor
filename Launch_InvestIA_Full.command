#!/bin/bash
# InvestIA Full Launcher
# This script runs Training + Backend + Frontend (Unified)

PROJECT_DIR="/Users/Macbookpro/Documents/Antigravity/Plataforma_Inversion_ML"

echo "=================================================="
echo "   🚀 InvestIA Predictor - Full Launcher"
echo "=================================================="
echo "Project Directory: $PROJECT_DIR"
echo ""

# 1. Setup Environment
cd "$PROJECT_DIR"
source venv/bin/activate
cd backend

# 2. Run Training
echo "1. Starting Model Training..."
echo "   (This process takes 20-30 minutes. Please wait.)"
echo "--------------------------------------------------"
python train.py --all

# 3. Open Browser (Scheduled)
# We use a background process to open the browser after a few seconds
(sleep 5 && open "http://localhost:8000") &

# 4. Start Backend (which serves Frontend too)
echo "--------------------------------------------------"
echo "2. Training Complete!"
echo "3. Starting System (Backend + Frontend)..."
echo "   The browser should open automatically."
echo "   (Press Ctrl+C to stop)"
echo "--------------------------------------------------"
uvicorn app.main:app --reload --port 8000
