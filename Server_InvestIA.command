#!/bin/bash
# InvestIA Server Script
# This script runs the Backend + Frontend server and opens the browser.

PROJECT_DIR="/Users/Macbookpro/Documents/Antigravity/Plataforma_Inversion_ML"

echo "=================================================="
echo "   🚀 InvestIA Predictor - Server & App"
echo "=================================================="
echo "Project Directory: $PROJECT_DIR"
echo ""

# 1. Setup Environment
cd "$PROJECT_DIR"
source venv/bin/activate
cd backend

# 2. Open Browser (Scheduled)
# We wait 8 seconds to ensure server is fully up
(sleep 8 && open "http://localhost:8000") &

# 3. Start Backend
echo "Starting System..."
echo "The browser should open automatically in a few seconds."
echo "--------------------------------------------------"
uvicorn app.main:app --reload --port 8000
