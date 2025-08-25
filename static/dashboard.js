// Trading Bot Dashboard JavaScript
let pnlChart, signalChart, projectionChart;
let currentSymbol = 'SUIUSDC';
let currentDays = 30;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadSystemStats();
    loadDashboardData();
    
    // Set up event listeners
    document.getElementById('refreshBtn').addEventListener('click', refreshDashboard);
    document.getElementById('symbolSelect').addEventListener('change', handleSymbolChange);
    document.getElementById('timeRange').addEventListener('change', handleTimeRangeChange);
    
    // Auto-refresh every 30 seconds
    setInterval(refreshDashboard, 30000);
});

function initializeCharts() {
    // Initialize PnL Chart
    const pnlCtx = document.getElementById('pnlChart').getContext('2d');
    pnlChart = new Chart(pnlCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Cumulative PnL ($)',
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'PnL ($)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // Initialize Signal Chart
    const signalCtx = document.getElementById('signalChart').getContext('2d');
    signalChart = new Chart(signalCtx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Buy Signals',
                    data: [],
                    backgroundColor: 'rgba(34, 197, 94, 0.8)',
                    borderColor: 'rgb(34, 197, 94)',
                    pointRadius: 6
                },
                {
                    label: 'Sell Signals',
                    data: [],
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: 'rgb(239, 68, 68)',
                    pointRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Signal Strength'
                    },
                    min: 0,
                    max: 10
                }
            }
        }
    });
    
    // Initialize Projection Chart
    const projectionCtx = document.getElementById('projectionChart').getContext('2d');
    projectionChart = new Chart(projectionCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Days'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Account Balance ($)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Projected Account Balance'
                }
            }
        }
    });
}

function handleSymbolChange(event) {
    currentSymbol = event.target.value;
    loadDashboardData();
}

function handleTimeRangeChange(event) {
    currentDays = parseInt(event.target.value);
    loadDashboardData();
}

function refreshDashboard() {
    loadSystemStats();
    loadDashboardData();
}

async function loadSystemStats() {
    try {
        const response = await fetch('/api/system-stats');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalSignals').textContent = data.data.total_signals || 0;
            document.getElementById('totalTrades').textContent = data.data.total_trades || 0;
            document.getElementById('openTrades').textContent = data.data.open_trades || 0;
            document.getElementById('lastSignal').textContent = 
                data.data.last_signal ? formatDateTime(data.data.last_signal) : 'No signals';
            
            // Update symbol dropdown
            const symbolSelect = document.getElementById('symbolSelect');
            const currentValue = symbolSelect.value;
            symbolSelect.innerHTML = '';
            
            if (data.data.symbols && data.data.symbols.length > 0) {
                data.data.symbols.forEach(symbol => {
                    const option = document.createElement('option');
                    option.value = symbol;
                    option.textContent = symbol;
                    symbolSelect.appendChild(option);
                });
                symbolSelect.value = currentValue;
            } else {
                const option = document.createElement('option');
                option.value = 'SUIUSDC';
                option.textContent = 'SUIUSDC';
                symbolSelect.appendChild(option);
            }
        }
    } catch (error) {
        console.error('Error loading system stats:', error);
    }
}

async function loadDashboardData() {
    await Promise.all([
        loadPerformanceData(),
        loadProjectedBalance(),
        loadRLBotStatus(),
        loadOpenPositions(),
        loadSignalsData(),
        loadTradesData(),
        loadChartData(),
        loadRecentRLDecisions()
    ]);
}

async function loadPerformanceData() {
    try {
        const response = await fetch(`/api/performance/${currentSymbol}?days=${currentDays}`);
        const data = await response.json();
        
        if (data.success && data.data.total_trades > 0) {
            const perf = data.data;
            
            document.getElementById('winRate').textContent = `${perf.win_rate.toFixed(2)}%`;
            document.getElementById('totalPnl').textContent = `$${perf.total_pnl.toFixed(2)}`;
            document.getElementById('avgWin').textContent = `$${perf.avg_win.toFixed(2)}`;
            document.getElementById('avgLoss').textContent = `$${perf.avg_loss.toFixed(2)}`;
            document.getElementById('performanceTotalTrades').textContent = perf.total_trades;
            document.getElementById('winningTrades').textContent = perf.winning_trades;
            document.getElementById('losingTrades').textContent = perf.losing_trades;
            document.getElementById('maxLoss').textContent = `$${perf.max_loss.toFixed(2)}`;
            
            // Calculate risk-reward ratio
            if (perf.avg_loss !== 0) {
                const rr = Math.abs(perf.avg_win / perf.avg_loss);
                document.getElementById('riskReward').textContent = `1:${rr.toFixed(2)}`;
            } else {
                document.getElementById('riskReward').textContent = 'N/A';
            }
            
            // Update PnL color
            const pnlElement = document.getElementById('totalPnl');
            pnlElement.className = perf.total_pnl >= 0 ? 'font-bold text-green-600' : 'font-bold text-red-600';
            
        } else {
            // Clear performance data
            ['winRate', 'totalPnl', 'avgWin', 'avgLoss', 'performanceTotalTrades', 
             'winningTrades', 'losingTrades', 'maxLoss', 'riskReward'].forEach(id => {
                document.getElementById(id).textContent = '-';
            });
        }
    } catch (error) {
        console.error('Error loading performance data:', error);
    }
}

async function loadProjectedBalance() {
    try {
        const response = await fetch(`/api/projected-balance/${currentSymbol}?days=${currentDays}&projection_days=30`);
        const data = await response.json();
        
        if (data.success && data.data) {
            const projData = data.data;
            
            // Update current balance
            document.getElementById('currentBalance').textContent = `$${projData.current_balance.toFixed(2)}`;
            
            // Update projections
            const scenarios = {};
            projData.projections.forEach(proj => {
                scenarios[proj.scenario] = proj.projections[proj.projections.length - 1]; // Last day (30 days)
            });
            
            // Update UI elements
            if (scenarios.conservative) {
                document.getElementById('conservativeProjection').textContent = `$${scenarios.conservative.balance}`;
            }
            if (scenarios.realistic) {
                document.getElementById('realisticProjection').textContent = `$${scenarios.realistic.balance}`;
            }
            if (scenarios.rl_enhanced) {
                document.getElementById('rlProjection').textContent = `$${scenarios.rl_enhanced.balance}`;
            } else {
                document.getElementById('rlProjection').textContent = 'N/A';
            }
            
            // Update projection chart
            updateProjectionChart(projData);
            
            // Load 90-day projections for risk assessment
            loadLongTermProjections();
            
            // Update note
            document.getElementById('projectionNote').textContent = 
                `Based on ${projData.historical_period_days} days of trading data`;
            
        } else {
            // Handle no data case
            document.getElementById('currentBalance').textContent = '$0.00';
            document.getElementById('conservativeProjection').textContent = 'Insufficient data';
            document.getElementById('realisticProjection').textContent = 'Insufficient data';
            document.getElementById('rlProjection').textContent = 'Insufficient data';
        }
        
    } catch (error) {
        console.error('Error loading projected balance:', error);
        document.getElementById('currentBalance').textContent = 'Error';
        document.getElementById('conservativeProjection').textContent = 'Error';
        document.getElementById('realisticProjection').textContent = 'Error';
        document.getElementById('rlProjection').textContent = 'Error';
    }
}

function updateProjectionChart(projData) {
    const datasets = [];
    const colors = {
        conservative: '#10b981', // green
        realistic: '#3b82f6',    // blue
        optimistic: '#f59e0b',   // amber
        pessimistic: '#ef4444',  // red
        rl_enhanced: '#8b5cf6'   // purple
    };
    
    projData.projections.forEach(scenario => {
        if (scenario.projections.length > 0) {
            datasets.push({
                label: scenario.scenario.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
                data: scenario.projections.map(p => p.balance),
                borderColor: colors[scenario.scenario] || '#6b7280',
                backgroundColor: colors[scenario.scenario] || '#6b7280',
                fill: false,
                tension: 0.1
            });
        }
    });
    
    // Create labels for days
    const days = projData.projections[0] ? projData.projections[0].projections.map(p => p.day) : [];
    
    projectionChart.data.labels = days;
    projectionChart.data.datasets = datasets;
    projectionChart.update();
}

async function loadLongTermProjections() {
    try {
        const response = await fetch(`/api/projected-balance/${currentSymbol}?days=${currentDays}&projection_days=90`);
        const data = await response.json();
        
        if (data.success && data.data) {
            const projections = data.data.projections;
            
            let bestCase = 0;
            let worstCase = Infinity;
            let realistic = 0;
            
            projections.forEach(scenario => {
                const finalBalance = scenario.projections[scenario.projections.length - 1].balance;
                if (scenario.scenario === 'optimistic') bestCase = finalBalance;
                if (scenario.scenario === 'pessimistic') worstCase = finalBalance;
                if (scenario.scenario === 'realistic') realistic = finalBalance;
            });
            
            document.getElementById('bestCase').textContent = `$${bestCase.toFixed(2)}`;
            document.getElementById('worstCase').textContent = `$${worstCase.toFixed(2)}`;
            document.getElementById('expectedRange').textContent = 
                `$${worstCase.toFixed(0)} - $${bestCase.toFixed(0)}`;
            
            // Calculate confidence based on spread
            const spread = bestCase - worstCase;
            const confidence = Math.max(0, Math.min(100, 100 - (spread / bestCase * 100)));
            
            document.getElementById('confidenceBar').style.width = `${confidence}%`;
            document.getElementById('confidenceText').textContent = `${confidence.toFixed(0)}% confidence`;
            
        }
    } catch (error) {
        console.error('Error loading long term projections:', error);
    }
}

async function loadRLBotStatus() {
    try {
        const response = await fetch('/api/rl-bot-status');
        const data = await response.json();
        
        if (data.success && data.data) {
            const botData = data.data;
            
            // Update bot status
            const statusElement = document.getElementById('rlBotStatus');
            if (botData.running) {
                statusElement.textContent = '🟢 RUNNING';
                statusElement.className = 'text-sm font-bold text-green-600';
            } else {
                statusElement.textContent = '🔴 STOPPED';
                statusElement.className = 'text-sm font-bold text-red-600';
            }
            
            document.getElementById('rlBotPid').textContent = botData.pid || 'N/A';
            document.getElementById('rlBotLastUpdate').textContent = 
                botData.last_update ? formatTime(botData.last_update) : 'N/A';
            
            // Update RL decision info
            if (botData.rl_decision) {
                const decision = botData.rl_decision;
                
                // Original signal
                const origSignal = decision.signal;
                document.getElementById('originalSignal').textContent = 
                    origSignal === 1 ? '🟢 BUY' : origSignal === -1 ? '🔴 SELL' : '⚪ HOLD';
                
                // RL Action
                document.getElementById('rlAction').textContent = decision.reasons[0];
                
                // Final decision
                const finalSignal = decision.signal;
                document.getElementById('finalDecision').textContent = 
                    finalSignal === 1 ? '🟢 BUY' : finalSignal === -1 ? '🔴 SELL' : '⚪ HOLD';
                
                // Reason
                document.getElementById('rlReason').textContent = decision.reasons.join(', ');
            } else {
                document.getElementById('originalSignal').textContent = 'N/A';
                document.getElementById('rlAction').textContent = 'N/A';
                document.getElementById('finalDecision').textContent = 'N/A';
                document.getElementById('rlReason').textContent = 'No recent RL decisions available';
            }
            
            // Update market data
            if (botData.market_data) {
                const market = botData.market_data;
                document.getElementById('livePrice').textContent = `${market.price.toFixed(4)}`;
                document.getElementById('liveRSI').textContent = market.rsi.toFixed(1);
                document.getElementById('liveVWAP').textContent = `${market.vwap.toFixed(4)}`;
            } else {
                document.getElementById('livePrice').textContent = 'N/A';
                document.getElementById('liveRSI').textContent = 'N/A';
                document.getElementById('liveVWAP').textContent = 'N/A';
            }
            
            // Update current signal
            if (botData.current_signal) {
                const signal = botData.current_signal;
                const signalText = signal.action;
                const signalColor = signalText === 'BUY' ? 'text-green-600' : 
                                  signalText === 'SELL' ? 'text-red-600' : 'text-gray-600';
                document.getElementById('liveSignal').innerHTML = 
                    `<span class="${signalColor}">${signalText} (${signal.strength})</span>`;
            } else {
                document.getElementById('liveSignal').textContent = 'N/A';
            }
            
            // Update live position
            const positionContainer = document.getElementById('livePosition');
            if (botData.position_info && botData.position_info.status !== 'No position') {
                const pos = botData.position_info;
                const sideColor = pos.side === 'LONG' ? 'text-green-600' : 'text-red-600';
                const pnlColor = pos.pnl && parseFloat(pos.pnl) >= 0 ? 'text-green-600' : 'text-red-600';
                
                positionContainer.innerHTML = `
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-gray-600">Side:</span>
                        <span class="text-sm font-bold ${sideColor}">${pos.side}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-gray-600">Size:</span>
                        <span class="text-sm font-bold">${pos.size}</span>
                    </div>
                    ${pos.pnl ? `
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-gray-600">PnL:</span>
                        <span class="text-sm font-bold ${pnlColor}">${pos.pnl} (${pos.pnl_percentage})</span>
                    </div>` : ''}
                `;
            } else {
                positionContainer.innerHTML = '<div class="text-center text-gray-500 text-sm">No open position</div>';
            }

        } else {
            // Handle error case
            document.getElementById('rlBotStatus').textContent = '❌ ERROR';
            document.getElementById('rlBotStatus').className = 'text-sm font-bold text-red-600';
        }
        
    } catch (error) {
        console.error('Error loading RL bot status:', error);
        document.getElementById('rlBotStatus').textContent = '❌ ERROR';
        document.getElementById('rlBotStatus').className = 'text-sm font-bold text-red-600';
    }
}

async function loadRecentRLDecisions() {
    try {
        const response = await fetch(`/api/rl-decisions/${currentSymbol}?limit=5`);
        const data = await response.json();
        const tbody = document.getElementById('recentDecisions');
        if (data.success && data.data.length > 0) {
            tbody.innerHTML = data.data.map(decision => `
                <tr class="border-b">
                    <td class="px-3 py-2 text-xs">${formatTime(decision.timestamp)}</td>
                    <td class="px-3 py-2 text-xs">
                        ${decision.signal === 1 ? '🟢 BUY' : 
                          decision.signal === -1 ? '🔴 SELL' : '⚪ HOLD'}
                    </td>
                    <td class="px-3 py-2 text-xs mobile-hide">${decision.reasons[0]}</td>
                    <td class="px-3 py-2 text-xs">
                        ${decision.signal === 1 ? '🟢 BUY' : 
                          decision.signal === -1 ? '🔴 SELL' : '⚪ HOLD'}
                    </td>
                    <td class="px-3 py-2 text-xs mobile-hide">${decision.strength}</td>
                    <td class="px-3 py-2 text-xs max-w-xs truncate" title="${decision.reasons.join(', ')}">
                        ${decision.reasons.join(', ')}
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="px-3 py-4 text-center text-gray-500">No recent RL decisions available</td></tr>';
        }
    } catch (error) {
        console.error('Error loading recent RL decisions:', error);
    }
}

function formatTime(timeString) {
    try {
        if (!timeString) return 'N/A';
        const date = new Date(timeString + 'Z'); // Assume UTC
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (e) {
        return timeString;
    }
}

async function loadOpenPositions() {
    try {
        const response = await fetch(`/api/open-positions/${currentSymbol}`);
        const data = await response.json();
        
        const container = document.getElementById('openPositions');
        
        if (data.success && data.data.database_positions && data.data.database_positions.length > 0) {
            const positions = data.data.database_positions;
            container.innerHTML = positions.map(trade => `
                <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                        <span class="font-semibold ${trade.side === 'BUY' ? 'text-green-600' : 'text-red-600'}">
                            ${trade.side}
                        </span>
                        <span class="text-gray-600">${trade.quantity.toFixed(4)}</span>
                    </div>
                    <div class="text-right">
                        <div class="font-semibold">$${trade.entry_price.toFixed(4)}</div>
                        <div class="text-xs text-gray-500">${formatDateTime(trade.timestamp)}</div>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="text-center text-gray-500">No open positions</div>';
        }
    } catch (error) {
        console.error('Error loading open positions:', error);
    }
}

async function loadSignalsData() {
    try {
        const response = await fetch(`/api/signals/${currentSymbol}?limit=10`);
        const data = await response.json();
        
        const tbody = document.getElementById('signalsTable');
        
        if (data.success && data.data.length > 0) {
            tbody.innerHTML = data.data.map(signal => {
                const signalText = signal.signal === 1 ? 'BUY' : signal.signal === -1 ? 'SELL' : 'HOLD';
                const signalClass = signal.signal === 1 ? 'signal-buy' : 
                                  signal.signal === -1 ? 'signal-sell' : 'signal-hold';
                
                return `
                    <tr>
                        <td class="px-3 py-2 text-xs">${formatDateTime(signal.timestamp)}</td>
                        <td class="px-3 py-2">
                            <span class="${signalClass}">${signalText}</span>
                        </td>
                        <td class="px-3 py-2 font-semibold">${signal.strength}</td>
                        <td class="px-3 py-2">$${signal.price.toFixed(4)}</td>
                        <td class="px-3 py-2">
                            <span class="${signal.executed ? 'status-closed' : 'status-open'}">
                                ${signal.executed ? 'Executed' : 'Pending'}
                            </span>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-500">No signals found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading signals data:', error);
    }
}

async function loadTradesData() {
    try {
        const response = await fetch(`/api/trades/${currentSymbol}?limit=10`);
        const data = await response.json();
        
        const tbody = document.getElementById('tradesTable');
        
        if (data.success && data.data.length > 0) {
            tbody.innerHTML = data.data.map(trade => {
                const pnlText = trade.pnl !== null ? `$${trade.pnl.toFixed(2)}` : 'Open';
                const pnlClass = trade.pnl > 0 ? 'text-green-600 font-semibold' : 
                                trade.pnl < 0 ? 'text-red-600 font-semibold' : '';
                
                return `
                    <tr>
                        <td class="px-3 py-2 text-xs">${formatDateTime(trade.timestamp)}</td>
                        <td class="px-3 py-2">
                            <span class="${trade.side === 'BUY' ? 'text-green-600' : 'text-red-600'} font-semibold">
                                ${trade.side}
                            </span>
                        </td>
                        <td class="px-3 py-2">$${trade.entry_price.toFixed(4)}</td>
                        <td class="px-3 py-2 ${pnlClass}">${pnlText}</td>
                        <td class="px-3 py-2">
                            <span class="${trade.status === 'CLOSED' ? 'status-closed' : 'status-open'}">
                                ${trade.status}
                            </span>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-500">No trades found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading trades data:', error);
    }
}

async function loadChartData() {
    try {
        const response = await fetch(`/api/chart-data/${currentSymbol}?days=${currentDays}`);
        const data = await response.json();
        
        if (data.success) {
            // Update PnL Chart
            const trades = data.data.trades || [];
            const pnlLabels = trades.map(trade => formatDateTime(trade.timestamp));
            const pnlData = trades.map(trade => trade.cumulative_pnl);
            
            pnlChart.data.labels = pnlLabels;
            pnlChart.data.datasets[0].data = pnlData;
            pnlChart.update();
            
            // Update Signal Chart
            const signals = data.data.signals || [];
            const buySignals = signals.filter(s => s.signal === 1).map(s => ({
                x: new Date(s.timestamp).getTime(),
                y: s.strength
            }));
            const sellSignals = signals.filter(s => s.signal === -1).map(s => ({
                x: new Date(s.timestamp).getTime(), 
                y: s.strength
            }));
            
            signalChart.data.datasets[0].data = buySignals;
            signalChart.data.datasets[1].data = sellSignals;
            signalChart.update();
        }
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}