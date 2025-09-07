// Trading Bot Dashboard JavaScript
let pnlChart, signalChart, projectionChart;
let currentSymbol = 'SUIUSDC';
let currentDays = 30;
let currentNewsPage = 1;
let newsPerPage = 10;

// PIN protection variables
let pendingPauseAction = null;
let pinAttempts = 0;
let pinBlocked = false;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadSystemStats();
    loadDashboardData();
    
    // Set up event listeners
    document.getElementById('refreshBtn').addEventListener('click', refreshDashboard);
    document.getElementById('symbolSelect').addEventListener('change', handleSymbolChange);
    document.getElementById('timeRange').addEventListener('change', handleTimeRangeChange);
    document.getElementById('logsBtn').addEventListener('click', handleLogsClick);
    document.getElementById('pauseBtn').addEventListener('click', handlePauseClick);
    
    // Load pause status on startup
    loadPauseStatus();
    
    // Auto-refresh every 30 seconds
    setInterval(refreshDashboard, 30000);
    setInterval(loadPauseStatus, 10000); // Check pause status more frequently
    
    // Load chart analysis data
    loadChartAnalysis();
    
    // Load market context data
    loadMarketContext();
    
    // Auto-refresh market context every 5 minutes
    setInterval(loadMarketContext, 300000);
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
    loadChartAnalysis();
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
        loadRecentRLDecisions(),
        fetchNews()
    ]);
}

async function fetchNews(page = 1) {
    try {
        const response = await fetch(`/api/news?page=${page}&per_page=${newsPerPage}`);
        const data = await response.json();
        const newsContainer = document.getElementById('newsContainer');
        const paginationInfo = document.getElementById('newsPaginationInfo');
        const paginationDiv = document.getElementById('newsPagination');
        const sentimentDiv = document.getElementById('marketSentiment');
        
        if (data.success && data.data.length > 0) {
            // Update news articles
            newsContainer.innerHTML = data.data.map(article => `
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-sm mb-2">
                        <a href="${article.url}" target="_blank" class="hover:underline">
                            ${article.title}
                        </a>
                    </h4>
                    <p class="text-xs text-gray-600 mb-2">${article.source.name} - ${formatDateTime(article.publishedAt)}</p>
                    <p class="text-sm text-gray-800">${article.description || 'No description available'}</p>
                </div>
            `).join('');
            
            // Update pagination info
            const { current_page, total_articles, total_pages } = data.pagination;
            paginationInfo.textContent = `Page ${current_page} of ${total_pages} (${total_articles} articles)`;
            
            // Update market sentiment (only available on first page)
            if (data.sentiment && page === 1) {
                updateMarketSentiment(data.sentiment);
            } else if (page === 1) {
                // Hide sentiment if not available
                sentimentDiv.classList.add('hidden');
            }
            
            // Update pagination controls
            updateNewsPagination(data.pagination);
            paginationDiv.style.display = total_pages > 1 ? 'flex' : 'none';
            
        } else {
            newsContainer.innerHTML = '<p class="text-gray-500">No news available.</p>';
            paginationInfo.textContent = 'No news articles';
            paginationDiv.style.display = 'none';
            sentimentDiv.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error fetching news:', error);
        document.getElementById('newsContainer').innerHTML = '<p class="text-red-500">Error loading news.</p>';
        document.getElementById('newsPaginationInfo').textContent = 'Error loading news';
        document.getElementById('marketSentiment').classList.add('hidden');
    }
}

function updateMarketSentiment(sentiment) {
    const sentimentDiv = document.getElementById('marketSentiment');
    
    if (!sentiment || sentiment.sentiment === 'Unknown') {
        sentimentDiv.classList.add('hidden');
        return;
    }
    
    // Get sentiment styling
    let sentimentClass = '';
    let sentimentIcon = '';
    
    switch (sentiment.sentiment.toLowerCase()) {
        case 'bullish':
            sentimentClass = 'bg-green-100 text-green-800 border border-green-200';
            sentimentIcon = '📈';
            break;
        case 'bearish':
            sentimentClass = 'bg-red-100 text-red-800 border border-red-200';
            sentimentIcon = '📉';
            break;
        case 'neutral':
            sentimentClass = 'bg-gray-100 text-gray-800 border border-gray-200';
            sentimentIcon = '📊';
            break;
        default:
            sentimentClass = 'bg-blue-100 text-blue-800 border border-blue-200';
            sentimentIcon = '❓';
    }
    
    // Create confidence indicator
    const confidenceStars = '★'.repeat(Math.round(sentiment.confidence / 2));
    const emptyStars = '☆'.repeat(5 - Math.round(sentiment.confidence / 2));
    
    sentimentDiv.className = `px-2 py-1 rounded text-xs font-medium ${sentimentClass}`;
    sentimentDiv.innerHTML = `
        <span class="flex items-center space-x-1">
            <span>${sentimentIcon}</span>
            <span>${sentiment.sentiment}</span>
            <span class="text-yellow-500" title="Confidence: ${sentiment.confidence}/10">${confidenceStars}${emptyStars}</span>
        </span>
    `;
    sentimentDiv.classList.remove('hidden');
    
    // Add tooltip for explanation
    if (sentiment.explanation) {
        sentimentDiv.title = sentiment.explanation;
    }
}

function updateNewsPagination(pagination) {
    const prevBtn = document.getElementById('newsPrevBtn');
    const nextBtn = document.getElementById('newsNextBtn');
    const pageNumbers = document.getElementById('newsPageNumbers');
    
    // Update Previous/Next buttons
    prevBtn.disabled = !pagination.has_previous;
    nextBtn.disabled = !pagination.has_next;
    
    // Update page numbers
    const maxVisiblePages = 5;
    const currentPage = pagination.current_page;
    const totalPages = pagination.total_pages;
    
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    // Adjust start page if we're near the end
    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    let pageNumbersHtml = '';
    
    // Add "..." if we're not starting from page 1
    if (startPage > 1) {
        pageNumbersHtml += `<button class="px-2 py-1 text-xs rounded hover:bg-gray-200" onclick="goToNewsPage(1)">1</button>`;
        if (startPage > 2) {
            pageNumbersHtml += `<span class="px-2 py-1 text-xs text-gray-500">...</span>`;
        }
    }
    
    // Add page numbers
    for (let i = startPage; i <= endPage; i++) {
        const isActive = i === currentPage;
        const btnClass = isActive 
            ? 'px-2 py-1 text-xs rounded bg-blue-500 text-white' 
            : 'px-2 py-1 text-xs rounded hover:bg-gray-200 text-gray-700';
        pageNumbersHtml += `<button class="${btnClass}" onclick="goToNewsPage(${i})">${i}</button>`;
    }
    
    // Add "..." if we're not ending at the last page
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            pageNumbersHtml += `<span class="px-2 py-1 text-xs text-gray-500">...</span>`;
        }
        pageNumbersHtml += `<button class="px-2 py-1 text-xs rounded hover:bg-gray-200" onclick="goToNewsPage(${totalPages})">${totalPages}</button>`;
    }
    
    pageNumbers.innerHTML = pageNumbersHtml;
    
    // Store current page
    currentNewsPage = currentPage;
}

function goToNewsPage(page) {
    if (page !== currentNewsPage) {
        fetchNews(page);
    }
}

function goToPreviousNewsPage() {
    if (currentNewsPage > 1) {
        fetchNews(currentNewsPage - 1);
    }
}

function goToNextNewsPage() {
    fetchNews(currentNewsPage + 1);
}

async function loadPerformanceData() {
    try {
        const response = await fetch(`/api/performance/${currentSymbol}?days=${currentDays}`);
        const data = await response.json();
        
        console.log('Performance API Response:', data); // Debug log
        
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
            
            // Update risk projections if available
            console.log('Projections data:', perf.projections); // Debug log
            if (perf.projections) {
                const proj = perf.projections;
                console.log('Setting projection values:', proj); // Debug log
                
                document.getElementById('bestCase').textContent = `$${proj.best_case_90d.toFixed(2)}`;
                document.getElementById('worstCase').textContent = `$${proj.worst_case_90d.toFixed(2)}`;
                document.getElementById('expectedRange').textContent = `$${proj.worst_case_90d.toFixed(0)} - $${proj.best_case_90d.toFixed(0)}`;
                
                // Update confidence bar
                const confidenceBar = document.getElementById('confidenceBar');
                confidenceBar.style.width = `${proj.confidence}%`;
                
                // Color coding for projections
                const bestCaseElement = document.getElementById('bestCase');
                const worstCaseElement = document.getElementById('worstCase');
                
                bestCaseElement.className = proj.best_case_90d >= 0 ? 'font-bold text-green-600' : 'font-bold text-red-600';
                worstCaseElement.className = proj.worst_case_90d >= 0 ? 'font-bold text-green-600' : 'font-bold text-red-600';
                
            } else {
                console.log('No projections data found in response'); // Debug log
                // Clear projection data if not available
                document.getElementById('bestCase').textContent = '$0.00';
                document.getElementById('worstCase').textContent = '$0.00';
                document.getElementById('expectedRange').textContent = '$0 - $0';
                document.getElementById('confidenceBar').style.width = '0%';
            }
            
        } else {
            // Clear performance data
            ['winRate', 'totalPnl', 'avgWin', 'avgLoss', 'performanceTotalTrades', 
             'winningTrades', 'losingTrades', 'maxLoss', 'riskReward'].forEach(id => {
                document.getElementById(id).textContent = '-';
            });
            
            // Clear projection data
            document.getElementById('bestCase').textContent = '$0.00';
            document.getElementById('worstCase').textContent = '$0.00';
            document.getElementById('expectedRange').textContent = '$0 - $0';
            document.getElementById('confidenceBar').style.width = '0%';
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
            
            // Update trade execution status - this will be updated by loadPauseStatus
            // but we can set a default here
            if (!document.getElementById('tradeExecution').textContent || 
                document.getElementById('tradeExecution').textContent === '-') {
                document.getElementById('tradeExecution').textContent = '🟢 ENABLED';
            }
            
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
        // Parse as UTC by properly formatting the timestamp
        const date = new Date(timeString.replace(' ', 'T') + 'Z');
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit',
            timeZone: 'Asia/Singapore'
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
    // Parse as UTC by adding 'Z' or treating as UTC
    const date = new Date(dateString.replace(' ', 'T') + 'Z');
    return date.toLocaleString('en-US', {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Singapore'
    });
}

function handleLogsClick() {
    // Open logs page in a new window/tab
    window.open('/logs', '_blank', 'width=1400,height=900,scrollbars=yes,resizable=yes');
}

async function handlePauseClick() {
    // Check if PIN attempts are blocked
    if (pinBlocked) {
        showNotification('PIN attempts blocked. Please wait before trying again.', 'error');
        return;
    }
    
    // Set pending action and show PIN modal
    pendingPauseAction = 'toggle';
    showPinModal();
}

async function loadPauseStatus() {
    try {
        const response = await fetch('/api/bot-pause-status');
        const data = await response.json();
        
        if (data.success) {
            const isPaused = data.data.is_paused;
            
            // Update pause button
            updatePauseButton(isPaused);
            
            // Update trade execution status indicator
            const tradeExecElement = document.getElementById('tradeExecution');
            if (isPaused) {
                tradeExecElement.textContent = '⏸️ PAUSED';
                tradeExecElement.className = 'text-xs font-bold text-yellow-600';
            } else {
                tradeExecElement.textContent = '🟢 ENABLED';
                tradeExecElement.className = 'text-xs font-bold text-green-600';
            }
            
        } else {
            console.error('Error loading pause status:', data.error);
        }
    } catch (error) {
        console.error('Error loading pause status:', error);
    }
}

function updatePauseButton(isPaused) {
    const pauseBtn = document.getElementById('pauseBtn');
    const pauseBtnText = document.getElementById('pauseBtnText');
    
    if (isPaused) {
        pauseBtn.className = 'bg-green-500 text-white px-3 py-1 sm:px-4 sm:py-2 rounded hover:bg-green-600 text-sm sm:text-base flex-1 sm:flex-none';
        pauseBtn.innerHTML = '▶️ <span class="hidden sm:inline" id="pauseBtnText">Resume</span>';
    } else {
        pauseBtn.className = 'bg-yellow-500 text-white px-3 py-1 sm:px-4 sm:py-2 rounded hover:bg-yellow-600 text-sm sm:text-base flex-1 sm:flex-none';
        pauseBtn.innerHTML = '⏸️ <span class="hidden sm:inline" id="pauseBtnText">Pause</span>';
    }
    
    pauseBtn.disabled = false;
}

// PIN Modal Functions
function showPinModal() {
    const modal = document.getElementById('pinModal');
    const pinInput = document.getElementById('controlPin');
    
    // Clear previous state
    pinInput.value = '';
    hideAllPinMessages();
    
    // Show modal and focus input
    modal.style.display = 'flex';
    setTimeout(() => pinInput.focus(), 100);
    
    // Add enter key support
    pinInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            submitPin();
        }
    });
    
    // Add input formatting (only numbers)
    pinInput.addEventListener('input', function(e) {
        // Only allow digits
        e.target.value = e.target.value.replace(/[^0-9]/g, '');
        
        // Clear error messages when user starts typing
        hideAllPinMessages();
    });
}

function closePinModal() {
    document.getElementById('pinModal').style.display = 'none';
    pendingPauseAction = null;
    hideAllPinMessages();
}

async function submitPin() {
    const pin = document.getElementById('controlPin').value.trim();
    const submitBtn = document.getElementById('submitPinBtn');
    
    // Validate PIN format
    if (!pin || pin.length !== 6 || !/^\d{6}$/.test(pin)) {
        showPinError('PIN must be exactly 6 digits');
        return;
    }
    
    if (!pendingPauseAction) {
        showPinError('No pending action');
        return;
    }
    
    // Disable submit button during request
    submitBtn.disabled = true;
    submitBtn.textContent = 'Verifying...';
    
    try {
        const response = await fetch('/api/bot-pause', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: pendingPauseAction,
                pin: pin
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // PIN validated successfully
            showPinSuccess('PIN validated! Executing action...');
            
            setTimeout(() => {
                closePinModal();
                showNotification(data.message, 'success');
                
                // Update UI
                updatePauseButton(data.is_paused);
                loadPauseStatus();
                
                // Reset attempt counter
                pinAttempts = 0;
                pinBlocked = false;
            }, 1000);
            
        } else {
            // PIN validation failed
            if (response.status === 429 || data.blocked) {
                // Rate limited/blocked
                showPinBlocked(data.message);
                pinBlocked = true;
                
                // Auto-close modal after showing blocked message
                setTimeout(() => {
                    closePinModal();
                    showNotification('PIN attempts blocked for 15 minutes', 'error');
                }, 2000);
                
                // Reset block after 15 minutes
                setTimeout(() => {
                    pinBlocked = false;
                    pinAttempts = 0;
                }, 15 * 60 * 1000);
                
            } else {
                // Invalid PIN
                pinAttempts++;
                showPinError(data.message);
                
                // Clear PIN input
                document.getElementById('controlPin').value = '';
                document.getElementById('controlPin').focus();
                
                if (pinAttempts >= 3) {
                    showPinBlocked('Too many failed attempts. Blocked for 15 minutes.');
                    pinBlocked = true;
                    
                    setTimeout(() => {
                        closePinModal();
                        showNotification('PIN attempts blocked for 15 minutes', 'error');
                    }, 2000);
                    
                    // Reset after 15 minutes
                    setTimeout(() => {
                        pinBlocked = false;
                        pinAttempts = 0;
                    }, 15 * 60 * 1000);
                }
            }
        }
        
    } catch (error) {
        console.error('PIN submission error:', error);
        showPinError('Network error. Please try again.');
    } finally {
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit';
    }
}

function showPinError(message) {
    hideAllPinMessages();
    const errorDiv = document.getElementById('pinError');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function showPinBlocked(message) {
    hideAllPinMessages();
    const blockedDiv = document.getElementById('pinBlocked');
    blockedDiv.textContent = message;
    blockedDiv.style.display = 'block';
}

function showPinSuccess(message) {
    hideAllPinMessages();
    const successDiv = document.getElementById('pinSuccess');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
}

function hideAllPinMessages() {
    document.getElementById('pinError').style.display = 'none';
    document.getElementById('pinBlocked').style.display = 'none';
    document.getElementById('pinSuccess').style.display = 'none';
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-4 py-2 rounded shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        'bg-blue-500 text-white'
    }`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Chart Analysis Functions
function loadChartAnalysis() {
    fetch('/api/chart-analysis')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayChartAnalysis(data.data);
                if (data.chart_available) {
                    loadChartImage();
                }
            } else {
                showChartAnalysisError(data.message || 'No chart analysis data available');
            }
        })
        .catch(error => {
            console.error('Error loading chart analysis:', error);
            showChartAnalysisError('Failed to load chart analysis');
        });
}

function loadChartImage() {
    const chartImage = document.getElementById('chartImage');
    const chartLoading = document.getElementById('chartLoading');
    
    // Add timestamp to prevent caching
    const imageUrl = '/api/chart-image?' + new Date().getTime();
    
    chartImage.onload = function() {
        chartLoading.style.display = 'none';
        chartImage.style.display = 'block';
    };
    
    chartImage.onerror = function() {
        showChartAnalysisError('Failed to load chart image');
    };
    
    chartImage.src = imageUrl;
}

function displayChartAnalysis(data) {
    try {
        // Update basic metrics
        const recommendation = data.ai_analysis?.recommendation || 'N/A';
        const confidence = data.ai_analysis?.confidence || 'N/A';
        const currentPrice = data.market_data?.price || 'N/A';
        const priceChange = data.market_data?.change_24h || 'N/A';
        
        document.getElementById('recommendation').textContent = recommendation;
        document.getElementById('confidence').textContent = confidence;
        document.getElementById('currentPrice').textContent = currentPrice !== 'N/A' ? `$${currentPrice.toFixed(4)}` : 'N/A';
        document.getElementById('priceChange').textContent = priceChange !== 'N/A' ? `${priceChange.toFixed(2)}%` : 'N/A';
        
        // Update recommendation card color based on recommendation
        const recommendationCard = document.getElementById('recommendationCard');
        recommendationCard.className = 'metric ' + getRecommendationClass(recommendation);
        
        // Update price change color
        const priceChangeElement = document.getElementById('priceChange');
        if (priceChange !== 'N/A') {
            priceChangeElement.parentElement.className = 'metric ' + (priceChange >= 0 ? 'metric-positive' : 'metric-negative');
        }
        
        // Display observations
        const observations = data.ai_analysis?.key_observations || [];
        const observationsList = document.getElementById('observations');
        observationsList.innerHTML = '';
        observations.forEach(obs => {
            const li = document.createElement('li');
            li.textContent = obs;
            li.className = 'flex items-start';
            li.innerHTML = `<span class="mr-2">•</span><span>${obs}</span>`;
            observationsList.appendChild(li);
        });
        
        // Display risk factors
        const riskFactors = data.ai_analysis?.risk_factors || [];
        const riskList = document.getElementById('riskFactors');
        riskList.innerHTML = '';
        riskFactors.forEach(risk => {
            const li = document.createElement('li');
            li.textContent = risk;
            li.className = 'flex items-start';
            li.innerHTML = `<span class="mr-2">•</span><span>${risk}</span>`;
            riskList.appendChild(li);
        });
        
        // Display AI reasoning
        const reasoning = data.ai_analysis?.reasoning || 'No analysis available';
        document.getElementById('reasoning').textContent = reasoning;
        
        // Update timestamp
        const analysisTime = data.analysis_time || 'Unknown';
        const formattedTime = formatTimestamp(analysisTime);
        document.getElementById('analysisTimestamp').textContent = `Last updated: ${formattedTime}`;
        
        // Show all sections
        document.getElementById('analysisResults').style.display = 'grid';
        document.getElementById('observationsSection').style.display = observations.length > 0 ? 'block' : 'none';
        document.getElementById('riskSection').style.display = riskFactors.length > 0 ? 'block' : 'none';
        document.getElementById('reasoningSection').style.display = 'block';
        
    } catch (error) {
        console.error('Error displaying chart analysis:', error);
        showChartAnalysisError('Error displaying analysis data');
    }
}

function getRecommendationClass(recommendation) {
    switch (recommendation?.toUpperCase()) {
        case 'BUY':
            return 'metric-positive';
        case 'SELL':
            return 'metric-negative';
        case 'HOLD':
            return 'metric-neutral';
        default:
            return 'metric-neutral';
    }
}

function showChartAnalysisError(message) {
    const chartLoading = document.getElementById('chartLoading');
    chartLoading.innerHTML = `<div class="text-red-500">${message}</div>`;
    document.getElementById('chartImage').style.display = 'none';
}

function formatTimestamp(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString();
    } catch (error) {
        return timestamp;
    }
}

async function loadMarketContext() {
    try {
        console.log('Loading market context...');
        const response = await fetch('/api/market-context');
        const result = await response.json();
        
        if (result.success && result.data) {
            const data = result.data;
            
            // Update BTC data
            document.getElementById('btcPrice').textContent = `$${formatNumber(data.btc_price)}`;
            const btcChange = data.btc_change_24h;
            const btcChangeEl = document.getElementById('btcChange');
            btcChangeEl.textContent = `${btcChange >= 0 ? '+' : ''}${btcChange.toFixed(2)}%`;
            btcChangeEl.className = btcChange >= 0 ? 'text-green-600' : 'text-red-600';
            
            // Update ETH data
            document.getElementById('ethPrice').textContent = `$${formatNumber(data.eth_price)}`;
            const ethChange = data.eth_change_24h;
            const ethChangeEl = document.getElementById('ethChange');
            ethChangeEl.textContent = `${ethChange >= 0 ? '+' : ''}${ethChange.toFixed(2)}%`;
            ethChangeEl.className = ethChange >= 0 ? 'text-green-600' : 'text-red-600';
            
            // Update BTC dominance
            document.getElementById('btcDominance').textContent = `${data.btc_dominance.toFixed(1)}%`;
            
            // Update Fear & Greed Index
            const fgIndex = data.fear_greed_index;
            const fgEl = document.getElementById('fearGreedIndex');
            fgEl.textContent = fgIndex;
            
            // Color code Fear & Greed Index
            if (fgIndex < 25) {
                fgEl.className = 'text-lg font-bold text-red-600';
            } else if (fgIndex > 75) {
                fgEl.className = 'text-lg font-bold text-green-600';
            } else {
                fgEl.className = 'text-lg font-bold text-yellow-600';
            }
            
            // Update cross-asset signals
            document.getElementById('marketTrend').textContent = capitalizeFirst(data.market_trend);
            
            if (data.cross_asset_signal) {
                document.getElementById('btcTrend').textContent = capitalizeFirst(data.cross_asset_signal.btc_trend.replace('_', ' '));
                document.getElementById('marketRegime').textContent = capitalizeFirst(data.cross_asset_signal.regime_signal.replace('_', ' '));
            }
            
            console.log('Market context loaded successfully');
        } else {
            console.warn('Market context data not available:', result.message);
            // Set fallback values
            document.getElementById('btcPrice').textContent = 'N/A';
            document.getElementById('ethPrice').textContent = 'N/A';
            document.getElementById('btcDominance').textContent = 'N/A';
            document.getElementById('fearGreedIndex').textContent = 'N/A';
            document.getElementById('marketTrend').textContent = 'N/A';
            document.getElementById('btcTrend').textContent = 'N/A';
            document.getElementById('marketRegime').textContent = 'N/A';
        }
    } catch (error) {
        console.error('Error loading market context:', error);
        // Set error indicators
        ['btcPrice', 'ethPrice', 'btcDominance', 'fearGreedIndex', 'marketTrend', 'btcTrend', 'marketRegime'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = 'Error';
        });
    }
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    } else if (num >= 1) {
        return num.toFixed(0);
    } else {
        return num.toFixed(4);
    }
}

function capitalizeFirst(str) {
    if (!str) return str;
    return str.charAt(0).toUpperCase() + str.slice(1);
}