
import sys
from pathlib import Path
import os

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from ml.predictor import Predictor
    
    print("Attempting to load VOO model...")
    predictor = Predictor()
    success = predictor.load_model("VOO")
    
    if success:
        print("✅ Success! Model loaded.")
        print(f"Input shape: {predictor.models['VOO'].model.input_shape}")
    else:
        print("❌ Failed to load model.")
        
except Exception as e:
    print(f"❌ Critical Error: {e}")
    import traceback
    traceback.print_exc()
