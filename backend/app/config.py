"""
Configuración del Predictor de Inversiones
"""
import os
from pathlib import Path

# Directorios base
BASE_DIR = Path(__file__).resolve().parent.parent
ML_DIR = BASE_DIR / "ml"
MODELS_DIR = BASE_DIR / "saved_models"
DATA_DIR = BASE_DIR / "data"

# Crear directorios si no existen
MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Activos de bajo riesgo para principiantes
ASSETS = {
    "VOO": {
        "name": "Vanguard S&P 500 ETF",
        "type": "ETF",
        "risk": "low",
        "description": "Sigue el índice S&P 500. Ideal para crecimiento a largo plazo con riesgo moderado.",
        "recent_earnings": "YTD Return: +24.5% | Yield: 1.45%",
        "investment_thesis": "Exposición core a las 500 empresas más grandes de EE.UU. Diversificación instantánea y bajo costo."
    },
    "VTI": {
        "name": "Vanguard Total Stock Market ETF",
        "type": "ETF", 
        "risk": "low",
        "description": "Exposición a todo el mercado de acciones de EE.UU. Máxima diversificación.",
        "recent_earnings": "YTD Return: +23.8% | Yield: 1.38%",
        "investment_thesis": "Captura el crecimiento de todo el mercado americano, incluyendo small y mid-caps."
    },
    "BND": {
        "name": "Vanguard Total Bond Market ETF",
        "type": "ETF",
        "risk": "very_low",
        "description": "Bonos de grado de inversión. Estabilidad y preservación de capital.",
        "recent_earnings": "YTD Return: +2.1% | Yield: 3.25%",
        "investment_thesis": "Estabilidad y generación de ingresos. Cobertura contra volatilidad del mercado accionario."
    },
    "SCHD": {
        "name": "Schwab US Dividend Equity ETF",
        "type": "ETF",
        "risk": "low",
        "description": "Empresas de alta calidad con historial de pago de dividendos crecientes.",
        "recent_earnings": "YTD Return: +14.2% | Yield: 3.45%",
        "investment_thesis": "Ingresos pasivos crecientes y menor volatilidad que el mercado general."
    },
    "VNQ": {
        "name": "Vanguard Real Estate ETF",
        "type": "ETF",
        "risk": "medium_low",
        "description": "Inversión en bienes raíces (REITs). Generación de ingresos y diversificación.",
        "recent_earnings": "YTD Return: +8.5% | Yield: 3.95%",
        "investment_thesis": "Exposición al sector inmobiliario sin necesidad de comprar propiedades físicas. Alta rentabilidad por dividendos."
    },
    "GLD": {
        "name": "SPDR Gold Shares",
        "type": "ETF",
        "risk": "low",
        "description": "Oro físico. Actúa como refugio seguro contra la inflación y volatilidad.",
        "recent_earnings": "YTD Return: +28.4% | Yield: 0.0%",
        "investment_thesis": "Protección contra incertidumbre geopolítica y devaluación monetaria. Descorrelación con acciones."
    },
    # Riesgo Medio
    "QQQ": {
        "name": "Invesco QQQ Trust",
        "type": "ETF",
        "risk": "medium",
        "description": "Sigue el Nasdaq-100. Enfoque en tecnología y crecimiento.",
        "recent_earnings": "YTD Return: +26.8% | Yield: 0.60%",
        "investment_thesis": "Concentración en las empresas tecnológicas más innovadoras y de mayor crecimiento."
    },
    "VIG": {
        "name": "Vanguard Dividend Appreciation",
        "type": "ETF",
        "risk": "medium",
        "description": "Empresas que aumentan sus dividendos año tras año. Calidad y crecimiento.",
        "recent_earnings": "YTD Return: +18.5% | Yield: 1.85%",
        "investment_thesis": "Calidad y crecimiento de dividendos. Empresas financieramente sólidas y disciplinadas."
    },
    "IWM": {
        "name": "iShares Russell 2000 ETF",
        "type": "ETF",
        "risk": "medium",
        "description": "Pequeñas empresas de EE.UU. Mayor potencial de crecimiento y volatilidad.",
        "recent_earnings": "YTD Return: +16.2% | Yield: 1.25%",
        "investment_thesis": "Potencial de alto crecimiento en empresas pequeñas. Beneficiario de bajadas de tasas de interés."
    },
    # Riesgo Alto
    "ARKK": {
        "name": "ARK Innovation ETF",
        "type": "ETF",
        "risk": "high",
        "description": "Innovación disruptiva (IA, genómica, fintech). Alto riesgo, alto potencial.",
        "recent_earnings": "YTD Return: +5.4% | Yield: 0.0%",
        "investment_thesis": "Apuesta agresiva por tecnologías futuras disruptivas. Alto potencial de revalorización a largo plazo."
    },
    "SOXL": {
        "name": "Direxion Daily Semiconductor Bull 3X",
        "type": "ETF",
        "risk": "high",
        "description": "Apalancado 3x en semiconductores. Extremadamente volátil, para trading corto plazo.",
        "recent_earnings": "YTD Return: +45.2% | Yield: 0.45%",
        "investment_thesis": "Instrumento táctico para aprovechar el superciclo de semiconductores e IA con apalancamiento."
    },
    "TQQQ": {
        "name": "ProShares UltraPro QQQ",
        "type": "ETF",
        "risk": "high",
        "description": "Apalancado 3x en Nasdaq-100. Solo para traders experimentados.",
        "recent_earnings": "YTD Return: +65.8% | Yield: 0.85%",
        "investment_thesis": "Máxima exposición al sector tecnológico. Para estrategias agresivas de corto plazo."
    },
    # Empresas - Riesgo Bajo
    "JNJ": {
        "name": "Johnson & Johnson",
        "type": "Stock",
        "risk": "low",
        "description": "Gigante farmacéutico y de consumo. Dividendos muy estables.",
        "recent_earnings": "Q3 '24: EPS $2.66 (+4.3% YoY) | Rev $21.4B (+6.8%)",
        "investment_thesis": "Refugio seguro en volatilidad. 60+ años incrementando dividendos. Pipeline farmacéutico sólido."
    },
    "KO": {
        "name": "Coca-Cola Company",
        "type": "Stock",
        "risk": "low",
        "description": "Líder mundial en bebidas. Flujo de caja predecible.",
        "recent_earnings": "Q3 '24: EPS $0.74 (+7% YoY) | Rev $11.9B (+8%)",
        "investment_thesis": "Marca global dominante con poder de fijación de precios. Excelente protección contra inflación."
    },
    "PG": {
        "name": "Procter & Gamble",
        "type": "Stock",
        "risk": "low",
        "description": "Bienes de consumo básico. Resiliente en recesiones.",
        "recent_earnings": "Q1 '25: EPS $1.83 (+17% YoY) | Rev $21.9B (+6%)",
        "investment_thesis": "Demanda inelástica de productos esenciales. Eficiencia operativa y retorno de capital a accionistas."
    },
    # Empresas - Riesgo Medio
    "AAPL": {
        "name": "Apple Inc.",
        "type": "Stock",
        "risk": "medium",
        "description": "Tecnología de consumo y servicios. Crecimiento sólido y recompra de acciones.",
        "recent_earnings": "Q4 '24: EPS $1.46 (+13% YoY) | Rev $89.5B (-1%)",
        "investment_thesis": "Ecosistema cerrado con alta retención. Crecimiento en Servicios y wearables. Fuerte recompra de acciones."
    },
    "MSFT": {
        "name": "Microsoft Corp.",
        "type": "Stock",
        "risk": "medium",
        "description": "Software, nube (Azure) e IA. Posición dominante en el mercado.",
        "recent_earnings": "Q1 '25: EPS $2.99 (+27% YoY) | Rev $56.5B (+13%)",
        "investment_thesis": "Liderazgo indiscutible en IA (OpenAI) y Cloud (Azure). Ingresos recurrentes masivos por Office 365."
    },
    "GOOGL": {
        "name": "Alphabet Inc.",
        "type": "Stock",
        "risk": "medium",
        "description": "Líder en búsquedas y publicidad digital. Inversión fuerte en IA.",
        "recent_earnings": "Q3 '24: EPS $1.55 (+46% YoY) | Rev $76.7B (+11%)",
        "investment_thesis": "Monopolio en búsquedas y YouTube. Valoración atractiva vs pares. Inversión agresiva en Gemini AI."
    },
    # Empresas - Riesgo Alto
    "TSLA": {
        "name": "Tesla Inc.",
        "type": "Stock",
        "risk": "high",
        "description": "Vehículos eléctricos y energía. Muy volátil pero con alto potencial.",
        "recent_earnings": "Q3 '24: EPS $0.66 (-37% YoY) | Rev $23.4B (+9%)",
        "investment_thesis": "Líder en EVs y conducción autónoma (FSD). Potencial disruptivo en robótica (Optimus) y energía."
    },
    "NVDA": {
        "name": "NVIDIA Corp.",
        "type": "Stock",
        "risk": "high",
        "description": "Líder en chips para IA y gaming. Crecimiento explosivo pero valoración alta.",
        "recent_earnings": "Q3 '24: EPS $4.02 (+593% YoY) | Rev $18.1B (+206%)",
        "investment_thesis": "Estándar de facto para entrenamiento de IA. Demanda insaciable de GPUs H100/H200. Márgenes récord."
    },
    "AMD": {
        "name": "Advanced Micro Devices",
        "type": "Stock",
        "risk": "high",
        "description": "Semiconductores para PCs y servidores. Competidor fuerte de Intel y NVIDIA.",
        "recent_earnings": "Q3 '24: EPS $0.70 (+4% YoY) | Rev $5.8B (+4%)",
        "investment_thesis": "Principal alternativa a NVIDIA en IA (MI300). Ganando cuota de mercado en servidores a Intel."
    }
}

# Configuración del modelo LSTM
MODEL_CONFIG = {
    "sequence_length": 60,      # Días de historial para predicción
    "prediction_days": 5,       # Días a predecir
    "lstm_units": 50,           # Unidades en capa LSTM
    "dropout_rate": 0.2,        # Tasa de dropout
    "epochs": 100,              # Épocas de entrenamiento
    "batch_size": 32,           # Tamaño del batch
    "validation_split": 0.2,    # Porcentaje para validación
    "early_stopping_patience": 10  # Paciencia para early stopping
}

# Configuración de datos
DATA_CONFIG = {
    "history_period": "2y",     # 2 años de datos históricos
    "interval": "1d",           # Intervalo diario
    "features": ["Open", "High", "Low", "Close", "Volume"],
    "target": "Close"
}

# Configuración de la API
API_CONFIG = {
    "title": "InvestIA Predictor API",
    "description": "API de predicción de inversiones de bajo riesgo con LSTM",
    "version": "1.0.0",
    "host": "0.0.0.0",
    "port": 8000
}

# Configuración de Email
EMAIL_CONFIG = {
    "sender": os.getenv("EMAIL_SENDER", "sf.alfaro10@gmail.com"),
    "password": os.getenv("EMAIL_PASSWORD", "ytkp nfaz slfg jodg"),  # App Password
    "recipient": os.getenv("EMAIL_RECIPIENT", "sf.alfaro10@gmail.com"),
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465
}

# Configuración de Telegram
TELEGRAM_CONFIG = {
    "bot_token": os.getenv("TELEGRAM_TOKEN", ""),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", "")
}

# Configuración de Análisis de Oportunidades
ANALYSIS_CONFIG = {
    "rsi_threshold_low": 30,      # Nivel de sobreventa
    "price_drop_threshold": 0.05, # 5% de caída reciente
    "volatility_threshold": 0.03  # 3% de volatilidad diaria (proxy de inestabilidad)
}
