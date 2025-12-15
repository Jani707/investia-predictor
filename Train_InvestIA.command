#!/bin/bash
# InvestIA Training Script
# This script runs the model training process.

PROJECT_DIR="/Users/Macbookpro/Documents/Antigravity/Plataforma_Inversion_ML"

echo "=================================================="
echo "   🧠 InvestIA Predictor - Model Training"
echo "=================================================="
echo "Project Directory: $PROJECT_DIR"
echo ""

# 1. Setup Environment
cd "$PROJECT_DIR"
source venv/bin/activate
cd backend

# 2. Run Training
echo "Starting Model Training..."
echo "This process may take 20-30 minutes."
echo "--------------------------------------------------"
python train.py --all

echo ""
echo "✅ Training Complete!"
echo "You can close this window now."
read -p "Press Enter to exit..."
