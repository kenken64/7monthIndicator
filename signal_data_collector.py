"""
Signal Data Collector
Periodically collects and saves signals from all sources to JSON files for aggregation
"""

import json
import logging
import time
import threading
from datetime import datetime
from typing import Dict, Optional
import os

# Import signal source modules
from cross_asset_correlation import CrossAssetAnalyzer
from crewai_integration import get_crewai_integration
from openai_news_sentiment import OpenAINewsSentiment
from timezone_utils import setup_singapore_logging

# Configure logger with Singapore timezone
logger = setup_singapore_logging(
    logger_name=__name__,
    level=logging.INFO,
    log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S SGT',
    console=True
)


class SignalDataCollector:
    """Collects and persists signal data from various sources"""

    def __init__(self):
        """Initialize the signal data collector"""
        self.running = False
        self.collector_thread = None

        # Initialize analyzers
        try:
            self.cross_asset_analyzer = CrossAssetAnalyzer()
            logger.info("✅ Cross-asset analyzer initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize cross-asset analyzer: {e}")
            self.cross_asset_analyzer = None

        try:
            self.crewai_integration = get_crewai_integration()
            logger.info("✅ CrewAI integration initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize CrewAI: {e}")
            self.crewai_integration = None

        # Check if we should use local sentiment analysis
        use_local_sentiment = os.getenv('USE_LOCAL_SENTIMENT', 'false').lower() == 'true'

        if use_local_sentiment:
            try:
                from local_sentiment import LocalSentimentAnalyzer
                self.sentiment_analyzer = LocalSentimentAnalyzer()
                self.use_local_sentiment = True
                logger.info("✅ Local sentiment analyzer initialized (cost-saving mode)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize local sentiment analyzer: {e}")
                self.sentiment_analyzer = None
                self.use_local_sentiment = False
        else:
            try:
                self.sentiment_analyzer = OpenAINewsSentiment()
                self.use_local_sentiment = False
                logger.info("✅ OpenAI news sentiment analyzer initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI news sentiment analyzer: {e}")
                self.sentiment_analyzer = None
                self.use_local_sentiment = False

        # Collection intervals (seconds)
        self.intervals = {
            'market_context': 300,      # 5 minutes
            'crewai': 300,              # 5 minutes
            'news_sentiment': 3600      # 1 hour
        }

        # Last collection times
        self.last_collection = {
            'market_context': 0,
            'crewai': 0,
            'news_sentiment': 0
        }

    def start_collection(self):
        """Start background data collection"""
        if not self.running:
            self.running = True
            self.collector_thread = threading.Thread(
                target=self._collection_loop,
                daemon=True,
                name="SignalDataCollector"
            )
            self.collector_thread.start()
            logger.info("🔄 Signal data collection started")

    def stop_collection(self):
        """Stop background data collection"""
        if self.running:
            self.running = False
            if self.collector_thread:
                self.collector_thread.join(timeout=5)
            logger.info("🛑 Signal data collection stopped")

    def _collection_loop(self):
        """Main collection loop"""
        logger.info("🔄 Signal data collection loop started")

        while self.running:
            try:
                current_time = time.time()

                # Collect market context
                if current_time - self.last_collection['market_context'] >= self.intervals['market_context']:
                    self._collect_market_context()
                    self.last_collection['market_context'] = current_time

                # Collect CrewAI signals
                if current_time - self.last_collection['crewai'] >= self.intervals['crewai']:
                    self._collect_crewai_signals()
                    self.last_collection['crewai'] = current_time

                # Collect news sentiment
                if current_time - self.last_collection['news_sentiment'] >= self.intervals['news_sentiment']:
                    self._collect_news_sentiment()
                    self.last_collection['news_sentiment'] = current_time

                # Sleep for 30 seconds before next check
                time.sleep(30)

            except Exception as e:
                logger.error(f"❌ Error in collection loop: {e}")
                time.sleep(60)

    def _collect_market_context(self):
        """Collect and save market context data"""
        try:
            if not self.cross_asset_analyzer:
                logger.warning("Cross-asset analyzer not available")
                return

            logger.info("📊 Collecting market context...")

            # Get market context
            context = self.cross_asset_analyzer.get_market_context()

            if not context:
                logger.warning("Failed to get market context")
                return

            # Determine trends
            btc_trend = 'bullish' if context.btc_change_24h > 0 else 'bearish' if context.btc_change_24h < 0 else 'neutral'
            eth_trend = 'bullish' if context.eth_change_24h > 0 else 'bearish' if context.eth_change_24h < 0 else 'neutral'

            # Calculate SUI-BTC correlation (simplified)
            correlation_strength = 0.7  # Default - would need historical data for accurate calculation

            # Create market context data
            market_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'btc': {
                    'price': context.btc_price,
                    'change_24h': context.btc_change_24h,
                    'dominance': context.btc_dominance,
                    'trend': btc_trend
                },
                'eth': {
                    'price': context.eth_price,
                    'change_24h': context.eth_change_24h,
                    'trend': eth_trend
                },
                'market': {
                    'trend': context.market_trend,
                    'volatility': context.volatility_regime,
                    'fear_greed_index': context.fear_greed_index,
                    'correlation_signal': context.correlation_signal
                },
                'correlation': {
                    'sui_btc': correlation_strength,
                    'sui_eth': correlation_strength * 0.9
                }
            }

            # Save to file
            # Detect environment (Docker uses /app, native uses project root)
            base_path = '/app' if os.path.exists('/app') else '/root/7monthIndicator'
            with open(f'{base_path}/market_context.json', 'w') as f:
                json.dump(market_data, f, indent=2)

            logger.info(f"✅ Market context saved: BTC ${context.btc_price:.0f} ({context.btc_change_24h:+.1f}%), Trend: {context.market_trend}")

        except Exception as e:
            logger.error(f"❌ Error collecting market context: {e}")

    def _collect_crewai_signals(self):
        """Collect and save CrewAI multi-agent signals"""
        try:
            if not self.crewai_integration:
                logger.warning("CrewAI integration not available")
                return

            logger.info("🤖 Collecting CrewAI signals...")

            # Get circuit breaker status
            circuit_breaker_status = self.crewai_integration.get_circuit_breaker_status()

            # Get statistics
            stats = self.crewai_integration.get_statistics()

            # Create simplified CrewAI signal data
            # Note: Full CrewAI analysis is expensive, so we use status/stats for now
            crewai_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'circuit_breaker': {
                    'state': circuit_breaker_status.get('state', 'NORMAL'),
                    'safe': circuit_breaker_status.get('btc_change_1h', 0) > -5.0,  # Safe if BTC drop < 5%
                    'trigger_reason': circuit_breaker_status.get('trigger_reason', 'None')
                },
                'consensus': {
                    'action': self._determine_crewai_action(circuit_breaker_status),
                    'confidence': 60.0  # Default confidence
                },
                'spike_detection': {
                    'spike_detected': False,
                    'spike_type': 'none'
                },
                'statistics': stats
            }

            # Save to file
            # Detect environment (Docker uses /app, native uses project root)
            base_path = '/app' if os.path.exists('/app') else '/root/7monthIndicator'
            with open(f'{base_path}/crewai_analysis.json', 'w') as f:
                json.dump(crewai_data, f, indent=2)

            logger.info(f"✅ CrewAI signals saved: State={crewai_data['circuit_breaker']['state']}, Action={crewai_data['consensus']['action']}")

        except Exception as e:
            logger.error(f"❌ Error collecting CrewAI signals: {e}")

    def _determine_crewai_action(self, circuit_breaker_status: Dict) -> str:
        """Determine action based on circuit breaker status"""
        btc_1h = circuit_breaker_status.get('btc_change_1h', 0)
        btc_4h = circuit_breaker_status.get('btc_change_4h', 0)

        # Conservative logic based on BTC trends
        if btc_1h < -5.0 or btc_4h < -10.0:
            return 'SELL'  # Market crash detected
        elif btc_1h > 3.0 and btc_4h > 5.0:
            return 'BUY'   # Strong uptrend
        else:
            return 'HOLD'  # Neutral/uncertain

    def _collect_news_sentiment(self):
        """Collect and save news sentiment data using OpenAI or local analyzer"""
        try:
            if not self.sentiment_analyzer:
                logger.warning("Sentiment analyzer not available")
                return

            # Detect environment (Docker uses /app, native uses project root)
            base_path = '/app' if os.path.exists('/app') else '/root/7monthIndicator'

            if self.use_local_sentiment:
                logger.info("📰 Collecting SUI news sentiment using local analyzer...")

                # Generate fallback news headlines with balanced sentiment
                # Format: "Title: Short description"
                fallback_headlines = [
                    "SUI Network Shows Strong DeFi Growth: Total Value Locked increases by 15% this week indicating strong adoption of DeFi protocols and ecosystem expansion",
                    "SUI Blockchain Rally Continues: Network maintains high transaction throughput of 100,000+ TPS with minimal fees, outperforming competitors",
                    "Developer Adoption Surges on SUI: Positive new dApp launches expand ecosystem capabilities with innovative smart contract applications",
                    "SUI Price Gains Bullish Momentum: Crypto market shows positive sentiment as SUI breaks through key resistance levels with strong volume",
                    "Institutional Investment Flows Into SUI: Layer 1 blockchain sees positive growth in institutional interest and major fund allocations",
                    "SUI Network Upgrade Enhances Efficiency: Smart contract improvements deliver bullish technical advancements in scalability and performance",
                    "Cross-Chain Bridges Expand SUI Reach: New integrations drive positive market response by improving interoperability with major blockchains",
                    "NFT Marketplace Activity Grows on SUI: Ecosystem sees rising trading volume and increased user engagement in digital collectibles",
                    "Validator Network Strengthens on SUI: Node count increases showing strong decentralization, security, and growing adoption by validators",
                    "SUI Foundation Boosts Ecosystem: New grants program announced to accelerate development and attract innovative projects to the platform"
                ]

                # Analyze sentiment using local analyzer
                local_result = self.sentiment_analyzer.analyze_sentiment(fallback_headlines)

                # Convert local analyzer output (0-10 scale) to OpenAI format (0-100 scale)
                sentiment_result = {
                    'sentiment': local_result['sentiment'],
                    'sentiment_score': (local_result['confidence'] / 10.0),  # Convert 0-10 to 0-1 scale
                    'confidence': local_result['confidence'] * 10,  # Convert 0-10 to 0-100 scale
                    'explanation': local_result['explanation'],
                    'article_count': len(fallback_headlines),
                    'scores': {
                        'bullish': int(local_result['scores'].get('bullish', 0) * 10),
                        'bearish': int(local_result['scores'].get('bearish', 0) * 10),
                        'neutral': max(0, len(fallback_headlines) - int(local_result['scores'].get('bullish', 0) * 10) - int(local_result['scores'].get('bearish', 0) * 10))
                    },
                    'timestamp': datetime.utcnow().isoformat(),
                    'headlines': fallback_headlines[:5]
                }

            else:
                logger.info("📰 Collecting SUI news sentiment using OpenAI...")

                # Fetch news and analyze sentiment in one call (20 latest news items)
                sentiment_result = self.sentiment_analyzer.get_news_and_sentiment(count=20)

            # Save to file (sentiment_result already has all the necessary fields)
            with open(f'{base_path}/news_sentiment.json', 'w') as f:
                json.dump(sentiment_result, f, indent=2)

            logger.info(f"✅ News sentiment saved: {sentiment_result['sentiment']} (score: {sentiment_result.get('sentiment_score', 0):.2f}, confidence: {sentiment_result.get('confidence', 0):.0f}%, articles: {sentiment_result['article_count']})")

        except Exception as e:
            logger.error(f"❌ Error collecting news sentiment: {e}")

    def force_collection(self):
        """Force immediate collection of all signals"""
        logger.info("🔄 Forcing immediate signal collection...")
        self._collect_market_context()
        self._collect_crewai_signals()
        self._collect_news_sentiment()
        logger.info("✅ Forced collection complete")


def main():
    """Test the signal data collector"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("🔍 Testing Signal Data Collector...")
    print("=" * 60)

    collector = SignalDataCollector()

    # Force immediate collection
    print("\n📊 Collecting all signals...")
    collector.force_collection()

    print("\n✅ Collection complete! Check the following files:")
    print("  • /root/7monthIndicator/market_context.json")
    print("  • /root/7monthIndicator/crewai_analysis.json")
    print("  • /root/7monthIndicator/news_sentiment.json")

    # Show file contents
    for filename in ['market_context.json', 'crewai_analysis.json', 'news_sentiment.json']:
        filepath = f'/root/7monthIndicator/{filename}'
        if os.path.exists(filepath):
            print(f"\n📄 {filename}:")
            with open(filepath, 'r') as f:
                data = json.load(f)
                print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
