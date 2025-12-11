"""
InvestIA Predictor - FastAPI Application
API principal para servir predicciones de inversión.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import sys
from pathlib import Path
from app.services.telegram_service import TelegramService
# from app.services.email_service import EmailService  <-- Replaced by Telegram
from app.services.analysis_service import AnalysisService

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import API_CONFIG, ASSETS
from app.routers import predictions, historical, metrics, assets, portfolio


async def run_market_analysis_loop():
    """Ejecuta el análisis de mercado periódicamente."""
    while True:
        try:
            print("\n⏰ Starting scheduled market analysis...")
            opportunities = AnalysisService.analyze_market()
            
            if opportunities:
                print(f"✨ Found {len(opportunities)} opportunities!")
                body = "🚀 *Oportunidades de Inversión Detectadas:*\n\n"
                for opp in opportunities:
                    body += f"🔹 *{opp['name']}* ({opp['symbol']})\n"
                    body += f"   💵 Precio: ${opp['price']:.2f}\n"
                    body += f"   📊 Razones: {', '.join(opp['reasons'])}\n\n"
                
                body += "_Recuerda: Esto es una sugerencia basada en algoritmos. Haz tu propia investigación._"
                
                # Enviar por Telegram
                success, msg = TelegramService.send_message(body)
                if not success:
                    print(f"⚠️ Failed to send Telegram notification: {msg}")
            else:
                print("😴 No opportunities found this time.")
                
        except Exception as e:
            print(f"❌ Error in market analysis loop: {e}")
            
        # Esperar 4 horas (14400 segundos) antes del siguiente análisis
        # Para pruebas, se puede reducir este tiempo
        await asyncio.sleep(14400)


# Inicialización de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    print("\n🚀 InvestIA Predictor API iniciando...")
    print(f"   Activos configurados: {list(ASSETS.keys())}")
    
    # Iniciar tarea en segundo plano
    asyncio.create_task(run_market_analysis_loop())
    
    yield
    print("\n👋 InvestIA Predictor API cerrando...")


app = FastAPI(
    title=API_CONFIG["title"],
    description=API_CONFIG["description"],
    version=API_CONFIG["version"],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para desarrollo local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(predictions.router, prefix="/api", tags=["Predicciones"])
app.include_router(historical.router, prefix="/api", tags=["Datos Históricos"])
app.include_router(metrics.router, prefix="/api", tags=["Métricas"])
app.include_router(assets.router, prefix="/api", tags=["Activos"])
app.include_router(portfolio.router, prefix="/api", tags=["Portafolio"])


@app.get("/api/info", tags=["General"])
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "name": API_CONFIG["title"],
        "version": API_CONFIG["version"],
        "description": API_CONFIG["description"],
        "endpoints": {
            "docs": "/docs",
            "predictions": "/api/predict/{symbol}",
            "all_predictions": "/api/predict/all",
            "historical": "/api/historical/{symbol}",
            "metrics": "/api/metrics/{symbol}",
            "assets": "/api/assets"
        },
        "status": "running"
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "investia-predictor"
    }


@app.get("/api/test-telegram", tags=["General"])
async def test_telegram():
    """
    Endpoint de prueba para forzar el envío de un mensaje a Telegram.
    """
    try:
        success, message = TelegramService.send_message(
            "🔔 *Test InvestIA*\n\nSi lees esto, ¡tu bot de Telegram está conectado correctamente! 🚀"
        )
        
        if success:
            return {"status": "success", "message": "Mensaje de prueba enviado a Telegram"}
        else:
            # Devolver el error específico que nos dio el servicio
            raise HTTPException(status_code=500, detail=f"Fallo Telegram: {message}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@app.post("/api/trigger-analysis", tags=["General"])
async def trigger_analysis():
    """
    Endpoint para despertar al servidor y ejecutar el análisis.
    Útil para Cron Jobs externos (ej: cron-job.org) en servidores gratuitos.
    """
    try:
        print("\n🔔 Trigger manual/externo de análisis recibido.")
        opportunities = AnalysisService.analyze_market()
        
        if opportunities:
            body = "🚀 *Oportunidades de Inversión Detectadas (Trigger Externo):*\n\n"
            for opp in opportunities:
                body += f"🔹 *{opp['name']}* ({opp['symbol']})\n"
                body += f"   💵 Precio: ${opp['price']:.2f}\n"
                body += f"   📊 Razones: {', '.join(opp['reasons'])}\n\n"
            
            body += "_Recuerda: Esto es una sugerencia basada en algoritmos. Haz tu propia investigación._"
            
            TelegramService.send_message(body)
            return {"status": "success", "message": f"Análisis completado. {len(opportunities)} oportunidades encontradas y enviadas."}
        
        return {"status": "success", "message": "Análisis completado. No se encontraron oportunidades."}
            
    except Exception as e:
        print(f"❌ Error en trigger analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug-network", tags=["General"])
async def debug_network():
    """
    Prueba conectividad de red (DNS y Puertos) para depurar errores en Render.
    """
    results = {}
    
    # 1. DNS Resolution
    try:
        import socket
        ip = socket.gethostbyname("smtp.gmail.com")
        results["dns_gmail"] = f"OK ({ip})"
    except Exception as e:
        results["dns_gmail"] = f"FAIL: {e}"
        
    # 2. Port Connectivity
    ports = [587, 465, 443]
    for port in ports:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('smtp.gmail.com', port))
            if result == 0:
                results[f"port_{port}"] = "OPEN"
            else:
                results[f"port_{port}"] = f"CLOSED (Code {result})"
            sock.close()
        except Exception as e:
            results[f"port_{port}"] = f"ERROR: {e}"
            
    return results


# --- BACKTEST ENDPOINT ---
from app.services.backtest_service import BacktestService

@app.post("/api/backtest", tags=["General"])
async def run_backtest(request: dict):
    """
    Ejecuta una simulación de backtesting.
    Body: { "symbol": "VOO", "days": 365 }
    """
    try:
        symbol = request.get("symbol", "VOO")
        days = int(request.get("days", 365))
        
        result = BacktestService.run_backtest(symbol, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- WATCHLIST ENDPOINTS ---
from app.services.watchlist_service import WatchlistService

@app.get("/api/watchlist", tags=["Watchlist"])
async def get_watchlist():
    return {"watchlist": WatchlistService.get_watchlist()}

@app.post("/api/watchlist/add", tags=["Watchlist"])
async def add_to_watchlist(request: dict):
    symbol = request.get("symbol")
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    return WatchlistService.add_symbol(symbol)

@app.post("/api/watchlist/remove", tags=["Watchlist"])
async def remove_from_watchlist(request: dict):
    symbol = request.get("symbol")
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    return WatchlistService.remove_symbol(symbol)


# Manejo de errores global
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Error interno del servidor",
            "detail": str(exc)
        }
    )

# --- DEBUG YFINANCE ---
@app.get("/api/debug-yfinance", tags=["General"])
async def debug_yfinance():
    """Prueba la conexión con Yahoo Finance."""
    try:
        import yfinance as yf
        ticker = yf.Ticker("VOO")
        hist = ticker.history(period="1d")
        if hist.empty:
            return {"status": "error", "message": "No data received from Yahoo Finance"}
        return {
            "status": "success", 
            "last_price": float(hist["Close"].iloc[-1]),
            "symbol": "VOO"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- STATIC FILES (FRONTEND) ---
from fastapi.staticfiles import StaticFiles
import os

# Determinar ruta absoluta al frontend
# Estamos en backend/app/main.py -> parent.parent es backend -> parent.parent.parent es root -> + frontend
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"

if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
else:
    print(f"⚠️ Frontend directory not found at {frontend_path}")
