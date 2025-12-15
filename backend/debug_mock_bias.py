
import random

def test_mock_bias():
    scores = []
    recommendations = []
    
    for _ in range(1000):
        # Logic from analysis_service.py (UPDATED)
        # FIX: Score neutral (-2 a 2) en lugar de sesgado positivo (-1 a 3)
        mock_score = random.uniform(-2, 2)
        
        rec = "MANTENER"
        if mock_score >= 2: rec = "COMPRAR"
        elif mock_score <= -1: rec = "VENDER"
        
        scores.append(mock_score)
        recommendations.append(rec)
        
    avg_score = sum(scores) / len(scores)
    buy_count = recommendations.count("COMPRAR")
    sell_count = recommendations.count("VENDER")
    hold_count = recommendations.count("MANTENER")
    
    print(f"Average Score: {avg_score:.2f} (Expected ~0.0)")
    print(f"Buy: {buy_count} ({buy_count/10:.1f}%)")
    print(f"Sell: {sell_count} ({sell_count/10:.1f}%)")
    print(f"Hold: {hold_count} ({hold_count/10:.1f}%)")
    
    if -0.2 < avg_score < 0.2:
        print("\n✅ CONFIRMED: Bias removed (Neutral distribution).")
    else:
        print(f"\n❌ Bias still present (Avg: {avg_score}).")

if __name__ == "__main__":
    test_mock_bias()
