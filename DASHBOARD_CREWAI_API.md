# CrewAI Dashboard API Endpoints

## Overview

7 new API endpoints have been added to the web dashboard (`web_dashboard.py`) to provide complete visibility into the CrewAI Multi-Agent System.

## New API Endpoints

### 1. Circuit Breaker Status
**Endpoint:** `GET /api/crewai/circuit-breaker-status`

**Purpose:** Get real-time circuit breaker status

**Response:**
```json
{
  "success": true,
  "data": {
    "state": "SAFE",  // SAFE, WARNING, TRIGGERED, RECOVERING
    "is_safe": true,
    "trigger_reason": null,
    "btc_change_1h": -2.5,
    "btc_change_4h": -1.2,
    "eth_change_1h": -1.8,
    "eth_change_4h": -0.9,
    "timestamp": "2025-10-13T14:30:00"
  }
}
```

**Usage:**
```javascript
fetch('/api/crewai/circuit-breaker-status')
  .then(r => r.json())
  .then(data => {
    console.log('Circuit Breaker:', data.data.state);
    if (!data.data.is_safe) {
      alert('Trading halted: ' + data.data.trigger_reason);
    }
  });
```

### 2. Spike Detections
**Endpoint:** `GET /api/crewai/spike-detections?limit=20&hours=24`

**Purpose:** Get recent price spike detections

**Query Parameters:**
- `limit` (default: 20) - Max number of spikes to return
- `hours` (default: 24) - Time window in hours

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "symbol": "SUIUSDC",
      "detection_type": "PRICE_SPIKE",
      "spike_percent": 5.2,
      "timeframe_minutes": 5,
      "volume_spike_multiplier": 3.5,
      "price_before": 3.42,
      "price_after": 3.60,
      "agent_analysis": "Strong bullish momentum detected",
      "timestamp": "2025-10-13T14:25:00"
    }
  ]
}
```

### 3. AI Agent Decisions
**Endpoint:** `GET /api/crewai/agent-decisions?limit=50&agent=Market%20Guardian`

**Purpose:** Get complete audit trail of AI agent decisions

**Query Parameters:**
- `limit` (default: 50) - Max number of decisions
- `agent` (optional) - Filter by agent name

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "agent_name": "Market Guardian",
      "agent_type": "circuit_breaker",
      "decision": "SAFE",
      "reasoning": "Market conditions stable, no crash detected",
      "confidence_score": 0.95,
      "context": "{\"btc_1h\": -1.2, \"eth_1h\": -0.8}",
      "timestamp": "2025-10-13T14:30:00"
    }
  ]
}
```

### 4. Spike Trades
**Endpoint:** `GET /api/crewai/spike-trades?limit=20&status=OPEN`

**Purpose:** Get trades executed on spike signals

**Query Parameters:**
- `limit` (default: 20) - Max number of trades
- `status` (optional) - OPEN or CLOSED

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "spike_detection_id": 1,
      "symbol": "SUIUSDC",
      "side": "BUY",
      "quantity": 100.0,
      "entry_price": 3.60,
      "exit_price": null,
      "pnl": null,
      "status": "OPEN",
      "entry_timestamp": "2025-10-13T14:26:00",
      "exit_timestamp": null
    }
  ]
}
```

### 5. CrewAI Statistics
**Endpoint:** `GET /api/crewai/statistics`

**Purpose:** Get comprehensive system statistics

**Response:**
```json
{
  "success": true,
  "data": {
    "trades_blocked_by_circuit_breaker": 5,
    "spikes_detected": 12,
    "agent_decisions_made": 287,
    "circuit_breaker_triggers": 1,
    "circuit_breaker_state": "SAFE",
    "agent_system_active": true,
    "monitoring_active": true
  }
}
```

### 6. Agent Status
**Endpoint:** `GET /api/crewai/agent-status`

**Purpose:** Get status of all 5 AI agents

**Response:**
```json
{
  "success": true,
  "data": {
    "system_running": true,
    "agents": {
      "market_guardian": {
        "last_activity": "2025-10-13T14:30:00",
        "decisions_24h": 1440
      },
      "market_scanner": {
        "last_activity": "2025-10-13T14:25:00",
        "decisions_24h": 288
      },
      "context_analyzer": {
        "last_activity": "2025-10-13T14:20:00",
        "decisions_24h": 288
      },
      "risk_assessment": {
        "last_activity": "2025-10-13T14:15:00",
        "decisions_24h": 50
      },
      "strategy_executor": {
        "last_activity": "2025-10-13T14:10:00",
        "decisions_24h": 45
      }
    }
  }
}
```

### 7. Force Circuit Breaker Check
**Endpoint:** `POST /api/crewai/force-check`

**Purpose:** Manually trigger circuit breaker check

**Request Body:**
```json
{
  "pin": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "checked",
    "safe": true,
    "result": "Market conditions normal"
  },
  "message": "Circuit breaker check completed"
}
```

**Security:** Requires 6-digit PIN authentication

## Integration Examples

### React/Vue.js Component Example

```javascript
// Circuit Breaker Status Component
import React, { useState, useEffect } from 'react';

function CircuitBreakerStatus() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/crewai/circuit-breaker-status');
        const data = await res.json();
        setStatus(data.data);
      } catch (error) {
        console.error('Error fetching status:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // Update every 10s

    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading...</div>;

  const stateColors = {
    SAFE: 'green',
    WARNING: 'yellow',
    TRIGGERED: 'red',
    RECOVERING: 'orange'
  };

  return (
    <div className="circuit-breaker-panel">
      <h3>Circuit Breaker Status</h3>
      <div className="status-badge" style={{
        backgroundColor: stateColors[status.state]
      }}>
        {status.state}
      </div>
      {!status.is_safe && (
        <div className="alert">
          ⚠️ Trading Halted: {status.trigger_reason}
        </div>
      )}
      <div className="market-conditions">
        <div>BTC 1h: {status.btc_change_1h}%</div>
        <div>BTC 4h: {status.btc_change_4h}%</div>
        <div>ETH 1h: {status.eth_change_1h}%</div>
        <div>ETH 4h: {status.eth_change_4h}%</div>
      </div>
    </div>
  );
}
```

### jQuery Example

```javascript
// Load agent decisions
function loadAgentDecisions() {
  $.ajax({
    url: '/api/crewai/agent-decisions',
    data: { limit: 10 },
    success: function(response) {
      if (response.success) {
        const decisions = response.data;
        let html = '<div class="agent-decisions">';

        decisions.forEach(decision => {
          html += `
            <div class="decision-card">
              <div class="agent-name">${decision.agent_name}</div>
              <div class="decision">${decision.decision}</div>
              <div class="reasoning">${decision.reasoning}</div>
              <div class="timestamp">${decision.timestamp}</div>
            </div>
          `;
        });

        html += '</div>';
        $('#agent-decisions-container').html(html);
      }
    }
  });
}

// Refresh every 30 seconds
setInterval(loadAgentDecisions, 30000);
loadAgentDecisions();
```

### Vanilla JavaScript Example

```javascript
// Real-time spike detection monitoring
async function monitorSpikes() {
  try {
    const response = await fetch('/api/crewai/spike-detections?hours=1');
    const data = await response.json();

    if (data.success && data.data.length > 0) {
      const latestSpike = data.data[0];

      showNotification({
        title: '📈 Spike Detected!',
        message: `${latestSpike.symbol}: +${latestSpike.spike_percent}% in ${latestSpike.timeframe_minutes}min`,
        type: 'success'
      });
    }
  } catch (error) {
    console.error('Error monitoring spikes:', error);
  }
}

// Check every 60 seconds
setInterval(monitorSpikes, 60000);
```

## Dashboard UI Recommendations

### 1. Circuit Breaker Panel
```html
<div class="circuit-breaker-panel">
  <div class="panel-header">
    <h3>🛡️ Circuit Breaker</h3>
    <span class="status-badge" id="cb-status"></span>
  </div>
  <div class="panel-body">
    <div class="metric">
      <label>State:</label>
      <span id="cb-state"></span>
    </div>
    <div class="metric">
      <label>BTC 1h Change:</label>
      <span id="cb-btc-1h"></span>
    </div>
    <div class="metric">
      <label>ETH 1h Change:</label>
      <span id="cb-eth-1h"></span>
    </div>
    <div id="cb-alert" class="alert" style="display:none;"></div>
  </div>
  <div class="panel-footer">
    <button onclick="forceCheck()">Force Check</button>
  </div>
</div>
```

### 2. Spike Detection Chart
```html
<div class="spike-chart-container">
  <h3>📈 Recent Spikes</h3>
  <canvas id="spikeChart"></canvas>
  <div id="spike-list"></div>
</div>
```

### 3. Agent Activity Dashboard
```html
<div class="agent-grid">
  <div class="agent-card" data-agent="market_guardian">
    <div class="agent-icon">🛡️</div>
    <div class="agent-name">Market Guardian</div>
    <div class="agent-status">Active</div>
    <div class="agent-decisions">1440 decisions/24h</div>
  </div>
  <!-- Repeat for each agent -->
</div>
```

### 4. Agent Decision Log
```html
<div class="decision-log">
  <h3>🤖 AI Agent Decisions</h3>
  <div class="filters">
    <select id="agent-filter">
      <option value="">All Agents</option>
      <option value="Market Guardian">Market Guardian</option>
      <option value="Market Scanner">Market Scanner</option>
      <option value="Context Analyzer">Context Analyzer</option>
      <option value="Risk Assessment">Risk Assessment</option>
      <option value="Strategy Executor">Strategy Executor</option>
    </select>
  </div>
  <div id="decision-list"></div>
</div>
```

## Testing the Endpoints

### Using curl

```bash
# Circuit breaker status
curl http://localhost:5000/api/crewai/circuit-breaker-status

# Spike detections
curl http://localhost:5000/api/crewai/spike-detections?limit=10&hours=24

# Agent decisions
curl http://localhost:5000/api/crewai/agent-decisions?limit=20

# Spike trades
curl http://localhost:5000/api/crewai/spike-trades?status=OPEN

# Statistics
curl http://localhost:5000/api/crewai/statistics

# Agent status
curl http://localhost:5000/api/crewai/agent-status

# Force check (with PIN)
curl -X POST http://localhost:5000/api/crewai/force-check \
  -H "Content-Type: application/json" \
  -d '{"pin":"123456"}'
```

### Using Python

```python
import requests

base_url = 'http://localhost:5000'

# Get circuit breaker status
response = requests.get(f'{base_url}/api/crewai/circuit-breaker-status')
data = response.json()
print('Circuit Breaker:', data['data']['state'])

# Get recent spikes
response = requests.get(f'{base_url}/api/crewai/spike-detections', params={
    'limit': 10,
    'hours': 24
})
spikes = response.json()['data']
print(f'Found {len(spikes)} spikes in last 24 hours')

# Get agent decisions
response = requests.get(f'{base_url}/api/crewai/agent-decisions', params={
    'limit': 50,
    'agent': 'Market Guardian'
})
decisions = response.json()['data']
for decision in decisions:
    print(f"{decision['timestamp']}: {decision['decision']} - {decision['reasoning']}")
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message here"
}
```

**Common Error Codes:**
- `401` - PIN authentication failed
- `429` - Rate limit exceeded (too many failed PIN attempts)
- `500` - Internal server error

**Example error handling:**

```javascript
async function loadCircuitBreakerStatus() {
  try {
    const response = await fetch('/api/crewai/circuit-breaker-status');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    if (!data.success) {
      console.error('API Error:', data.error);
      return null;
    }

    return data.data;

  } catch (error) {
    console.error('Network Error:', error);
    return null;
  }
}
```

## Performance Considerations

**Polling Recommendations:**
- Circuit breaker status: Every 10-30 seconds
- Spike detections: Every 60 seconds
- Agent decisions: Every 30 seconds
- Statistics: Every 60 seconds
- Agent status: Every 60 seconds

**Caching:**
- Agent decisions and spike data are queried from database
- Circuit breaker status is real-time from memory
- Consider implementing browser-side caching for non-critical data

## Security

**PIN-Protected Endpoints:**
- `/api/crewai/force-check` - Requires 6-digit PIN

**Rate Limiting:**
- 3 failed PIN attempts = 15 minute block
- Based on client IP address

**Setup PIN:**
```bash
# Add to .env file
BOT_CONTROL_PIN=123456
```

## Next Steps

To complete the dashboard UI:

1. **Update dashboard.html** - Add CrewAI panels
2. **Create CSS styles** - Style the new components
3. **Add JavaScript** - Implement real-time updates
4. **Create charts** - Visualize spike and agent data
5. **Test integration** - Verify all endpoints work

## Summary

✅ **7 new API endpoints added**
✅ **Complete CrewAI data access**
✅ **Real-time monitoring capability**
✅ **Database integration for history**
✅ **Security with PIN authentication**

The backend API is now complete. Frontend dashboard components can be built to visualize this data.
