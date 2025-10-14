#!/usr/bin/env python3
"""
Script to create mock AI agent data for dashboard testing
"""

import sqlite3
import json
from datetime import datetime, timedelta
import random
import uuid

DB_PATH = 'data/trading_bot.db'

def generate_detection_id():
    return f"spike_{uuid.uuid4().hex[:12]}"

def generate_trade_id():
    return f"trade_{uuid.uuid4().hex[:12]}"

def generate_decision_id():
    return f"decision_{uuid.uuid4().hex[:12]}"

def create_mock_spike_detections(conn, count=5):
    """Create mock spike detection records"""
    cursor = conn.cursor()

    spike_types = ['price_spike', 'volume_explosion', 'liquidation_cascade', 'momentum_breakout']
    directions = ['UP', 'DOWN']
    legitimacy_types = ['LIKELY_LEGITIMATE', 'QUESTIONABLE', 'SUSPICIOUS']
    final_decisions = ['TRADE', 'AVOID', 'MONITOR']

    detections = []

    for i in range(count):
        detection_id = generate_detection_id()
        timestamp = (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat()

        spike_type = random.choice(spike_types)
        direction = random.choice(directions)
        magnitude = round(random.uniform(5.0, 25.0), 2)
        timeframe = random.choice([5, 15, 30, 60])
        volume_mult = round(random.uniform(2.0, 8.0), 2)
        confidence = round(random.uniform(0.6, 0.95), 2)

        btc_price = round(random.uniform(62000, 68000), 2)
        eth_price = round(random.uniform(3200, 3600), 2)
        market_trend = random.choice(['BULLISH', 'BEARISH', 'NEUTRAL'])
        circuit_breaker_safe = True

        legitimacy = random.choice(legitimacy_types)
        manipulation_score = random.randint(0, 10)
        market_correlation = random.choice([True, False])
        order_book_balanced = random.choice([True, False])

        scanner_decision = json.dumps({
            "recommendation": "INVESTIGATE" if legitimacy != "SUSPICIOUS" else "AVOID",
            "reasoning": f"Detected {spike_type} with {magnitude}% magnitude"
        })

        context_decision = json.dumps({
            "recommendation": "FAVORABLE" if market_trend in ['BULLISH', 'NEUTRAL'] else "UNFAVORABLE",
            "reasoning": f"Market trend is {market_trend}, BTC at ${btc_price}"
        })

        risk_decision = json.dumps({
            "recommendation": "APPROVED" if legitimacy == "LIKELY_LEGITIMATE" else "DENIED",
            "risk_score": manipulation_score,
            "reasoning": f"Legitimacy: {legitimacy}, Manipulation score: {manipulation_score}/10"
        })

        final_decision = random.choice(final_decisions)
        executed = final_decision == "TRADE"

        cursor.execute("""
            INSERT INTO spike_detections (
                detection_id, symbol, timestamp, spike_type, direction, magnitude_percent,
                timeframe_minutes, volume_multiplier, confidence_score,
                btc_price, eth_price, market_trend, circuit_breaker_safe,
                legitimacy, manipulation_score, market_correlation, order_book_balanced,
                scanner_decision, context_decision, risk_decision, final_decision,
                executed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            detection_id, 'SUIUSDC', timestamp, spike_type, direction, magnitude,
            timeframe, volume_mult, confidence,
            btc_price, eth_price, market_trend, circuit_breaker_safe,
            legitimacy, manipulation_score, market_correlation, order_book_balanced,
            scanner_decision, context_decision, risk_decision, final_decision,
            executed
        ))

        detections.append({
            'detection_id': detection_id,
            'executed': executed,
            'direction': direction,
            'timestamp': timestamp
        })

    conn.commit()
    print(f"✅ Created {count} mock spike detections")
    return detections

def create_mock_agent_decisions(conn, detections):
    """Create mock agent decision records"""
    cursor = conn.cursor()

    agent_names = [
        'market_guardian',
        'market_scanner',
        'context_analyzer',
        'risk_assessment',
        'strategy_executor'
    ]

    tasks = {
        'market_guardian': 'monitor_circuit_breaker',
        'market_scanner': 'detect_anomalies',
        'context_analyzer': 'analyze_market_conditions',
        'risk_assessment': 'evaluate_trade_risk',
        'strategy_executor': 'execute_strategy'
    }

    decisions_created = 0

    for detection in detections:
        # Create 3-5 agent decisions per detection
        num_agents = random.randint(3, 5)
        selected_agents = random.sample(agent_names, num_agents)

        for agent_name in selected_agents:
            decision_id = generate_decision_id()
            timestamp = detection['timestamp']
            task_name = tasks[agent_name]

            # Create realistic decision content based on agent
            if agent_name == 'market_guardian':
                decision_data = {
                    "status": "SAFE",
                    "action": "ALLOW_TRADING",
                    "circuit_breaker_state": "SAFE"
                }
                reasoning = "Market conditions are within normal parameters. Circuit breaker remains in SAFE state."
                confidence = 0.95

            elif agent_name == 'market_scanner':
                decision_data = {
                    "anomaly_detected": True,
                    "anomaly_type": detection['spike_type'] if 'spike_type' in str(detection) else "price_spike",
                    "recommendation": "INVESTIGATE"
                }
                reasoning = f"Detected unusual market activity. Magnitude suggests potential trading opportunity."
                confidence = random.uniform(0.7, 0.9)

            elif agent_name == 'context_analyzer':
                decision_data = {
                    "market_sentiment": random.choice(["BULLISH", "BEARISH", "NEUTRAL"]),
                    "btc_correlation": random.choice([True, False]),
                    "recommendation": random.choice(["FAVORABLE", "NEUTRAL", "UNFAVORABLE"])
                }
                reasoning = "Cross-asset analysis shows correlation with broader market movements."
                confidence = random.uniform(0.65, 0.85)

            elif agent_name == 'risk_assessment':
                risk_score = random.randint(2, 8)
                decision_data = {
                    "risk_score": risk_score,
                    "max_position_size": random.randint(100, 500),
                    "recommendation": "APPROVED" if risk_score < 6 else "DENIED"
                }
                reasoning = f"Risk analysis complete. Risk score: {risk_score}/10. Position sizing calculated based on volatility."
                confidence = random.uniform(0.75, 0.95)

            else:  # strategy_executor
                decision_data = {
                    "action": random.choice(["EXECUTE", "HOLD", "SKIP"]),
                    "entry_price": round(random.uniform(2.5, 3.2), 4),
                    "stop_loss": round(random.uniform(2.3, 2.5), 4),
                    "take_profit": round(random.uniform(3.3, 3.8), 4)
                }
                reasoning = "Entry conditions met. Executing trade with calculated risk parameters."
                confidence = random.uniform(0.7, 0.9)

            execution_time = random.randint(150, 3000)
            llm_tokens = random.randint(500, 2500)

            cursor.execute("""
                INSERT INTO agent_decisions (
                    decision_id, agent_name, task_name, timestamp,
                    input_data, decision, reasoning, confidence_score,
                    detection_id, execution_time_ms, llm_tokens_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision_id, agent_name, task_name, timestamp,
                json.dumps({"detection_id": detection['detection_id']}),
                json.dumps(decision_data), reasoning, confidence,
                detection['detection_id'], execution_time, llm_tokens
            ))

            decisions_created += 1

    conn.commit()
    print(f"✅ Created {decisions_created} mock agent decisions")

def create_mock_spike_trades(conn, detections):
    """Create mock spike trade records for executed detections"""
    cursor = conn.cursor()

    trades_created = 0

    for detection in detections:
        if not detection['executed']:
            continue

        trade_id = generate_trade_id()
        timestamp = detection['timestamp']

        side = 'LONG' if detection['direction'] == 'UP' else 'SHORT'
        entry_price = round(random.uniform(2.6, 3.0), 4)
        quantity = round(random.uniform(100, 500), 2)
        position_size = round(entry_price * quantity, 2)

        # Some trades are closed, some are still open
        is_closed = random.choice([True, False])

        if is_closed:
            exit_price = round(entry_price * random.uniform(0.95, 1.08), 4)
            pnl_percent = round(((exit_price - entry_price) / entry_price) * 100, 2)
            if side == 'SHORT':
                pnl_percent = -pnl_percent
            pnl_usd = round(position_size * (pnl_percent / 100), 2)
            holding_time = random.randint(5, 120)
            status = random.choice(['CLOSED', 'STOPPED_OUT'])
            exit_timestamp = (datetime.fromisoformat(timestamp) + timedelta(minutes=holding_time)).isoformat()
            exit_reason = random.choice(['TAKE_PROFIT', 'STOP_LOSS', 'MANUAL'])
        else:
            exit_price = None
            pnl_usd = None
            pnl_percent = None
            holding_time = None
            status = 'OPEN'
            exit_timestamp = None
            exit_reason = None

        stop_loss = round(entry_price * 0.97, 4)
        take_profit = round(entry_price * 1.05, 4)

        cursor.execute("""
            INSERT INTO spike_trades (
                trade_id, detection_id, symbol, timestamp, side, entry_price, exit_price,
                quantity, position_size_usd, stop_loss_price, take_profit_price,
                pnl_usd, pnl_percent, holding_time_minutes, status,
                exit_timestamp, exit_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_id, detection['detection_id'], 'SUIUSDC', timestamp, side, entry_price, exit_price,
            quantity, position_size, stop_loss, take_profit,
            pnl_usd, pnl_percent, holding_time, status,
            exit_timestamp, exit_reason
        ))

        trades_created += 1

    conn.commit()
    print(f"✅ Created {trades_created} mock spike trades")

def main():
    print("🚀 Creating mock AI agent data for dashboard...")

    conn = sqlite3.connect(DB_PATH)

    try:
        # Create spike detections
        detections = create_mock_spike_detections(conn, count=10)

        # Create agent decisions for each detection
        create_mock_agent_decisions(conn, detections)

        # Create trades for executed detections
        create_mock_spike_trades(conn, detections)

        print("\n✅ Mock data creation complete!")
        print(f"   - Spike detections: {len(detections)}")
        print(f"   - Agent decisions: Multiple per detection")
        print(f"   - Spike trades: {sum(1 for d in detections if d['executed'])}")
        print("\n🌐 Refresh the dashboard to see the new data!")

    except Exception as e:
        print(f"❌ Error creating mock data: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
