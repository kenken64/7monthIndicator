#!/usr/bin/env python3
"""
Chart Analysis Bot for SUI/USDC

A specialized bot that:
1. Fetches 15-minute interval chart data for SUI/USDC from Binance
2. Plots 24 hours of data as a professional trading chart
3. Sends the chart image to OpenAI for analysis
4. Gets buy/sell recommendations for short-term trading

Features:
- Real-time data from Binance API
- Professional candlestick charts with technical indicators
- AI-powered chart analysis using OpenAI GPT-4 Vision
- Automated trading recommendations
"""

import os
import sys
import json
import logging
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import mplfinance as mpf
from datetime import datetime, timedelta
from binance.client import Client
from dotenv import load_dotenv
import base64
from io import BytesIO
import warnings
import time

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chart_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChartAnalysisBot:
    """
    AI-powered chart analysis bot for SUI/USDC trading recommendations
    
    This bot combines technical analysis with AI vision capabilities to provide
    intelligent trading recommendations based on chart patterns and market trends.
    """
    
    def __init__(self, symbol: str = 'SUIUSDC'):
        """
        Initialize the Chart Analysis Bot
        
        Args:
            symbol: Trading pair symbol (default: SUIUSDC)
        """
        self.symbol = symbol
        
        # Initialize Binance client
        self.binance_api_key = os.getenv('BINANCE_API_KEY')
        self.binance_secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not self.binance_api_key or not self.binance_secret_key:
            logger.error("Binance API credentials not found in environment variables")
            sys.exit(1)
        
        self.binance_client = Client(self.binance_api_key, self.binance_secret_key)
        
        # Initialize OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            logger.error("OpenAI API key not found in environment variables")
            logger.info("Please add OPENAI_API_KEY to your .env file")
            sys.exit(1)
        
        # Chart configuration
        self.interval = '15m'  # 15-minute intervals
        self.hours_back = 24   # 24 hours of data
        self.chart_filename = f'chart_analysis_{self.symbol}.png'
        
        logger.info(f"🤖 Chart Analysis Bot initialized for {self.symbol}")
        logger.info(f"📊 Configuration: {self.interval} intervals, {self.hours_back}h history")
    
    def fetch_market_data(self) -> pd.DataFrame:
        """
        Fetch 15-minute interval data for the last 24 hours from Binance
        
        Returns:
            pd.DataFrame: OHLCV data with technical indicators
        """
        try:
            logger.info(f"📈 Fetching {self.symbol} data for last {self.hours_back} hours...")
            
            # Calculate the number of 15-minute intervals needed for 24 hours
            intervals_needed = int(self.hours_back * 4)  # 4 intervals per hour for 15min
            
            # Fetch klines data from Binance
            klines = self.binance_client.get_klines(
                symbol=self.symbol,
                interval=self.interval,
                limit=intervals_needed
            )
            
            if not klines:
                raise ValueError(f"No data received for {self.symbol}")
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Convert price columns to float
            price_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in price_cols:
                df[col] = df[col].astype(float)
            
            # Calculate technical indicators
            df = self._calculate_indicators(df)
            
            logger.info(f"✅ Fetched {len(df)} data points from {df.index[0]} to {df.index[-1]}")
            logger.info(f"💰 Current price: ${df['close'].iloc[-1]:.4f}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching market data: {e}")
            raise
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the chart
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            pd.DataFrame: DataFrame with added technical indicators
        """
        try:
            # Moving Averages
            df['EMA_9'] = df['close'].ewm(span=9).mean()
            df['EMA_21'] = df['close'].ewm(span=21).mean()
            df['SMA_50'] = df['close'].rolling(window=50).mean()
            
            # RSI calculation
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD calculation
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
            
            # Bollinger Bands
            df['BB_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
            df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
            
            # Volume Moving Average
            df['Volume_MA'] = df['volume'].rolling(window=20).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error calculating indicators: {e}")
            raise
    
    def create_professional_chart(self, df: pd.DataFrame) -> str:
        """
        Create a professional trading chart with technical indicators
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            str: Path to saved chart image
        """
        try:
            logger.info(f"🎨 Creating professional chart for {self.symbol}...")
            
            # Prepare data for mplfinance
            df_plot = df[['open', 'high', 'low', 'close', 'volume']].copy()
            
            # Define additional plots for indicators
            additional_plots = [
                # EMA lines
                mpf.make_addplot(df['EMA_9'], color='orange', width=1.5, label='EMA 9'),
                mpf.make_addplot(df['EMA_21'], color='blue', width=1.5, label='EMA 21'),
                mpf.make_addplot(df['SMA_50'], color='red', width=1, label='SMA 50'),
                
                # Bollinger Bands
                mpf.make_addplot(df['BB_upper'], color='gray', linestyle='--', alpha=0.5),
                mpf.make_addplot(df['BB_lower'], color='gray', linestyle='--', alpha=0.5),
                
                # Volume
                mpf.make_addplot(df['volume'], type='bar', panel=1, color='lightblue', alpha=0.7),
                mpf.make_addplot(df['Volume_MA'], panel=1, color='red', width=1),
                
                # RSI
                mpf.make_addplot(df['RSI'], panel=2, color='purple', width=1.5),
                
                # MACD
                mpf.make_addplot(df['MACD'], panel=3, color='blue', width=1),
                mpf.make_addplot(df['MACD_signal'], panel=3, color='red', width=1),
                mpf.make_addplot(df['MACD_histogram'], type='bar', panel=3, color='gray', alpha=0.3),
            ]
            
            # Create the chart
            current_price = df['close'].iloc[-1]
            price_change = df['close'].iloc[-1] - df['close'].iloc[0]
            price_change_pct = (price_change / df['close'].iloc[0]) * 100
            
            title = f"{self.symbol} - 15min Chart (24h) | ${current_price:.4f} ({price_change_pct:+.2f}%)"
            
            # Chart style
            style = mpf.make_mpf_style(
                marketcolors=mpf.make_marketcolors(
                    up='g', down='r', edge='inherit',
                    wick={'up':'green', 'down':'red'},
                    volume='lightblue'
                ),
                gridstyle='-',
                gridcolor='lightgray',
                facecolor='white',
                edgecolor='black'
            )
            
            # Save chart
            mpf.plot(
                df_plot,
                type='candle',
                style=style,
                addplot=additional_plots,
                volume=False,  # We're adding volume manually
                panel_ratios=(3, 1, 1, 1),  # Main, Volume, RSI, MACD
                figsize=(16, 12),
                title=title,
                savefig=dict(fname=self.chart_filename, dpi=300, bbox_inches='tight'),
                tight_layout=True
            )
            
            logger.info(f"✅ Chart saved as: {self.chart_filename}")
            return self.chart_filename
            
        except Exception as e:
            logger.error(f"❌ Error creating chart: {e}")
            raise
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode image to base64 for OpenAI API
        
        Args:
            image_path: Path to image file
            
        Returns:
            str: Base64 encoded image
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Error encoding image: {e}")
            raise
    
    def analyze_chart_with_openai(self, chart_path: str, current_data: dict) -> dict:
        """
        Send chart to OpenAI for AI-powered analysis
        
        Args:
            chart_path: Path to chart image
            current_data: Current market data for context
            
        Returns:
            dict: AI analysis with buy/sell recommendation
        """
        try:
            logger.info("🤖 Sending chart to OpenAI for analysis...")
            
            # Encode image
            base64_image = self.encode_image_to_base64(chart_path)
            
            # Prepare context data
            context_info = f"""
            Current Market Context for {self.symbol}:
            - Current Price: ${current_data['price']:.4f}
            - 24h Change: {current_data['change_24h']:+.2f}%
            - RSI: {current_data['rsi']:.2f}
            - MACD: {current_data['macd']:.6f}
            - EMA 9: ${current_data['ema_9']:.4f}
            - EMA 21: ${current_data['ema_21']:.4f}
            - Volume: {current_data['volume']:.0f}
            - Timestamp: {current_data['timestamp']}
            """
            
            # Create the prompt
            prompt = f"""You are a professional cryptocurrency trading analyst with expertise in technical analysis. 
Please analyze this {self.symbol} 15-minute chart covering the last 24 hours.

{context_info}

Based on the chart patterns, technical indicators, and current market conditions, please provide:

1. Overall Market Sentiment: Bullish, Bearish, or Neutral
2. Short-term Direction (next 1-4 hours): BUY, SELL, or HOLD
3. Confidence Level: High (80-100%), Medium (50-79%), or Low (0-49%)
4. Key Technical Observations: 
   - Support and resistance levels
   - Trend analysis
   - Indicator signals (RSI, MACD, EMAs)
   - Volume analysis
   - Chart patterns identified

5. Risk Assessment: What are the main risks for this trade?
6. Entry/Exit Strategy: Suggested entry price, stop loss, and take profit levels

Please provide a JSON response with this structure:
{{
    "recommendation": "BUY or SELL or HOLD",
    "confidence": "High or Medium or Low",
    "sentiment": "Bullish or Bearish or Neutral",
    "entry_price": {current_data['price']},
    "stop_loss": {current_data['price'] * 0.98},
    "take_profit": {current_data['price'] * 1.02},
    "key_observations": ["observation1", "observation2"],
    "risk_factors": ["risk1", "risk2"],
    "reasoning": "Detailed explanation of the recommendation"
}}

Focus on SHORT-TERM trading opportunities (1-4 hour timeframe) and be specific with price levels."""
            
            # Prepare API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.1
            }
            
            # Send request to OpenAI
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    # Fallback: create structured response from text
                    analysis = {
                        "recommendation": "HOLD",
                        "confidence": "Medium",
                        "sentiment": "Neutral",
                        "reasoning": ai_response,
                        "entry_price": current_data['price'],
                        "stop_loss": current_data['price'] * 0.98,
                        "take_profit": current_data['price'] * 1.02,
                        "key_observations": ["AI provided text analysis"],
                        "risk_factors": ["Standard trading risks"]
                    }
            except json.JSONDecodeError:
                # Fallback response
                analysis = {
                    "recommendation": "HOLD",
                    "confidence": "Low",
                    "sentiment": "Neutral",
                    "reasoning": ai_response,
                    "entry_price": current_data['price'],
                    "stop_loss": current_data['price'] * 0.98,
                    "take_profit": current_data['price'] * 1.02,
                    "key_observations": ["AI analysis completed"],
                    "risk_factors": ["Standard market risks"]
                }
            
            logger.info(f"✅ AI Analysis completed: {analysis['recommendation']} ({analysis['confidence']} confidence)")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing chart with OpenAI: {e}")
            # Return fallback analysis
            return {
                "recommendation": "HOLD",
                "confidence": "Low",
                "sentiment": "Neutral",
                "reasoning": f"Error occurred during AI analysis: {str(e)}",
                "entry_price": current_data['price'],
                "stop_loss": current_data['price'] * 0.98,
                "take_profit": current_data['price'] * 1.02,
                "key_observations": ["Analysis unavailable due to error"],
                "risk_factors": ["Unable to assess risks due to error"]
            }
    
    def run_analysis(self) -> dict:
        """
        Run complete chart analysis workflow
        
        Returns:
            dict: Complete analysis results
        """
        try:
            logger.info(f"🚀 Starting chart analysis for {self.symbol}...")
            
            # Step 1: Fetch market data
            df = self.fetch_market_data()
            
            # Step 2: Create chart
            chart_path = self.create_professional_chart(df)
            
            # Step 3: Prepare current data context
            current_data = {
                'price': df['close'].iloc[-1],
                'change_24h': ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100,
                'rsi': df['RSI'].iloc[-1],
                'macd': df['MACD'].iloc[-1],
                'ema_9': df['EMA_9'].iloc[-1],
                'ema_21': df['EMA_21'].iloc[-1],
                'volume': df['volume'].iloc[-1],
                'timestamp': df.index[-1].strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            # Step 4: AI Analysis
            ai_analysis = self.analyze_chart_with_openai(chart_path, current_data)
            
            # Step 5: Compile complete results
            complete_analysis = {
                'symbol': self.symbol,
                'analysis_time': datetime.now().isoformat(),
                'chart_file': chart_path,
                'market_data': current_data,
                'ai_analysis': ai_analysis,
                'data_points': len(df),
                'timeframe': f"{self.interval} intervals, {self.hours_back}h history"
            }
            
            # Log summary
            logger.info("📊 === CHART ANALYSIS COMPLETE ===")
            logger.info(f"🎯 Recommendation: {ai_analysis['recommendation']}")
            logger.info(f"📈 Confidence: {ai_analysis['confidence']}")
            logger.info(f"💭 Sentiment: {ai_analysis['sentiment']}")
            logger.info(f"💰 Entry Price: ${ai_analysis.get('entry_price', 'N/A')}")
            logger.info(f"🛡️ Stop Loss: ${ai_analysis.get('stop_loss', 'N/A')}")
            logger.info(f"🎯 Take Profit: ${ai_analysis.get('take_profit', 'N/A')}")
            logger.info(f"📸 Chart saved: {chart_path}")
            
            return complete_analysis
            
        except Exception as e:
            logger.error(f"❌ Error in analysis workflow: {e}")
            raise

def run_single_analysis(bot):
    """
    Run a single analysis cycle
    """
    try:
        # Run analysis
        results = bot.run_analysis()
        
        # Save results to file
        results_file = f"analysis_results_{bot.symbol}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📁 Results saved to: {results_file}")
        logger.info("🎉 Chart analysis completed successfully!")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error in analysis cycle: {e}")
        return None

def main():
    """
    Main entry point for the Chart Analysis Bot
    Runs continuous analysis every 15 minutes
    """
    try:
        logger.info("🤖 Starting Chart Analysis Bot for SUI/USDC...")
        logger.info("⏰ Running analysis every 15 minutes...")
        
        # Create bot instance
        bot = ChartAnalysisBot(symbol='SUIUSDC')
        
        # Run initial analysis
        logger.info("🚀 Running initial analysis...")
        run_single_analysis(bot)
        
        # Continuous loop with 15-minute intervals
        while True:
            try:
                logger.info("⏳ Waiting 15 minutes until next analysis...")
                time.sleep(15 * 60)  # 15 minutes = 900 seconds
                
                logger.info("🔄 Starting scheduled analysis cycle...")
                run_single_analysis(bot)
                
            except KeyboardInterrupt:
                logger.info("👋 Chart analysis stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                logger.info("⏳ Waiting 5 minutes before retry...")
                time.sleep(5 * 60)  # Wait 5 minutes before retry
                
    except KeyboardInterrupt:
        logger.info("👋 Chart analysis stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()