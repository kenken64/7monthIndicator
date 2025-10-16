// ============================================================================
// Backtesting Functions for Dashboard
// ============================================================================

/**
 * Load backtest data availability on page load
 */
async function loadBacktestData() {
    try {
        const response = await fetch('/api/backtest/available-data');
        const result = await response.json();

        if (result.success && result.data) {
            const data = result.data;

            // Update signal data
            if (data.signals && data.signals.length > 0) {
                const signalData = data.signals[0];
                document.getElementById('backtestSignalCount').textContent = signalData.signal_count || 0;
                document.getElementById('backtestBuyCount').textContent = signalData.buy_count || 0;
                document.getElementById('backtestSellCount').textContent = signalData.sell_count || 0;

                // Format dates
                if (signalData.first_signal && signalData.last_signal) {
                    const firstDate = new Date(signalData.first_signal).toLocaleDateString();
                    const lastDate = new Date(signalData.last_signal).toLocaleDateString();
                    document.getElementById('backtestSignalDates').textContent = `${firstDate} - ${lastDate}`;
                }

                // Set status
                const statusEl = document.getElementById('backtestDataStatus');
                const recommendEl = document.getElementById('backtestRecommendation');

                if (signalData.buy_count > 0 || signalData.sell_count > 0) {
                    statusEl.textContent = '✅ Ready';
                    statusEl.className = 'text-sm font-bold text-green-600';
                    recommendEl.textContent = 'Sufficient data for backtesting';
                } else {
                    statusEl.textContent = '⚠️  Limited';
                    statusEl.className = 'text-sm font-bold text-yellow-600';
                    recommendEl.textContent = 'Need BUY/SELL signals';
                }
            } else {
                // No signals
                document.getElementById('backtestSignalCount').textContent = '0';
                document.getElementById('backtestDataStatus').textContent = '❌  No Data';
                document.getElementById('backtestDataStatus').className = 'text-sm font-bold text-red-600';
                document.getElementById('backtestRecommendation').textContent = 'Run bot to collect signals';
            }

            // Load insights immediately
            await loadBacktestInsights();
        }
    } catch (error) {
        console.error('Error loading backtest data:', error);
    }
}

/**
 * Run quick backtest with current weights
 */
async function runQuickBacktest() {
    const btn = document.getElementById('quickBacktestBtn');
    const loadingEl = document.getElementById('backtestLoading');
    const resultsEl = document.getElementById('backtestResults');

    try {
        // Disable button and show loading
        btn.disabled = true;
        btn.innerHTML = '<span class="text-2xl">⏳</span><div class="ml-3 text-left"><div class="font-semibold">Running...</div><div class="text-xs opacity-90">Please wait</div></div>';
        loadingEl.style.display = 'block';
        resultsEl.style.display = 'none';

        const response = await fetch('/api/backtest/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: 'SUIUSDC',
                days_back: 30
            })
        });

        const result = await response.json();

        if (result.success && result.data) {
            displayBacktestResults(result.data);
            // Reload insights with new backtest data
            await loadBacktestInsights();
        } else {
            alert('Backtest failed: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error running backtest:', error);
        alert('Error running backtest. Check console for details.');
    } finally {
        // Re-enable button
        btn.disabled = false;
        btn.innerHTML = '<span class="text-2xl">⚡</span><div class="ml-3 text-left"><div class="font-semibold">Quick Backtest</div><div class="text-xs opacity-90">Test current weight configuration</div></div>';
        loadingEl.style.display = 'none';
    }
}

/**
 * Run weight optimization with PIN protection
 */
async function runWeightOptimization() {
    // Prompt for PIN
    const pin = prompt('Enter your 6-digit PIN to run weight optimization:');

    if (!pin) {
        return; // User cancelled
    }

    if (!/^\d{6}$/.test(pin)) {
        alert('PIN must be exactly 6 digits');
        return;
    }

    const btn = document.getElementById('optimizeBtn');
    const loadingEl = document.getElementById('backtestLoading');

    try {
        // Disable button and show loading
        btn.disabled = true;
        btn.innerHTML = '<span class="text-2xl">⏳</span><div class="ml-3 text-left"><div class="font-semibold">Optimizing...</div><div class="text-xs opacity-90">Testing 6 configurations</div></div>';
        loadingEl.style.display = 'block';

        const response = await fetch('/api/backtest/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pin: pin,
                symbol: 'SUIUSDC',
                days_back: 30
            })
        });

        const result = await response.json();

        if (result.success && result.data) {
            // Display best result
            if (result.data.best_by_roi) {
                displayBacktestResults(result.data.best_by_roi);
            }

            // Show all results in console
            console.log('Optimization Results:', result.data.results);

            const roi = result.data.best_by_roi && result.data.best_by_roi.roi ? result.data.best_by_roi.roi.toFixed(2) : '0.00';
            alert('Optimization complete! Tested ' + result.data.total_tested + ' configurations.\nBest ROI: ' + roi + '%\nCheck console for full results.');

            // Reload insights
            await loadBacktestInsights();
        } else {
            // Check if it's a PIN error
            if (response.status === 401 || response.status === 429) {
                alert('PIN validation failed: ' + (result.message || 'Invalid PIN'));
            } else {
                alert('Optimization failed: ' + (result.error || 'Unknown error'));
            }
        }
    } catch (error) {
        console.error('Error running optimization:', error);
        alert('Error running optimization. Check console for details.');
    } finally {
        // Re-enable button
        btn.disabled = false;
        btn.innerHTML = '<span class="text-2xl">🎯</span><div class="ml-3 text-left"><div class="font-semibold">Optimize Weights</div><div class="text-xs opacity-90">Find best signal weight combination</div></div>';
        loadingEl.style.display = 'none';
    }
}

/**
 * Display backtest results in the UI
 */
function displayBacktestResults(data) {
    const resultsEl = document.getElementById('backtestResults');

    // Update metrics
    const roi = data.roi || 0;
    document.getElementById('backtestROI').textContent = roi.toFixed(2) + '%';
    document.getElementById('backtestROI').className = 'text-xl font-bold ' + (roi > 0 ? 'text-green-600' : 'text-red-600');

    const winRate = data.win_rate || 0;
    document.getElementById('backtestWinRate').textContent = winRate.toFixed(1) + '%';
    document.getElementById('backtestWinRate').className = 'text-xl font-bold ' + (winRate > 50 ? 'text-green-600' : 'text-yellow-600');

    document.getElementById('backtestTotalTrades').textContent = data.total_trades || 0;

    const pnl = data.total_pnl || 0;
    document.getElementById('backtestTotalPnL').textContent = '$' + pnl.toFixed(2);
    document.getElementById('backtestTotalPnL').className = 'text-xl font-bold ' + (pnl > 0 ? 'text-green-600' : 'text-red-600');

    const sharpe = data.sharpe_ratio || 0;
    document.getElementById('backtestSharpe').textContent = sharpe.toFixed(2);
    document.getElementById('backtestSharpe').className = 'text-xl font-bold ' + (sharpe > 1 ? 'text-green-600' : 'text-gray-600');

    const drawdown = data.max_drawdown || 0;
    document.getElementById('backtestDrawdown').textContent = drawdown.toFixed(1) + '%';
    document.getElementById('backtestDrawdown').className = 'text-xl font-bold ' + (drawdown > 20 ? 'text-red-600' : 'text-yellow-600');

    // Update period
    if (data.config) {
        document.getElementById('backtestPeriod').textContent = data.config.start_date + ' to ' + data.config.end_date;
    }

    // Show results with animation
    resultsEl.style.display = 'block';
    resultsEl.classList.add('backtest-results-enter');
}

/**
 * Load actionable insights from backtest
 */
async function loadBacktestInsights() {
    try {
        const response = await fetch('/api/backtest/insights');
        const result = await response.json();

        if (result.success && result.data) {
            displayInsights(result.data.insights);
        }
    } catch (error) {
        console.error('Error loading insights:', error);
    }
}

/**
 * Display actionable insights in the UI
 */
function displayInsights(insights) {
    const insightsList = document.getElementById('insightsList');

    if (!insights || insights.length === 0) {
        insightsList.innerHTML = '<div class="text-center text-gray-500 text-sm py-4">No insights available. Run a backtest to generate insights.</div>';
        return;
    }

    // Sort insights by importance (danger > warning > positive > info)
    const priority = { 'danger': 1, 'warning': 2, 'positive': 3, 'info': 4 };
    insights.sort((a, b) => (priority[a.type] || 99) - (priority[b.type] || 99));

    const iconMap = {
        'positive': '✅',
        'warning': '⚠️',
        'danger': '🚨',
        'info': 'ℹ️'
    };

    insightsList.innerHTML = insights.map(insight => {
        return '<div class="insight-card insight-' + insight.type + '">' +
            '<div class="flex items-start">' +
                '<div class="insight-icon icon-' + insight.type + '">' +
                    (iconMap[insight.type] || 'ℹ️') +
                '</div>' +
                '<div class="ml-4 flex-1">' +
                    '<div class="insight-title">' + insight.title + '</div>' +
                    '<div class="insight-message">' + insight.message + '</div>' +
                    '<div class="flex items-center justify-between">' +
                        '<div class="insight-action">' + insight.action + '</div>' +
                        '<div class="insight-confidence confidence-' + insight.confidence + '">' +
                            insight.confidence.toUpperCase() +
                        '</div>' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>';
    }).join('');
}

// Initialize backtest data on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadBacktestData);
} else {
    loadBacktestData();
}
