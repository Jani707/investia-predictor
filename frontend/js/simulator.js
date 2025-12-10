/**
 * InvestIA Predictor - Portfolio Simulator
 * Maneja la lógica de "Paper Trading" (Dinero Virtual)
 */

class PortfolioSimulator {
    constructor() {
        this.balance = 10000.00; // Balance inicial $10,000
        this.holdings = {}; // { "VOO": { quantity: 5, avgPrice: 350.00 } }
        this.transactions = [];

        this.loadFromStorage();
        this.updateUI();
    }

    /**
     * Carga datos guardados
     */
    loadFromStorage() {
        const saved = localStorage.getItem('investia_simulator');
        if (saved) {
            const data = JSON.parse(saved);
            this.balance = data.balance;
            this.holdings = data.holdings;
            this.transactions = data.transactions;
        }
    }

    /**
     * Guarda datos
     */
    save() {
        const data = {
            balance: this.balance,
            holdings: this.holdings,
            transactions: this.transactions
        };
        localStorage.setItem('investia_simulator', JSON.stringify(data));
        this.updateUI();
    }

    /**
     * Ejecuta una compra
     */
    buy(symbol, price, quantity) {
        const totalCost = price * quantity;

        if (totalCost > this.balance) {
            return { success: false, message: "Fondos insuficientes" };
        }

        this.balance -= totalCost;

        if (!this.holdings[symbol]) {
            this.holdings[symbol] = { quantity: 0, avgPrice: 0 };
        }

        // Calcular nuevo precio promedio
        const currentQty = this.holdings[symbol].quantity;
        const currentAvg = this.holdings[symbol].avgPrice;
        const newAvg = ((currentQty * currentAvg) + totalCost) / (currentQty + quantity);

        this.holdings[symbol].quantity += quantity;
        this.holdings[symbol].avgPrice = newAvg;

        this.transactions.push({
            type: 'BUY',
            symbol,
            price,
            quantity,
            date: new Date().toISOString()
        });

        this.save();
        return { success: true, message: `Compraste ${quantity} de ${symbol}` };
    }

    /**
     * Ejecuta una venta
     */
    sell(symbol, price, quantity) {
        if (!this.holdings[symbol] || this.holdings[symbol].quantity < quantity) {
            return { success: false, message: "No tienes suficientes acciones" };
        }

        const totalValue = price * quantity;
        this.balance += totalValue;

        this.holdings[symbol].quantity -= quantity;

        if (this.holdings[symbol].quantity === 0) {
            delete this.holdings[symbol];
        }

        this.transactions.push({
            type: 'SELL',
            symbol,
            price,
            quantity,
            date: new Date().toISOString()
        });

        this.save();
        return { success: true, message: `Vendiste ${quantity} de ${symbol}` };
    }

    /**
     * Actualiza la interfaz del simulador
     */
    updateUI() {
        // Actualizar balance en header
        const balanceEl = document.getElementById('simBalanceDisplay').querySelector('.value');
        if (balanceEl) balanceEl.textContent = `$${this.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

        // Actualizar tabla de holdings
        const tbody = document.getElementById('holdingsTableBody');
        if (!tbody) return;

        if (Object.keys(this.holdings).length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No tienes activos aún. ¡Compra algo!</td></tr>';
            return;
        }

        // Nota: Necesitamos el precio actual para calcular ganancias. 
        // Esto se actualizará desde app.js cuando tenga los precios.
        // Por ahora renderizamos lo que tenemos.
        this.renderHoldingsTable();
    }

    renderHoldingsTable(currentPrices = {}) {
        const tbody = document.getElementById('holdingsTableBody');
        if (!tbody) return;

        let totalPortfolioValue = 0;

        const rows = Object.entries(this.holdings).map(([symbol, data]) => {
            const currentPrice = currentPrices[symbol] || data.avgPrice; // Fallback
            const totalValue = data.quantity * currentPrice;
            totalPortfolioValue += totalValue;

            const profit = (currentPrice - data.avgPrice) * data.quantity;
            const profitPercent = ((currentPrice - data.avgPrice) / data.avgPrice) * 100;
            const profitClass = profit >= 0 ? 'positive' : 'negative';

            return `
                <tr>
                    <td><strong>${symbol}</strong></td>
                    <td>${data.quantity}</td>
                    <td>$${data.avgPrice.toFixed(2)}</td>
                    <td>$${currentPrice.toFixed(2)}</td>
                    <td>$${totalValue.toFixed(2)}</td>
                    <td class="${profitClass}">
                        $${profit.toFixed(2)} (${profitPercent.toFixed(2)}%)
                    </td>
                    <td>
                        <button class="btn-small sell-btn" onclick="app.openTradeModal('SELL', '${symbol}', ${currentPrice})">Vender</button>
                    </td>
                </tr>
            `;
        }).join('');

        tbody.innerHTML = rows;

        // Actualizar valor total del portafolio (Cash + Activos)
        const totalValueEl = document.getElementById('portfolioValue');
        if (totalValueEl) {
            const total = this.balance + totalPortfolioValue;
            totalValueEl.textContent = `$${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
        }
    }
}

const simulator = new PortfolioSimulator();
