
import sys
from pathlib import Path
import pickle
import os

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from app.config import DATA_DIR
    
    symbol = "VOO"
    scaler_path = DATA_DIR / f"{symbol}_scaler.pkl"
    
    print(f"Attempting to load scaler from {scaler_path}...")
    
    if not scaler_path.exists():
        print("❌ Scaler file does not exist!")
        sys.exit(1)
        
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
        
    print("✅ Success! Scaler loaded.")
    print(f"Scaler type: {type(scaler)}")
    
except Exception as e:
    print(f"❌ Critical Error: {e}")
    import traceback
    traceback.print_exc()
