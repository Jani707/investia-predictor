/**
 * InvestIA Predictor - Charts Module
 * Maneja la creación y actualización de gráficos con Chart.js
 */

class ChartManager {
    constructor() {
        this.charts = {};
        this.chartColors = {
            primary: '#58a6ff',
            secondary: '#79c0ff',
            success: '#3fb950',
            danger: '#f85149',
            warning: '#f0b429',
            grid: '#30363d',
            text: '#8b949e'
        };
    }

    /**
     * Destruye un gráfico existente
     */
    destroyChart(chartId) {
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
            delete this.charts[chartId];
        }
    }

    /**
     * Crea o actualiza el gráfico de precios
     */
    createPriceChart(canvasId, data) {
        this.destroyChart(canvasId);

        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const hasPrections = data.predictions && data.predictions.labels;

        // Preparar datasets
        const datasets = [
            {
                label: 'Precio de Cierre',
                data: data.datasets.close,
                borderColor: this.chartColors.primary,
                backgroundColor: this.hexToRgba(this.chartColors.primary, 0.1),
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                borderWidth: 2
            }
        ];

        // Agregar predicciones si existen
        let allLabels = [...data.labels];

        if (hasPrections) {
            // Agregar predicciones como un dataset separado
            const predictionData = new Array(data.labels.length - 1).fill(null);
            predictionData.push(data.datasets.close[data.datasets.close.length - 1]); // Conectar con último punto
            predictionData.push(...data.predictions.values);

            allLabels = [...data.labels, ...data.predictions.labels];

            datasets.push({
                label: 'Predicción',
                data: predictionData,
                borderColor: this.chartColors.success,
                backgroundColor: this.hexToRgba(this.chartColors.success, 0.1),
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 8,
                borderWidth: 2,
                borderDash: [5, 5]
            });
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: allLabels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: this.chartColors.text,
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: '#21262d',
                        titleColor: '#f0f6fc',
                        bodyColor: '#8b949e',
                        borderColor: '#30363d',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            label: (context) => {
                                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: this.chartColors.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: this.chartColors.text,
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        grid: {
                            color: this.chartColors.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: this.chartColors.text,
                            callback: (value) => `$${value.toFixed(0)}`
                        }
                    }
                }
            }
        });

        return this.charts[canvasId];
    }

    /**
     * Crea el gráfico de confianza por activo
     */
    createConfidenceChart(canvasId, predictions) {
        this.destroyChart(canvasId);

        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const labels = predictions.map(p => p.symbol);
        const confidenceScores = predictions.map(p => (p.confidence?.score || 0.5) * 100);
        const colors = predictions.map(p => {
            const level = p.confidence?.level || 'medium';
            if (level === 'high') return this.chartColors.success;
            if (level === 'low') return this.chartColors.danger;
            return this.chartColors.warning;
        });

        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Confianza del Modelo (%)',
                    data: confidenceScores,
                    backgroundColor: colors.map(c => this.hexToRgba(c, 0.7)),
                    borderColor: colors,
                    borderWidth: 2,
                    borderRadius: 8,
                    barThickness: 40
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#21262d',
                        titleColor: '#f0f6fc',
                        bodyColor: '#8b949e',
                        borderColor: '#30363d',
                        borderWidth: 1,
                        padding: 12,
                        callbacks: {
                            label: (context) => {
                                return `Confianza: ${context.parsed.x.toFixed(1)}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        min: 0,
                        max: 100,
                        grid: {
                            color: this.chartColors.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: this.chartColors.text,
                            callback: (value) => `${value}%`
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: this.chartColors.text,
                            font: {
                                weight: 'bold'
                            }
                        }
                    }
                }
            }
        });

        return this.charts[canvasId];
    }

    /**
     * Crea un mini gráfico sparkline
     */
    createSparkline(canvasId, data, trend = 'neutral') {
        this.destroyChart(canvasId);

        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const color = trend === 'bullish' ? this.chartColors.success :
            trend === 'bearish' ? this.chartColors.danger :
                this.chartColors.warning;

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map((_, i) => i),
                datasets: [{
                    data: data,
                    borderColor: color,
                    backgroundColor: this.hexToRgba(color, 0.1),
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                scales: {
                    x: { display: false },
                    y: { display: false }
                }
            }
        });

        return this.charts[canvasId];
    }

    /**
     * Convierte hex a rgba
     */
    hexToRgba(hex, alpha = 1) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    /**
     * Crea un gráfico de torta para la asignación de portafolio
     */
    createAllocationChart(canvasId, allocation) {
        this.destroyChart(canvasId);

        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const labels = allocation.map(a => a.symbol);
        const data = allocation.map(a => a.percentage);

        // Generar colores
        const baseColors = [
            this.chartColors.primary,
            this.chartColors.success,
            this.chartColors.warning,
            this.chartColors.danger,
            this.chartColors.secondary
        ];

        const backgroundColors = allocation.map((_, i) =>
            this.hexToRgba(baseColors[i % baseColors.length], 0.7)
        );

        const borderColors = allocation.map((_, i) =>
            baseColors[i % baseColors.length]
        );

        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: this.chartColors.text,
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: '#21262d',
                        titleColor: '#f0f6fc',
                        bodyColor: '#8b949e',
                        borderColor: '#30363d',
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => {
                                return `${context.label}: ${context.parsed}%`;
                            }
                        }
                    }
                }
            }
        });

        return this.charts[canvasId];
    }
}

// Instancia global
const chartManager = new ChartManager();
