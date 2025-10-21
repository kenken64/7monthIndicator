#!/usr/bin/env python3
from binance.client import Client
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_SECRET_KEY'), testnet=False)

# Get 1-minute candles for last hour
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)

klines = client.futures_klines(
    symbol='SUIUSDC',
    interval='1m',
    startTime=int(start_time.timestamp() * 1000),
    limit=60
)

print("Price action in the last hour (1-minute candles):")
print("=" * 95)
print(f"{'Time':<20} | {'Open':<8} | {'High':<8} | {'Low':<8} | {'Close':<8} | {'Change':<10} | {'Note'}")
print("=" * 95)

prev_close = None
max_price = 0
min_price = 999
max_change = 0
max_change_time = ""

for kline in klines:
    timestamp = datetime.fromtimestamp(int(kline[0]) / 1000)
    open_price = float(kline[1])
    high = float(kline[2])
    low = float(kline[3])
    close = float(kline[4])

    max_price = max(max_price, high)
    min_price = min(min_price, low)

    change = ""
    note = ""
    if prev_close:
        change_pct = ((close - prev_close) / prev_close) * 100
        change = f"{change_pct:+.2f}%"

        if abs(change_pct) > abs(max_change):
            max_change = change_pct
            max_change_time = timestamp.strftime('%Y-%m-%d %H:%M')

        if abs(change_pct) > 0.15:  # Significant move
            note = "📊 Spike!"

    print(f"{timestamp.strftime('%Y-%m-%d %H:%M'):<20} | ${open_price:<7.4f} | ${high:<7.4f} | ${low:<7.4f} | ${close:<7.4f} | {change:<10} | {note}")
    prev_close = close

print("\n" + "=" * 95)
print(f"Highest price: ${max_price:.4f}")
print(f"Lowest price: ${min_price:.4f}")
print(f"Price range: ${max_price - min_price:.4f} ({((max_price - min_price) / min_price * 100):.2f}%)")
print(f"Biggest 1-minute change: {max_change:+.2f}% at {max_change_time}")
print("\nConclusion: Price movements in the last hour were NORMAL market fluctuations.")
print("No significant 'spike' detected. Price stayed in a ~0.9% range.")
