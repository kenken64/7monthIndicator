#!/usr/bin/env python3
"""
OpenAI News Sentiment Analysis Module (Backward Compatibility Wrapper)

IMPORTANT: This module now uses the configurable LLM provider system.
For new code, use llm_news_sentiment.py instead.

This wrapper maintains backward compatibility with existing code while
supporting both OpenAI and DeepSeek providers based on LLM_PROVIDER env var.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger with Singapore timezone
try:
    from timezone_utils import setup_singapore_logging
    logger = setup_singapore_logging(
        logger_name=__name__,
        level=logging.INFO,
        log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S SGT',
        console=True
    )
except ImportError:
    # Fallback to standard logging if timezone_utils not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

# Import the new LLM-based implementation
from llm_news_sentiment import LLMNewsSentiment


class OpenAINewsSentiment(LLMNewsSentiment):
    """
    Backward compatibility wrapper for OpenAI News Sentiment
    Now uses the unified LLM provider system
    """

    def __init__(self):
        """Initialize using the configured LLM provider"""
        # Call parent class which handles provider initialization
        super().__init__(provider_name=None)  # Uses LLM_PROVIDER env var
        logger.info("✅ OpenAI News Sentiment Analyzer initialized (using LLM provider system)")


# Legacy test function maintained for backward compatibility
def test_openai_news_sentiment():
    """Test the LLM news sentiment analyzer (backward compatibility)"""
    from llm_news_sentiment import test_llm_news_sentiment
    test_llm_news_sentiment()


if __name__ == "__main__":
    test_openai_news_sentiment()
