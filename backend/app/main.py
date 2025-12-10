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
from app.services.email_service import EmailService
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
                body = "🚀 Oportunidades de Inversión Detectadas:\n\n"
                for opp in opportunities:
                    body += f"🔹 {opp['name']} ({opp['symbol']})\n"
                    body += f"   Precio: ${opp['price']:.2f}\n"
                    body += f"   Razones: {', '.join(opp['reasons'])}\n\n"
                
                body += "Recuerda: Esto es una sugerencia basada en algoritmos. Haz tu propia investigación."
                
                EmailService.send_email("InvestIA - Oportunidad de Compra Detectada", body)
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


@app.get("/", tags=["General"])
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


@app.get("/api/test-email", tags=["General"])
async def test_email():
    """
    Endpoint de prueba para forzar el envío de un correo.
    Útil para verificar la configuración SMTP.
    """
    try:
        success = EmailService.send_email(
            subject="🔔 Test InvestIA - Verificación de Sistema",
            body="Este es un correo de prueba solicitado manualmente para verificar que el sistema de notificaciones está funcionando correctamente.\n\nSi lees esto, ¡todo está bien configurado! 🚀"
        )
        
        if success:
            return {"status": "success", "message": "Correo de prueba enviado correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Fallo al enviar el correo. Revisa los logs del servidor.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            # Reutilizamos la lógica de envío (podríamos refactorizar, pero por ahora duplicamos para simplicidad)
            body = "🚀 Oportunidades de Inversión Detectadas (Trigger Externo):\n\n"
            for opp in opportunities:
                body += f"🔹 {opp['name']} ({opp['symbol']})\n"
                body += f"   Precio: ${opp['price']:.2f}\n"
                body += f"   Razones: {', '.join(opp['reasons'])}\n\n"
            
            body += "Recuerda: Esto es una sugerencia basada en algoritmos. Haz tu propia investigación."
            
            EmailService.send_email("InvestIA - Oportunidad Detectada (Auto)", body)
            return {"status": "success", "message": f"Análisis completado. {len(opportunities)} oportunidades encontradas y enviadas."}
        
        return {"status": "success", "message": "Análisis completado. No se encontraron oportunidades."}
            
    except Exception as e:
        print(f"❌ Error en trigger analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug-network", tags=["General"])
async def debug_network():
    """
    Endpoint de depuración para probar conectividad de red.
    """
    import socket
    results = {}
    
    # Test DNS resolution
    try:
        ip = socket.gethostbyname("smtp.gmail.com")
        results["dns_resolution"] = f"Success: {ip}"
    except Exception as e:
        results["dns_resolution"] = f"Failed: {e}"
        
    # Test Port 587
    try:
        sock = socket.create_connection(("smtp.gmail.com", 587), timeout=5)
        sock.close()
        results["port_587"] = "Open"
    except Exception as e:
        results["port_587"] = f"Closed/Blocked: {e}"
        
    # Test Port 465
    try:
        sock = socket.create_connection(("smtp.gmail.com", 465), timeout=5)
        sock.close()
        results["port_465"] = "Open"
    except Exception as e:
        results["port_465"] = f"Closed/Blocked: {e}"
        
    return results


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
