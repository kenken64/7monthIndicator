#!/usr/bin/env python3
"""
Local Sentiment Analysis Module

A cost-effective alternative to OpenAI API for basic sentiment analysis.
Uses keyword-based scoring and simple NLP techniques to analyze market sentiment
from news headlines without external API calls.
"""

import re
from typing import List, Dict

class LocalSentimentAnalyzer:
    """
    Local sentiment analyzer using keyword-based scoring
    """
    
    def __init__(self):
        # Bullish keywords and their weights
        self.bullish_keywords = {
            'surge': 3, 'rally': 3, 'boom': 3, 'soar': 3, 'moon': 3,
            'bull': 2, 'gain': 2, 'rise': 2, 'pump': 2, 'breakout': 2,
            'up': 1, 'green': 1, 'positive': 1, 'growth': 1, 'increase': 1,
            'adoption': 2, 'bullish': 3, 'institutional': 2, 'etf': 2,
            'approval': 2, 'investment': 1, 'buy': 1, 'long': 1
        }
        
        # Bearish keywords and their weights  
        self.bearish_keywords = {
            'crash': 3, 'dump': 3, 'collapse': 3, 'plunge': 3, 'tank': 3,
            'bear': 2, 'fall': 2, 'drop': 2, 'decline': 2, 'sell': 2,
            'down': 1, 'red': 1, 'negative': 1, 'loss': 1, 'decrease': 1,
            'regulation': 2, 'ban': 3, 'crackdown': 3, 'bearish': 3,
            'short': 1, 'fear': 2, 'panic': 3, 'liquidation': 2
        }
        
        # Market volatility keywords
        self.volatility_keywords = {
            'volatile': 2, 'volatility': 2, 'swing': 1, 'turbulent': 2,
            'uncertainty': 1, 'unstable': 1, 'whipsaw': 2
        }
    
    def analyze_sentiment(self, news_titles: List[str]) -> Dict:
        """
        Analyze sentiment from news titles using keyword scoring
        
        Args:
            news_titles: List of news headlines
            
        Returns:
            Dict: Sentiment analysis results
        """
        if not news_titles:
            return {
                'sentiment': 'Unknown',
                'confidence': 0,
                'explanation': 'No titles provided'
            }
        
        # Combine all titles into one text
        text = ' '.join(news_titles).lower()
        
        # Remove punctuation and split into words
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        
        # Calculate sentiment scores
        bullish_score = 0
        bearish_score = 0
        volatility_score = 0
        
        total_words = len(words)
        
        for word in words:
            if word in self.bullish_keywords:
                bullish_score += self.bullish_keywords[word]
            elif word in self.bearish_keywords:
                bearish_score += self.bearish_keywords[word]
            elif word in self.volatility_keywords:
                volatility_score += self.volatility_keywords[word]
        
        # Normalize scores by number of titles
        num_titles = len(news_titles)
        bullish_score = bullish_score / num_titles if num_titles > 0 else 0
        bearish_score = bearish_score / num_titles if num_titles > 0 else 0
        volatility_score = volatility_score / num_titles if num_titles > 0 else 0
        
        # Determine overall sentiment
        net_score = bullish_score - bearish_score
        
        if net_score > 1.0:
            sentiment = 'Bullish'
        elif net_score < -1.0:
            sentiment = 'Bearish'
        else:
            sentiment = 'Neutral'
        
        # Calculate confidence (0-10 scale)
        total_sentiment_score = bullish_score + bearish_score
        confidence = min(10, int(total_sentiment_score * 2))
        
        # Generate explanation
        explanation = self._generate_explanation(
            bullish_score, bearish_score, volatility_score, sentiment
        )
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'explanation': explanation,
            'scores': {
                'bullish': round(bullish_score, 2),
                'bearish': round(bearish_score, 2),
                'volatility': round(volatility_score, 2),
                'net': round(net_score, 2)
            }
        }
    
    def _generate_explanation(self, bullish: float, bearish: float, 
                            volatility: float, sentiment: str) -> str:
        """Generate explanation based on scores"""
        
        explanations = []
        
        if sentiment == 'Bullish':
            explanations.append("Positive market sentiment from news")
            if bullish > 2:
                explanations.append("Strong bullish indicators in headlines")
        elif sentiment == 'Bearish':
            explanations.append("Negative market sentiment from news")
            if bearish > 2:
                explanations.append("Strong bearish indicators in headlines")
        else:
            explanations.append("Mixed or neutral market sentiment")
        
        if volatility > 1:
            explanations.append("High volatility expected")
        
        return ". ".join(explanations) + "."

def test_local_sentiment():
    """Test local sentiment analyzer"""
    analyzer = LocalSentimentAnalyzer()
    
    # Test cases
    test_cases = [
        ["Bitcoin surges to new highs as institutional adoption grows"],
        ["Crypto market crashes amid regulatory crackdown fears"],
        ["Mixed signals in crypto market with volatile trading"],
        ["Ethereum rally continues, BTC gains momentum"],
        ["Market sees bearish sentiment as prices plunge"]
    ]
    
    print("🧪 Testing Local Sentiment Analysis:")
    print("=" * 50)
    
    for i, titles in enumerate(test_cases, 1):
        result = analyzer.analyze_sentiment(titles)
        print(f"\nTest {i}: {titles[0][:60]}...")
        print(f"Sentiment: {result['sentiment']}")
        print(f"Confidence: {result['confidence']}/10")
        print(f"Explanation: {result['explanation']}")
        print(f"Scores: {result['scores']}")

if __name__ == "__main__":
    test_local_sentiment()