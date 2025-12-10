import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.email_service import EmailService
from app.services.analysis_service import AnalysisService
from app.config import EMAIL_CONFIG

def test_email_service():
    print("\n📧 Testing EmailService...")
    
    # Mock smtplib to avoid actual sending if credentials are missing
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Test with dummy credentials if not set
        original_password = EMAIL_CONFIG["password"]
        if not original_password:
            EMAIL_CONFIG["password"] = "dummy_password"
            
        success = EmailService.send_email("Test Subject", "Test Body")
        
        if success:
            print("✅ EmailService.send_email() returned True")
            mock_server.sendmail.assert_called()
            print("✅ SMTP sendmail called successfully (Mocked)")
        else:
            print("❌ EmailService.send_email() returned False")
            
        # Restore config
        EMAIL_CONFIG["password"] = original_password

def test_analysis_service():
    print("\n🔍 Testing AnalysisService...")
    
    # Mock yfinance to return data that triggers an opportunity
    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = MagicMock()
        mock_ticker.return_value = mock_instance
        
        # Create a mock DataFrame with low RSI and price drop
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(start="2024-01-01", periods=100)
        data = {
            "Open": np.random.rand(100) * 100,
            "High": np.random.rand(100) * 110,
            "Low": np.random.rand(100) * 90,
            "Close": np.linspace(100, 50, 100), # Price dropping
            "Volume": np.random.randint(1000, 10000, 100)
        }
        df = pd.DataFrame(data, index=dates)
        mock_instance.history.return_value = df
        
        # Run analysis
        opportunities = AnalysisService.analyze_market()
        
        if opportunities:
            print(f"✅ Found {len(opportunities)} opportunities (Mocked Data)")
            for opp in opportunities:
                print(f"   - {opp['symbol']}: {opp['reasons']}")
        else:
            print("❌ No opportunities found (Check thresholds or mock data)")

if __name__ == "__main__":
    test_email_service()
    test_analysis_service()
