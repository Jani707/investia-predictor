import sys
import os
from pathlib import Path
import asyncio

# Add backend directory to path
sys.path.append(str(Path(__file__).resolve().parent))

from app.routers.portfolio import generate_portfolio, PortfolioRequest
from app.services.backtest_service import BacktestService
from ml.predictor import Predictor

async def test_portfolio():
    print("\n--- Testing Portfolio Generation ---")
    try:
        request = PortfolioRequest(risk_profile="medium", amount=10000)
        print(f"Requesting portfolio for: {request}")
        result = await generate_portfolio(request)
        print("✅ Portfolio generated successfully!")
        print(f"Allocation count: {len(result['allocation'])}")
    except Exception as e:
        print(f"❌ Portfolio Generation Failed: {e}")
        import traceback
        traceback.print_exc()

def test_backtest():
    print("\n--- Testing Backtest ---")
    try:
        symbol = "VOO"
        days = 365
        print(f"Running backtest for {symbol} ({days} days)...")
        result = BacktestService.run_backtest(symbol, days)
        if "error" in result:
             print(f"❌ Backtest returned error: {result['error']}")
        else:
            print(f"✅ Backtest successful! Return: {result['return_pct']:.2f}%")
    except Exception as e:
        print(f"❌ Backtest Failed: {e}")
        import traceback
        traceback.print_exc()

def test_predictor():
    print("\n--- Testing Predictor ---")
    try:
        predictor = Predictor()
        symbol = "VOO"
        print(f"Predicting for {symbol}...")
        result = predictor.predict(symbol)
        print(f"Prediction result success: {result.get('success')}")
        if not result.get('success'):
            print(f"Error: {result.get('error')}")
    except Exception as e:
        print(f"❌ Predictor Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run sync tests
    test_predictor()
    test_backtest()
    
    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_portfolio())
    loop.close()
