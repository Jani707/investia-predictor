/**
 * InvestIA Predictor - Main Application
 * Coordina la lógica principal del dashboard
 */

class App {
    constructor() {
        this.predictions = [];
        this.assets = [];
        this.currentSymbol = 'VOO';
        this.currentPeriod = 30;
        this.refreshInterval = null;
        this.isLoading = false;
    }

    /**
     * Inicializa la aplicación
     */
    async init() {
        console.log('🚀 InvestIA Predictor iniciando...');

        // Configurar event listeners
        this.setupEventListeners();

        // Verificar conexión con el servidor
        await this.checkAPIConnection();

        // Cargar datos iniciales
        await this.loadInitialData();

        // Iniciar auto-refresh cada 5 minutos
        this.startAutoRefresh();

        console.log('✅ InvestIA Predictor listo!');
    }

    /**
     * Configura los event listeners
     */
    setupEventListeners() {
        // Botón de refresh
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        // Selector de activo
        const assetSelector = document.getElementById('assetSelector');
        if (assetSelector) {
            assetSelector.addEventListener('change', (e) => {
                this.currentSymbol = e.target.value;
                this.updateChart();
            });
        }

        // Botones de período
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentPeriod = parseInt(e.target.dataset.days);
                this.updateChart();
            });
        });

        // Navegación
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        // Botón de generar portafolio
        const generatePortfolioBtn = document.getElementById('generatePortfolioBtn');
        if (generatePortfolioBtn) {
            generatePortfolioBtn.addEventListener('click', () => this.generatePortfolio());
        }

        // Botón de Backtest
        const runBacktestBtn = document.getElementById('runBacktestBtn');
        if (runBacktestBtn) {
            runBacktestBtn.addEventListener('click', () => this.runBacktest());
        }

        // Botón agregar símbolo
        const addSymbolBtn = document.getElementById('addSymbolBtn');
        if (addSymbolBtn) {
            addSymbolBtn.addEventListener('click', () => this.handleAddSymbol());
        }
    }

    /**
     * Ejecuta el Backtest
     */
    async runBacktest() {
        const symbol = document.getElementById('backtestSymbol').value;
        const days = document.getElementById('backtestPeriod').value;
        const amount = document.getElementById('backtestAmount').value;
        const btn = document.getElementById('runBacktestBtn');
        const stats = document.getElementById('backtestStats');

        try {
            btn.disabled = true;
            btn.innerHTML = '⏳ Simulando...';

            const result = await api.runBacktest(symbol, days, amount);

            // Mostrar estadísticas
            stats.style.display = 'flex';

            const stratReturn = result.return_pct;
            const benchReturn = result.benchmark_return_pct;
            const finalValue = result.final_value;

            // Mostrar Valor Final
            const finalValueEl = document.getElementById('btFinalValue');
            finalValueEl.textContent = `$${finalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            finalValueEl.className = `value ${stratReturn >= 0 ? 'positive' : 'negative'}`;

            const stratEl = document.getElementById('btStrategyReturn');
            stratEl.textContent = `${stratReturn.toFixed(2)}%`;
            stratEl.className = `value ${stratReturn >= 0 ? 'positive' : 'negative'}`;

            const benchEl = document.getElementById('btBenchmarkReturn');
            benchEl.textContent = `${benchReturn.toFixed(2)}%`;
            benchEl.className = `value ${benchReturn >= 0 ? 'positive' : 'negative'}`;

            document.getElementById('btTradeCount').textContent = result.trades.length;

            const ddEl = document.getElementById('btMaxDrawdown');
            ddEl.textContent = `${result.max_drawdown.toFixed(2)}%`;
            ddEl.className = `value ${result.max_drawdown > 20 ? 'negative' : 'neutral'}`;

            // Renderizar Bitácora
            const logContainer = document.getElementById('tradeLogContainer');
            const logBody = document.getElementById('tradeLogBody');

            if (result.trades.length > 0) {
                logContainer.style.display = 'block';
                logBody.innerHTML = result.trades.map(trade => `
                    <tr>
                        <td>${trade.date}</td>
                        <td class="${trade.type === 'BUY' ? 'text-success' : 'text-danger'}">
                            ${trade.type === 'BUY' ? '🟢 COMPRA' : '🔴 VENTA'}
                        </td>
                        <td>$${trade.price.toFixed(2)}</td>
                        <td>${trade.shares.toFixed(2)}</td>
                        <td>${trade.reason || (trade.type === 'BUY' ? `Score: ${trade.score}` : 'Señal Técnica')}</td>
                    </tr>
                `).join('');
            } else {
                logContainer.style.display = 'none';
            }

            // Renderizar gráfico
            chartManager.createBacktestChart('backtestChart', result.equity_curve, result.benchmark_curve);

            // Mensaje resumen
            const diff = stratReturn - benchReturn;
            let msg = '';
            let type = 'info';

            if (diff > 0) {
                msg = `¡Excelente! La IA superó al mercado por un ${diff.toFixed(2)}%`;
                type = 'success';
            } else {
                msg = `La IA rindió un ${Math.abs(diff).toFixed(2)}% menos que el mercado.`;
                type = 'warning';
            }

            this.showToast(type, msg);

        } catch (error) {
            console.error(error);
            this.showToast('error', 'Error al ejecutar la simulación');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-icon">▶️</span> Simular';
        }
    }

    /**
     * Verifica la conexión con la API
     */
    async checkAPIConnection() {
        const statusIndicator = document.getElementById('apiStatus');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');

        try {
            const connected = await api.checkConnection();

            if (connected) {
                statusDot.classList.add('connected');
                statusDot.classList.remove('error');
                statusText.textContent = 'Conectado';
            } else {
                throw new Error('No conectado');
            }
        } catch (error) {
            statusDot.classList.add('error');
            statusDot.classList.remove('connected');
            statusText.textContent = 'Sin conexión';
            this.showToast('error', 'No se pudo conectar con el servidor. Verifica que la API esté corriendo.');
        }
    }

    /**
     * Carga los datos iniciales
     */
    async loadInitialData() {
        this.setLoading(true);

        try {
            // Cargar predicciones
            await this.loadPredictions();

            // Cargar gráfico inicial
            await this.updateChart();

            // Actualizar tabla de activos
            this.updateAssetsTable();

        } catch (error) {
            console.error('Error cargando datos iniciales:', error);
            this.showToast('error', 'Error al cargar los datos. Intenta de nuevo.');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Carga las predicciones
     */
    async loadPredictions() {
        try {
            const response = await api.getAllPredictions();

            // Manejar estado de carga (cache warming)
            if (response.status === 'loading') {
                this.showLoadingState();
                return;
            }

            this.predictions = response.predictions || [];

            // Actualizar UI
            this.renderPredictionCards();
            this.updateStats();
            this.updateConfidenceChart();
            this.populateBacktestSelector();

            // Actualizar precios en el simulador
            const currentPrices = {};
            this.predictions.forEach(p => {
                currentPrices[p.symbol] = p.current_price;
            });
            simulator.renderHoldingsTable(currentPrices);

        } catch (error) {
            console.error('Error cargando predicciones:', error);
            // Mostrar estado de error
            this.showNoPredictions();
        }
    }

    /**
     * Llena el selector de Backtest con los activos disponibles
     */
    populateBacktestSelector() {
        const selector = document.getElementById('backtestSymbol');
        if (!selector) return;

        // Guardar selección actual si existe
        const currentSelection = selector.value;

        // Limpiar opciones
        selector.innerHTML = '';

        // Ordenar alfabéticamente
        const sortedPreds = [...this.predictions].sort((a, b) => a.symbol.localeCompare(b.symbol));

        sortedPreds.forEach(pred => {
            const option = document.createElement('option');
            option.value = pred.symbol;
            option.textContent = `${pred.symbol} - ${pred.name || ''}`;
            selector.appendChild(option);
        });

        // Restaurar selección o seleccionar el primero (VOO por defecto si existe)
        if (currentSelection && this.predictions.find(p => p.symbol === currentSelection)) {
            selector.value = currentSelection;
        } else {
            // Intentar seleccionar VOO por defecto
            if (this.predictions.find(p => p.symbol === 'VOO')) {
                selector.value = 'VOO';
            }
        }
    }
    showLoadingState() {
        const grid = document.getElementById('predictionsGrid');
        if (!grid) return;

        grid.innerHTML = `
            <div class="loading-container">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
                <h3>Analizando Mercado...</h3>
                <p style="color: var(--text-secondary); margin-top: 0.5rem;">
                    Nuestros algoritmos están procesando los datos en tiempo real.
                    <br>Por favor espera un momento...
                </p>
                <div class="loader" style="margin: 2rem auto; border: 4px solid var(--bg-secondary); border-top: 4px solid var(--accent-primary); border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite;"></div>
                <style>
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                </style>
            </div>
        `;

        // Reintentar automáticamente en 5 segundos
        setTimeout(() => this.loadPredictions(), 5000);
    }

    /**
     * Renderiza las tarjetas de predicción
     */
    renderPredictionCards() {
        const grid = document.getElementById('predictionsGrid');
        if (!grid) return;

        if (this.predictions.length === 0) {
            this.showNoPredictions();
            return;
        }

        grid.innerHTML = this.predictions.map(pred => this.createPredictionCard(pred)).join('');
    }

    /**
     * Crea el HTML de una tarjeta de predicción
     */
    createPredictionCard(prediction) {
        const trend = prediction.trend || 'neutral';
        const change = prediction.average_change_percent || 0;
        const changeClass = change >= 0 ? 'positive' : 'negative';
        const changeSymbol = change >= 0 ? '+' : '';

        const recommendation = prediction.recommendation || 'MANTENER';
        let recClass = 'hold';
        if (recommendation === 'COMPRAR') recClass = 'buy';
        if (recommendation === 'VENDER') recClass = 'sell';

        const confidencePercent = ((prediction.confidence?.score || 0.5) * 100).toFixed(0);
        const currentPrice = prediction.current_price || 0;

        // Sentiment Badge
        let sentimentHtml = '';
        if (prediction.sentiment) {
            const s = prediction.sentiment;
            let sClass = 'neutral';
            if (s.label === 'Bullish') sClass = 'positive';
            if (s.label === 'Bearish') sClass = 'negative';
            sentimentHtml = `<div class="sentiment-badge ${sClass}" title="Basado en ${s.count} noticias">📰 ${s.label} (${s.score.toFixed(2)})</div>`;
        }

        // Predicciones por día
        const predictions = prediction.predictions || [];
        const predDays = predictions.slice(0, 5).map((p, i) => `
            <div class="prediction-day">
                <span class="day-label">D${p.day || i + 1}</span>
                <span class="day-value ${p.change_percent >= 0 ? 'positive' : 'negative'}">
                    ${p.change_percent >= 0 ? '+' : ''}${(p.change_percent || 0).toFixed(1)}%
                </span>
            </div>
        `).join('');

        return `
            <div class="prediction-card ${trend}">
                <div class="card-header">
                    <div>
                        <div class="card-symbol">${prediction.symbol}</div>
                        <div class="card-name">${prediction.name || prediction.symbol}</div>
                    </div>
                    <span class="card-badge ${trend}">${trend}</span>
                </div>
                
                <div class="card-price">
                    <span class="current-price">$${currentPrice.toFixed(2)}</span>
                    <span class="price-change ${changeClass}">
                        ${changeSymbol}${change.toFixed(2)}%
                    </span>
                </div>
                
                ${sentimentHtml}
                
                <div class="card-predictions">
                    ${predDays}
                </div>
                
                <div class="card-footer">
                    <div class="confidence-meter">
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${confidencePercent}%"></div>
                        </div>
                        <span class="confidence-text">${confidencePercent}%</span>
                    </div>
                    <div class="card-actions">
                        <button class="btn-small buy-btn" onclick="app.handleBuy('${prediction.symbol}', ${currentPrice})">
                            Comprar
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Maneja la compra desde la UI
     */
    handleBuy(symbol, price) {
        // Por simplicidad, compramos 1 unidad por defecto o preguntamos
        const quantity = prompt(`¿Cuántas acciones de ${symbol} quieres comprar a $${price}?`, "1");
        if (quantity && parseInt(quantity) > 0) {
            const result = simulator.buy(symbol, price, parseInt(quantity));
            if (result.success) {
                this.showToast('success', result.message);
            } else {
                this.showToast('error', result.message);
            }
        }
    }

    /**
     * Abre modal de trade (placeholder para venta)
     */
    openTradeModal(type, symbol, price) {
        if (type === 'SELL') {
            const quantity = prompt(`¿Cuántas acciones de ${symbol} quieres vender a $${price}?`, "1");
            if (quantity && parseInt(quantity) > 0) {
                const result = simulator.sell(symbol, price, parseInt(quantity));
                if (result.success) {
                    this.showToast('success', result.message);
                } else {
                    this.showToast('error', result.message);
                }
            }
        }
    }

    /**
     * Muestra mensaje cuando no hay predicciones
     */
    showNoPredictions() {
        const grid = document.getElementById('predictionsGrid');
        if (!grid) return;

        grid.innerHTML = `
            <div class="loading-container">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
                <h3>No hay predicciones disponibles</h3>
                <p style="color: var(--text-secondary); margin-top: 0.5rem;">
                    Los modelos aún no han sido entrenados. Ejecuta el script de entrenamiento:
                </p>
                <code style="display: block; margin-top: 1rem; padding: 1rem; background: var(--bg-tertiary); border-radius: 8px;">
                    cd backend && python train.py --all
                </code>
            </div>
        `;
    }

    /**
     * Actualiza las estadísticas del dashboard
     */
    async updateStats() {
        // Total de activos
        const totalAssets = document.getElementById('totalAssets');
        if (totalAssets) {
            totalAssets.textContent = this.predictions.length || 6;
        }

        // Precisión promedio
        const avgAccuracy = document.getElementById('avgAccuracy');
        if (avgAccuracy) {
            const accuracies = this.predictions
                .map(p => p.confidence?.directional_accuracy || 0)
                .filter(a => a > 0);

            if (accuracies.length > 0) {
                const avg = accuracies.reduce((a, b) => a + b, 0) / accuracies.length;
                avgAccuracy.textContent = `${(avg * 100).toFixed(0)}%`;
            } else {
                avgAccuracy.textContent = '--%';
            }
        }

        // Señales alcistas
        const bullishCount = document.getElementById('bullishCount');
        if (bullishCount) {
            const bullish = this.predictions.filter(p => p.trend === 'bullish').length;
            bullishCount.textContent = bullish;
        }

        // Última actualización (Basada en entrenamiento real)
        const lastUpdate = document.getElementById('lastUpdate');
        if (lastUpdate) {
            try {
                const status = await api.getTrainingStatus();
                const models = status.models || [];

                // Encontrar la fecha más reciente
                const dates = models
                    .map(m => m.last_trained)
                    .filter(d => d) // Filtrar nulos
                    .map(d => new Date(d));

                if (dates.length > 0) {
                    // Ordenar descendente
                    const mostRecent = new Date(Math.max.apply(null, dates));

                    lastUpdate.textContent = mostRecent.toLocaleString('es-CL', {
                        hour: '2-digit',
                        minute: '2-digit',
                        day: '2-digit',
                        month: '2-digit',
                        hour12: false
                    }).replace(',', '');
                    lastUpdate.title = `Último entrenamiento: ${mostRecent.toLocaleString()}`;
                } else {
                    lastUpdate.textContent = 'Pendiente';
                }
            } catch (error) {
                console.warn('No se pudo obtener fecha de entrenamiento:', error);
                lastUpdate.textContent = '--:--';
            }
        }
    }

    /**
     * Actualiza el gráfico principal
     */
    async updateChart() {
        try {
            const data = await api.getChartData(this.currentSymbol, this.currentPeriod);
            chartManager.createPriceChart('priceChart', data);
        } catch (error) {
            console.error('Error actualizando gráfico:', error);
        }
    }

    /**
     * Actualiza el gráfico de confianza
     */
    updateConfidenceChart() {
        if (this.predictions.length > 0) {
            chartManager.createConfidenceChart('confidenceChart', this.predictions);
        }
    }

    /**
     * Actualiza la tabla de activos
     */
    updateAssetsTable() {
        const tbody = document.getElementById('assetsTableBody');
        if (!tbody) return;

        const riskLabels = {
            'very_low': 'Muy Bajo',
            'low': 'Bajo',
            'medium_low': 'Medio-Bajo',
            'medium': 'Medio',
            'high': 'Alto'
        };

        const rows = this.predictions.map(pred => {
            const change = pred.average_change_percent || 0;
            const changeClass = change >= 0 ? 'positive' : 'negative';
            const recommendation = pred.recommendation || 'MANTENER';
            let recClass = 'hold';
            if (recommendation === 'COMPRAR') recClass = 'buy';
            if (recommendation === 'VENDER') recClass = 'sell';

            // Obtener el último día de predicción
            const lastPred = pred.predictions?.[pred.predictions.length - 1];
            const pred5d = lastPred?.predicted_price || pred.current_price;
            const pred5dChange = lastPred?.change_percent || 0;

            return `
                <tr>
                    <td><strong>${pred.symbol}</strong></td>
                    <td>${pred.name || pred.symbol}</td>
                    <td><small>${pred.description || ''}</small></td>
                    <td>ETF/Stock</td>
                    <td><span class="risk-badge ${pred.risk || 'medium'}">${riskLabels[pred.risk] || 'Medio'}</span></td>
                    <td>$${(pred.current_price || 0).toFixed(2)}</td>
                    <td class="${pred5dChange >= 0 ? 'positive' : 'negative'}">
                        $${pred5d.toFixed(2)} (${pred5dChange >= 0 ? '+' : ''}${pred5dChange.toFixed(2)}%)
                    </td>
                    <td><span class="recommendation ${recClass}">${recommendation}</span></td>
                    <td>
                        <button class="btn-small" style="background: #ef5350;" onclick="app.handleRemoveSymbol('${pred.symbol}')">🗑️</button>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = rows.join('');
    }

    /**
     * Refresca todos los datos
     */
    async refreshData() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<span class="btn-icon">⏳</span> Actualizando...';
        }

        try {
            await this.checkAPIConnection();

            // Forzar actualización en backend
            await api.post('/predict/refresh');

            await this.loadInitialData();
            this.showToast('success', 'Datos de mercado actualizados');
        } catch (error) {
            console.error('Refresh error:', error);
            this.showToast('error', `Error: ${error.message || 'No se pudo conectar'}`);
        } finally {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<span class="btn-icon">🔄</span> Actualizar';
            }
        }
    }

    /**
     * Inicia el auto-refresh
     */
    startAutoRefresh() {
        // Refrescar cada 5 minutos
        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, 5 * 60 * 1000);
    }

    /**
     * Muestra/oculta el estado de carga
     */
    setLoading(loading) {
        this.isLoading = loading;
    }

    /**
     * Genera el portafolio de inversión
     */
    async generatePortfolio() {
        const riskProfile = document.getElementById('riskProfile').value;
        const amount = document.getElementById('investAmount').value;
        const btn = document.getElementById('generatePortfolioBtn');
        const results = document.getElementById('portfolioResults');

        if (!amount || amount < 100) {
            this.showToast('warning', 'Por favor ingresa un monto válido (min $100)');
            return;
        }

        try {
            btn.disabled = true;
            btn.innerHTML = '<span class="btn-icon">⏳</span> Generando...';

            const data = await api.generatePortfolio(riskProfile, amount);

            // Mostrar resultados
            results.style.display = 'block';

            // Renderizar gráfico
            chartManager.createAllocationChart('allocationChart', data.allocation);

            // Mostrar retorno esperado
            const returnEl = document.getElementById('portfolioReturn');
            if (returnEl) {
                returnEl.textContent = `+${data.expected_annual_return}%`;
            }

            // Configurar botón de ejecución
            const execBtn = document.getElementById('executePortfolioBtn');
            if (execBtn) {
                execBtn.onclick = () => this.executePortfolio(data.allocation);
            }

            // Renderizar tabla
            const tbody = document.getElementById('allocationTableBody');
            tbody.innerHTML = data.allocation.map(asset => `
                <tr>
                    <td>
                        <strong>${asset.symbol}</strong><br>
                        <small>${asset.name}</small>
                    </td>
                    <td>${asset.percentage}%</td>
                    <td>$${asset.amount.toLocaleString()}</td>
                    <td>${asset.shares}</td>
                    <td><small>${asset.recent_earnings || '-'}</small></td>
                    <td><small><em>${asset.investment_thesis || '-'}</em></small></td>
                </tr>
            `).join('');

            this.showToast('success', 'Portafolio generado exitosamente');

        } catch (error) {
            console.error('Error generando portafolio:', error);
            this.showToast('error', 'Error al generar el portafolio');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-icon">✨</span> Generar Propuesta';
        }
    }

    /**
     * Ejecuta la compra del portafolio en el simulador
     */
    executePortfolio(allocation) {
        if (!confirm('¿Estás seguro de comprar todos estos activos en el simulador?')) return;

        let successCount = 0;

        allocation.forEach(asset => {
            // Comprar cada activo
            // Nota: Usamos el precio estimado del portafolio, idealmente deberíamos tener el precio real actual
            // pero para el simulador está bien usar el snapshot del momento de generación.
            // asset.shares es float, el simulador puede manejarlo o lo redondeamos?
            // simulator.buy espera cantidad entera? Revisemos simulator.js... 
            // simulator.js: this.holdings[symbol].quantity += quantity; (suma directo)
            // Mejor redondeamos hacia abajo para asegurar ejecución simple o permitimos fraccional si JS lo aguanta.
            // Vamos a permitir fraccional por ahora.

            // Necesitamos el precio unitario. asset.amount / asset.shares = precio
            const price = asset.amount / asset.shares;

            const result = simulator.buy(asset.symbol, price, asset.shares);
            if (result.success) successCount++;
        });

        if (successCount > 0) {
            this.showToast('success', `¡Orden ejecutada! Se compraron ${successCount} activos.`);
            // Scroll al simulador para ver resultados?
            // document.getElementById('simulator').scrollIntoView({ behavior: 'smooth' });
        } else {
            this.showToast('warning', 'No se pudieron comprar los activos (¿Fondos insuficientes?)');
        }
    }

    /**
     * Muestra una notificación toast
     */
    showToast(type, message) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;

        container.appendChild(toast);

        // Auto-remove después de 5 segundos
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});
