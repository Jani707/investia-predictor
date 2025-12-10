/**
 * InvestIA Predictor - API Client
 * Maneja todas las comunicaciones con el backend FastAPI
 */

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000/api'
    : 'https://investia-backend.onrender.com/api'; // URL por defecto en Render (ajustar si cambia el nombre)

class APIClient {
    constructor(baseUrl = API_BASE_URL) {
        this.baseUrl = baseUrl;
        this.isConnected = false;
    }

    /**
     * Realiza una petición GET a la API
     */
    async get(endpoint) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * Verifica la conexión con el servidor
     */
    async checkConnection() {
        try {
            const response = await fetch(`${this.baseUrl.replace('/api', '')}/health`);
            this.isConnected = response.ok;
            return this.isConnected;
        } catch (error) {
            this.isConnected = false;
            return false;
        }
    }

    // ==========================================
    // Endpoints de Predicciones
    // ==========================================

    /**
     * Obtiene predicciones de todos los activos
     */
    async getAllPredictions() {
        return this.get('/predict/all');
    }

    /**
     * Obtiene predicción de un activo específico
     */
    async getPrediction(symbol) {
        return this.get(`/predict/${symbol}`);
    }

    /**
     * Obtiene resumen de predicción
     */
    async getPredictionSummary(symbol) {
        return this.get(`/predict/${symbol}/summary`);
    }

    // ==========================================
    // Endpoints de Datos Históricos
    // ==========================================

    /**
     * Obtiene datos históricos
     */
    async getHistorical(symbol, days = 30) {
        return this.get(`/historical/${symbol}?days=${days}`);
    }

    /**
     * Obtiene datos formateados para gráficos
     */
    async getChartData(symbol, days = 60) {
        return this.get(`/historical/${symbol}/chart?days=${days}`);
    }

    /**
     * Obtiene el precio más reciente
     */
    async getLatestPrice(symbol) {
        return this.get(`/historical/${symbol}/latest`);
    }

    // ==========================================
    // Endpoints de Métricas
    // ==========================================

    /**
     * Obtiene métricas de todos los modelos
     */
    async getAllMetrics() {
        return this.get('/metrics/all');
    }

    /**
     * Obtiene métricas de un modelo específico
     */
    async getMetrics(symbol) {
        return this.get(`/metrics/${symbol}`);
    }

    /**
     * Obtiene estado de entrenamiento
     */
    async getTrainingStatus() {
        return this.get('/metrics/status');
    }

    // ==========================================
    // Endpoints de Activos
    // ==========================================

    /**
     * Obtiene todos los activos
     */
    async getAssets() {
        return this.get('/assets');
    }

    /**
     * Obtiene información de un activo
     */
    async getAssetInfo(symbol) {
        return this.get(`/assets/${symbol}`);
    }

    /**
     * Filtra activos por nivel de riesgo
     */
    async getAssetsByRisk(level) {
        return this.get(`/assets/risk/${level}`);
    }

    // ==========================================
    // Endpoints de Portafolio
    // ==========================================

    /**
     * Genera una propuesta de portafolio
     */
    async generatePortfolio(riskProfile, amount) {
        try {
            const response = await fetch(`${this.baseUrl}/portfolio/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    risk_profile: riskProfile,
                    amount: parseFloat(amount)
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error [generatePortfolio]:', error);
            throw error;
        }
    }
}

// Instancia global
const api = new APIClient();
