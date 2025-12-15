#!/bin/bash
# InvestIA Ultimate Launcher
# This script guarantees TWO separate Terminal windows:
# 1. Training Window
# 2. Server Window (Backend + Frontend)

PROJECT_DIR="/Users/Macbookpro/Documents/Antigravity/Plataforma_Inversion_ML"

echo "=================================================="
echo "   🚀 InvestIA Predictor - Start System"
echo "=================================================="
echo "Launching components in separate windows..."

# 1. Launch Training in Window #1
echo "1. Launching Model Training..."
open -a Terminal "$PROJECT_DIR/Train_InvestIA.command"

# 2. Launch Server in Window #2
echo "2. Launching Server & App..."
open -a Terminal "$PROJECT_DIR/Server_InvestIA.command"

echo ""
echo "✅ Done! Two new Terminal windows have been opened."
echo "   - Window 1: Model Training"
echo "   - Window 2: Server & App"
echo ""
echo "You can close this launcher window now."
exit
