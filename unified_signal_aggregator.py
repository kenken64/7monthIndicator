"""
Unified Signal Aggregator
Combines signals from multiple sources to determine trading strength:
1. Layer 1: Technical Indicators (RSI, MACD, VWAP, EMA)
2. Layer 2: RL Enhancement
3. Chart Analysis (OpenAI GPT-4 Vision)
4. CrewAI Multi-Agent System
5. Market Context & Cross-Asset Analysis
6. News Sentiment Analysis
"""

import json
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class UnifiedSignalAggregator:
    """Aggregates signals from multiple sources with weighted scoring"""

    # Signal weights (must sum to 1.0)
    WEIGHTS = {
        'technical': 0.25,      # Layer 1: Traditional indicators
        'rl': 0.30,             # Layer 2: RL enhancement (highest weight)
        'chart_analysis': 0.15, # OpenAI vision analysis
        'crewai': 0.15,         # Multi-agent system
        'market_context': 0.10, # Cross-asset correlation
        'news_sentiment': 0.05  # News sentiment
    }

    def __init__(self):
        """Initialize the aggregator"""
        self.last_chart_analysis = None
        self.last_crewai_signal = None
        self.last_market_context = None
        self.last_news_sentiment = None

        # Cache durations
        self.chart_analysis_ttl = timedelta(minutes=15)
        self.crewai_ttl = timedelta(minutes=5)
        self.market_context_ttl = timedelta(minutes=10)
        self.news_sentiment_ttl = timedelta(hours=1)

    def aggregate_signals(
        self,
        technical_signal: Dict,
        rl_signal: Dict,
        current_price: float,
        symbol: str = "SUIUSDC"
    ) -> Dict:
        """
        Aggregate all signals into a unified trading decision

        Args:
            technical_signal: Layer 1 technical indicators signal
            rl_signal: Layer 2 RL enhancement signal
            current_price: Current market price
            symbol: Trading symbol

        Returns:
            Dict with unified signal, strength (0-10), confidence, and breakdown
        """
        logger.info("=== Starting Unified Signal Aggregation ===")

        signals = {}
        scores = {}
        confidences = {}

        # 1. Technical Indicators (Layer 1)
        tech_score, tech_conf = self._score_technical_signal(technical_signal)
        signals['technical'] = technical_signal
        scores['technical'] = tech_score
        confidences['technical'] = tech_conf
        logger.info(f"Technical Score: {tech_score:.2f}/10 (confidence: {tech_conf:.1f}%)")

        # 2. RL Enhancement (Layer 2)
        rl_score, rl_conf = self._score_rl_signal(rl_signal)
        signals['rl'] = rl_signal
        scores['rl'] = rl_score
        confidences['rl'] = rl_conf
        logger.info(f"RL Score: {rl_score:.2f}/10 (confidence: {rl_conf:.1f}%)")

        # 3. Chart Analysis
        chart_score, chart_conf = self._score_chart_analysis(symbol)
        signals['chart_analysis'] = self.last_chart_analysis
        scores['chart_analysis'] = chart_score
        confidences['chart_analysis'] = chart_conf
        logger.info(f"Chart Analysis Score: {chart_score:.2f}/10 (confidence: {chart_conf:.1f}%)")

        # 4. CrewAI Multi-Agent
        crewai_score, crewai_conf = self._score_crewai_signal(symbol)
        signals['crewai'] = self.last_crewai_signal
        scores['crewai'] = crewai_score
        confidences['crewai'] = crewai_conf
        logger.info(f"CrewAI Score: {crewai_score:.2f}/10 (confidence: {crewai_conf:.1f}%)")

        # 5. Market Context & Cross-Asset
        market_score, market_conf = self._score_market_context()
        signals['market_context'] = self.last_market_context
        scores['market_context'] = market_score
        confidences['market_context'] = market_conf
        logger.info(f"Market Context Score: {market_score:.2f}/10 (confidence: {market_conf:.1f}%)")

        # 6. News Sentiment
        news_score, news_conf = self._score_news_sentiment(symbol)
        signals['news_sentiment'] = self.last_news_sentiment
        scores['news_sentiment'] = news_score
        confidences['news_sentiment'] = news_conf
        logger.info(f"News Sentiment Score: {news_score:.2f}/10 (confidence: {news_conf:.1f}%)")

        # Calculate weighted score
        weighted_score = sum(
            scores[key] * self.WEIGHTS[key]
            for key in scores.keys()
        )

        # Calculate overall confidence (weighted average)
        overall_confidence = sum(
            confidences[key] * self.WEIGHTS[key]
            for key in confidences.keys()
        )

        # Determine unified signal
        unified_signal = self._determine_signal(weighted_score, overall_confidence)

        logger.info(f"=== UNIFIED RESULT: {unified_signal} | Strength: {weighted_score:.2f}/10 | Confidence: {overall_confidence:.1f}% ===")

        return {
            'signal': unified_signal,
            'strength': round(weighted_score, 2),
            'confidence': round(overall_confidence, 1),
            'timestamp': datetime.utcnow().isoformat(),
            'breakdown': {
                'scores': scores,
                'confidences': confidences,
                'weights': self.WEIGHTS
            },
            'raw_signals': signals
        }

    def _score_technical_signal(self, signal: Dict) -> Tuple[float, float]:
        """
        Score technical indicators signal (0-10)

        Returns:
            (score, confidence)
        """
        if not signal:
            return 5.0, 0.0  # Neutral if no signal

        action = signal.get('action', 'HOLD')

        # Base score from action
        if action == 'BUY':
            base_score = 7.0
        elif action == 'SELL':
            base_score = 3.0
        else:  # HOLD
            base_score = 5.0

        # Adjust based on indicator alignment
        indicators = signal.get('indicators', {})
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', 0)

        # RSI adjustments
        if rsi < 30:  # Oversold - bullish
            base_score += 1.0
        elif rsi > 70:  # Overbought - bearish
            base_score -= 1.0

        # MACD adjustments
        if macd > 0:  # Bullish
            base_score += 0.5
        elif macd < 0:  # Bearish
            base_score -= 0.5

        # Clamp to 0-10
        score = max(0.0, min(10.0, base_score))

        # Confidence based on signal strength
        confidence = signal.get('confidence', 50.0)

        return score, confidence

    def _score_rl_signal(self, signal: Dict) -> Tuple[float, float]:
        """
        Score RL enhancement signal (0-10)

        Returns:
            (score, confidence)
        """
        if not signal:
            return 5.0, 0.0

        action = signal.get('action', 'HOLD')
        confidence = signal.get('confidence', 0.0)

        # Base score from action
        if action == 'BUY':
            base_score = 8.0  # RL is trusted more
        elif action == 'SELL':
            base_score = 2.0
        else:  # HOLD
            base_score = 5.0

        # Adjust based on RL confidence
        # High confidence RL should push score further from neutral
        if confidence > 70:
            if action == 'BUY':
                base_score += 1.5
            elif action == 'SELL':
                base_score -= 1.5
        elif confidence > 50:
            if action == 'BUY':
                base_score += 0.5
            elif action == 'SELL':
                base_score -= 0.5

        score = max(0.0, min(10.0, base_score))

        return score, confidence

    def _score_chart_analysis(self, symbol: str) -> Tuple[float, float]:
        """
        Score chart analysis from OpenAI GPT-4 Vision (0-10)

        Returns:
            (score, confidence)
        """
        try:
            # Load latest chart analysis
            analysis_file = f'/root/7monthIndicator/analysis_results_{symbol}.json'
            if not os.path.exists(analysis_file):
                logger.warning(f"Chart analysis file not found: {analysis_file}")
                return 5.0, 0.0

            with open(analysis_file, 'r') as f:
                data = json.load(f)

            self.last_chart_analysis = data

            # Check if analysis is recent enough
            analysis_time = datetime.fromisoformat(data.get('analysis_time', '2000-01-01T00:00:00'))
            if datetime.utcnow() - analysis_time > self.chart_analysis_ttl:
                logger.warning(f"Chart analysis is stale ({analysis_time})")
                return 5.0, 20.0  # Low confidence for stale data

            ai_analysis = data.get('ai_analysis', {})
            recommendation = ai_analysis.get('recommendation', 'HOLD')
            confidence_str = ai_analysis.get('confidence', 'Low')

            # Convert confidence string to numeric
            confidence_map = {'Low': 30.0, 'Medium': 60.0, 'High': 85.0}
            confidence = confidence_map.get(confidence_str, 50.0)

            # Score based on recommendation
            if recommendation == 'BUY':
                score = 7.5
            elif recommendation == 'SELL':
                score = 2.5
            else:  # HOLD
                score = 5.0

            # Adjust based on sentiment
            sentiment = ai_analysis.get('sentiment', 'Neutral')
            if sentiment == 'Bullish':
                score += 1.0
            elif sentiment == 'Bearish':
                score -= 1.0

            score = max(0.0, min(10.0, score))

            return score, confidence

        except Exception as e:
            logger.error(f"Error scoring chart analysis: {e}")
            return 5.0, 0.0

    def _score_crewai_signal(self, symbol: str) -> Tuple[float, float]:
        """
        Score CrewAI multi-agent signal (0-10)

        Returns:
            (score, confidence)
        """
        try:
            # Load latest CrewAI analysis
            crewai_file = '/root/7monthIndicator/crewai_analysis.json'
            if not os.path.exists(crewai_file):
                logger.warning("CrewAI analysis file not found")
                return 5.0, 0.0

            with open(crewai_file, 'r') as f:
                data = json.load(f)

            self.last_crewai_signal = data

            # Check timestamp
            timestamp = datetime.fromisoformat(data.get('timestamp', '2000-01-01T00:00:00'))
            if datetime.utcnow() - timestamp > self.crewai_ttl:
                logger.warning(f"CrewAI signal is stale ({timestamp})")
                return 5.0, 20.0

            # Get consensus signal
            consensus = data.get('consensus', {})
            action = consensus.get('action', 'HOLD')
            confidence = consensus.get('confidence', 50.0)

            # Score based on action
            if action == 'BUY':
                score = 7.5
            elif action == 'SELL':
                score = 2.5
            else:
                score = 5.0

            # Adjust based on spike detection
            spike_detected = data.get('spike_detection', {}).get('spike_detected', False)
            if spike_detected:
                spike_type = data.get('spike_detection', {}).get('spike_type', 'unknown')
                if spike_type == 'bullish':
                    score += 1.0
                elif spike_type == 'bearish':
                    score -= 1.0

            score = max(0.0, min(10.0, score))

            return score, confidence

        except Exception as e:
            logger.error(f"Error scoring CrewAI signal: {e}")
            return 5.0, 0.0

    def _score_market_context(self) -> Tuple[float, float]:
        """
        Score market context & cross-asset analysis (0-10)

        Returns:
            (score, confidence)
        """
        try:
            # Load market context
            context_file = '/root/7monthIndicator/market_context.json'
            if not os.path.exists(context_file):
                logger.warning("Market context file not found")
                return 5.0, 0.0

            with open(context_file, 'r') as f:
                data = json.load(f)

            self.last_market_context = data

            # Check timestamp
            timestamp = datetime.fromisoformat(data.get('timestamp', '2000-01-01T00:00:00'))
            if datetime.utcnow() - timestamp > self.market_context_ttl:
                logger.warning(f"Market context is stale ({timestamp})")
                return 5.0, 20.0

            # Analyze BTC/ETH trends
            btc_trend = data.get('btc', {}).get('trend', 'neutral')
            eth_trend = data.get('eth', {}).get('trend', 'neutral')
            correlation = data.get('correlation', {}).get('sui_btc', 0.5)

            # Base score from market leaders
            score = 5.0

            if btc_trend == 'bullish' and eth_trend == 'bullish':
                score = 6.5  # Positive market
            elif btc_trend == 'bearish' and eth_trend == 'bearish':
                score = 3.5  # Negative market

            # Adjust based on correlation
            # High correlation means SUI follows BTC/ETH more closely
            if correlation > 0.7:
                if btc_trend == 'bullish':
                    score += 1.0
                elif btc_trend == 'bearish':
                    score -= 1.0

            score = max(0.0, min(10.0, score))
            confidence = 70.0  # Market context is generally reliable

            return score, confidence

        except Exception as e:
            logger.error(f"Error scoring market context: {e}")
            return 5.0, 0.0

    def _score_news_sentiment(self, symbol: str) -> Tuple[float, float]:
        """
        Score news sentiment analysis (0-10)

        Returns:
            (score, confidence)
        """
        try:
            # Load news sentiment
            news_file = '/root/7monthIndicator/news_sentiment.json'
            if not os.path.exists(news_file):
                logger.warning("News sentiment file not found")
                return 5.0, 0.0

            with open(news_file, 'r') as f:
                data = json.load(f)

            self.last_news_sentiment = data

            # Check timestamp
            timestamp = datetime.fromisoformat(data.get('timestamp', '2000-01-01T00:00:00'))
            if datetime.utcnow() - timestamp > self.news_sentiment_ttl:
                logger.warning(f"News sentiment is stale ({timestamp})")
                return 5.0, 20.0

            # Get sentiment score (-1 to 1)
            sentiment_score = data.get('sentiment_score', 0.0)
            article_count = data.get('article_count', 0)

            # Convert sentiment to 0-10 scale
            # -1 (very bearish) -> 0
            # 0 (neutral) -> 5
            # +1 (very bullish) -> 10
            score = (sentiment_score + 1) * 5.0

            # Confidence based on article count
            if article_count >= 10:
                confidence = 75.0
            elif article_count >= 5:
                confidence = 60.0
            elif article_count >= 2:
                confidence = 40.0
            else:
                confidence = 20.0

            return score, confidence

        except Exception as e:
            logger.error(f"Error scoring news sentiment: {e}")
            return 5.0, 0.0

    def _determine_signal(self, score: float, confidence: float) -> str:
        """
        Determine final signal based on unified score and confidence

        Args:
            score: Unified score (0-10)
            confidence: Overall confidence (0-100)

        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        # Require minimum confidence for non-HOLD signals
        MIN_CONFIDENCE = 55.0

        if confidence < MIN_CONFIDENCE:
            return 'HOLD'

        # Score thresholds
        if score >= 6.5:
            return 'BUY'
        elif score <= 3.5:
            return 'SELL'
        else:
            return 'HOLD'

    def get_signal_summary(self, unified_result: Dict) -> str:
        """
        Generate a human-readable summary of the unified signal

        Args:
            unified_result: Result from aggregate_signals()

        Returns:
            Formatted string summary
        """
        signal = unified_result['signal']
        strength = unified_result['strength']
        confidence = unified_result['confidence']
        breakdown = unified_result['breakdown']

        summary = f"\n{'='*60}\n"
        summary += f"UNIFIED SIGNAL: {signal} | Strength: {strength:.2f}/10 | Confidence: {confidence:.1f}%\n"
        summary += f"{'='*60}\n\n"

        summary += "Signal Breakdown:\n"
        for source, score in breakdown['scores'].items():
            weight = self.WEIGHTS[source] * 100
            conf = breakdown['confidences'][source]
            summary += f"  • {source.replace('_', ' ').title()}: {score:.2f}/10 (weight: {weight:.0f}%, conf: {conf:.1f}%)\n"

        summary += f"\n{'='*60}\n"

        return summary


def create_aggregator() -> UnifiedSignalAggregator:
    """Factory function to create an aggregator instance"""
    return UnifiedSignalAggregator()
