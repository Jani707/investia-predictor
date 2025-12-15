/**
 * InvestIA Predictor - Chart Manager
 * Usa TradingView Lightweight Charts para gráficos financieros profesionales
 */

class ChartManager {
    constructor() {
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.resizeObserver = null;
    }

    /**
     * Crea o actualiza el gráfico de precios (Usando Chart.js)
     */
    createPriceChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        // Destruir gráfico anterior si existe
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }

        const ctx = canvas.getContext('2d');

        // Preparar datasets
        const datasets = [];

        // 1. Precio Histórico
        if (data.datasets && data.datasets.close) {
            datasets.push({
                label: 'Precio Histórico',
                data: data.datasets.close,
                borderColor: '#2962FF',
                backgroundColor: 'rgba(41, 98, 255, 0.1)',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 0,
                fill: true
            });
        }

        // 2. Predicciones (si existen)
        if (data.predictions) {
            // Necesitamos alinear las predicciones con el eje X extendido
            // El backend devuelve labels para todo, o labels separados?
            // Revisando historical.py: devuelve chart_data["labels"] (histórico) y chart_data["predictions"]["labels"] (futuro)

            // Combinar labels
            const allLabels = [...data.labels, ...data.predictions.labels];

            // Crear array de datos de predicción alineado
            // Llenar con nulls para la parte histórica
            const predictionValues = new Array(data.labels.length).fill(null);

            // Conectar visualmente: el último punto histórico es el primero de la predicción?
            // Si no, habrá un hueco. Vamos a añadir el último valor histórico al inicio de la predicción
            if (data.datasets.close.length > 0) {
                // Reemplazar el último null con el último precio real para continuidad
                predictionValues[predictionValues.length - 1] = data.datasets.close[data.datasets.close.length - 1];
            }

            // Añadir valores futuros
            data.predictions.values.forEach(v => predictionValues.push(v));

            datasets.push({
                label: 'Predicción IA',
                data: predictionValues,
                borderColor: '#00E676',
                borderDash: [5, 5],
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 2,
                fill: false
            });

            // Actualizar labels globales
            data.labels = allLabels;
        }

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        labels: { color: '#d1d4dc' }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#2B2B43' },
                        ticks: { color: '#d1d4dc' }
                    },
                    y: {
                        grid: { color: '#2B2B43' },
                        ticks: { color: '#d1d4dc' }
                    }
                }
            }
        });
    }

    /**
     * Crea el gráfico de Backtest (Comparativa)
     */
    /**
     * Crea el gráfico de Backtest (Comparativa) usando Chart.js
     */
    createBacktestChart(canvasId, strategyData, benchmarkData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        // Destruir gráfico anterior si existe
        if (canvas.chartInstance) {
            canvas.chartInstance.destroy();
        }

        const ctx = canvas.getContext('2d');

        // Extraer labels (fechas) de strategyData
        // strategyData es [{time: '...', value: ...}, ...]
        const labels = strategyData.map(d => d.time);
        const strategyValues = strategyData.map(d => d.value);
        const benchmarkValues = benchmarkData.map(d => d.value);

        canvas.chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Estrategia IA',
                        data: strategyValues,
                        borderColor: '#00E676', // Verde
                        backgroundColor: 'rgba(0, 230, 118, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        pointRadius: 0,
                        fill: true
                    },
                    {
                        label: 'Buy & Hold (Benchmark)',
                        data: benchmarkValues,
                        borderColor: '#2962FF', // Azul
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.1,
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        labels: { color: '#d1d4dc' }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#2B2B43' },
                        ticks: { color: '#d1d4dc' }
                    },
                    y: {
                        grid: { color: '#2B2B43' },
                        ticks: { color: '#d1d4dc' }
                    }
                }
            }
        });
    }

    /**
     * Crea el gráfico de distribución de portafolio
     */
    createAllocationChart(canvasId, allocationData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        // Destruir gráfico anterior si existe
        if (canvas.chartInstance) {
            canvas.chartInstance.destroy();
        }

        const ctx = canvas.getContext('2d');
        const labels = allocationData.map(a => a.symbol);
        const data = allocationData.map(a => a.percentage);
        const colors = [
            '#26a69a', '#2962FF', '#FF6D00', '#F06292',
            '#AB47BC', '#7E57C2', '#5C6BC0', '#42A5F5'
        ];

        canvas.chartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#d1d4dc' }
                    }
                }
            }
        });
    }

    /**
     * Gráfico de Confianza (Bar Chart)
     */
    createConfidenceChart(canvasId, predictions) {
        // Por ahora no implementado en el diseño principal, 
        // pero dejamos el método para evitar errores en app.js
        console.log("Confidence chart update skipped (not in current layout)");
    }
}

const chartManager = new ChartManager();
