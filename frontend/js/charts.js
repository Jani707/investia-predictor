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
     * Crea o actualiza el gráfico de precios (Candlestick)
     */
    createPriceChart(containerId, data) {
        const container = document.getElementById('tvChartContainer');
        if (!container) return;

        // Limpiar gráfico anterior si existe
        if (this.chart) {
            this.chart.remove();
            this.chart = null;
        }

        // Configuración del gráfico
        const chartOptions = {
            layout: {
                textColor: '#d1d4dc',
                background: { type: 'solid', color: '#1e222d' },
            },
            grid: {
                vertLines: { color: '#2B2B43' },
                horzLines: { color: '#2B2B43' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#2B2B43',
            },
            timeScale: {
                borderColor: '#2B2B43',
                timeVisible: true,
            },
        };

        // Crear instancia
        this.chart = LightweightCharts.createChart(container, chartOptions);

        // Serie de Velas
        this.candleSeries = this.chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        // Formatear datos para Lightweight Charts
        // Esperamos data.dates (fechas) y data.prices (precios close)
        // Para velas reales necesitaríamos Open, High, Low, Close.
        // Como la API actual devuelve solo Close, simularemos velas simples o usaremos LineSeries si no hay OHLC.

        // NOTA: Para este demo, convertiremos los datos lineales a formato compatible
        // Idealmente el backend debería enviar OHLC.
        // Usaremos LineSeries por ahora si solo tenemos Close, o simularemos velas.

        // Si data tiene formato OHLC (lo ideal):
        if (data.ohlc) {
            this.candleSeries.setData(data.ohlc);
        } else {
            // Fallback a LineSeries si solo tenemos precios de cierre
            this.chart.removeSeries(this.candleSeries);
            this.candleSeries = this.chart.addLineSeries({
                color: '#2962FF',
                lineWidth: 2,
            });

            const lineData = data.dates.map((date, index) => ({
                time: date,
                value: data.prices[index]
            }));

            this.candleSeries.setData(lineData);
        }

        // Ajustar tamaño automáticamente
        this.chart.timeScale().fitContent();

        // Manejar resize
        if (this.resizeObserver) this.resizeObserver.disconnect();
        this.resizeObserver = new ResizeObserver(entries => {
            if (entries.length === 0 || entries[0].target !== container) { return; }
            const newRect = entries[0].contentRect;
            this.chart.applyOptions({ height: newRect.height, width: newRect.width });
        });
        this.resizeObserver.observe(container);
    }

    /**
     * Crea el gráfico de Backtest (Comparativa)
     */
    createBacktestChart(containerId, strategyData, benchmarkData) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Limpiar
        container.innerHTML = '';

        const chart = LightweightCharts.createChart(container, {
            layout: { textColor: '#d1d4dc', background: { type: 'solid', color: '#1e222d' } },
            grid: { vertLines: { color: '#2B2B43' }, horzLines: { color: '#2B2B43' } },
            rightPriceScale: { borderColor: '#2B2B43' },
            timeScale: { borderColor: '#2B2B43' },
        });

        // Línea Estrategia (Verde)
        const strategySeries = chart.addLineSeries({
            color: '#26a69a',
            lineWidth: 2,
            title: 'Estrategia IA',
        });
        strategySeries.setData(strategyData);

        // Línea Benchmark (Gris/Azul)
        const benchmarkSeries = chart.addLineSeries({
            color: '#2962FF',
            lineWidth: 2,
            lineStyle: 2, // Dashed
            title: 'Buy & Hold',
        });
        benchmarkSeries.setData(benchmarkData);

        chart.timeScale().fitContent();

        // Resize observer
        new ResizeObserver(entries => {
            if (entries.length === 0) return;
            const newRect = entries[0].contentRect;
            chart.applyOptions({ height: newRect.height, width: newRect.width });
        }).observe(container);
    }

    /**
     * Gráfico de Confianza (Mantenemos Chart.js para este gráfico simple de barras si es necesario,
     * o lo eliminamos si ya no encaja en el diseño. Por ahora lo dejamos comentado o simplificado).
     */
    createConfidenceChart(canvasId, predictions) {
        // Implementación opcional o mantener Chart.js solo para este widget pequeño
        // Por simplicidad en esta fase, nos enfocamos en el gráfico principal.
    }
}

const chartManager = new ChartManager();
