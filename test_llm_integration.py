#!/usr/bin/env python3
"""
Test script for LLM provider integration
Tests both OpenAI and DeepSeek providers if configured
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_llm_provider():
    """Test the base LLM provider abstraction"""
    print("=" * 60)
    print("Testing LLM Provider Abstraction")
    print("=" * 60)

    try:
        from llm_provider import get_llm_provider, LLMProviderFactory

        # Show available providers
        available = LLMProviderFactory.get_available_providers()
        print(f"✅ Available providers: {', '.join(available)}")

        # Get current provider
        current_provider = os.getenv('LLM_PROVIDER', 'openai')
        print(f"📍 Current provider: {current_provider}")

        # Test provider initialization
        provider = get_llm_provider()
        print(f"✅ Provider initialized: {provider.__class__.__name__}")

        # Test simple completion
        print("\n🧪 Testing simple chat completion...")
        response = provider.chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, World!' in exactly 2 words."}
            ],
            model=provider.get_model_name("fast"),
            temperature=0.1,
            max_tokens=50
        )

        print(f"✅ Response received: {response['content'][:100]}")
        print(f"✅ Model used: {response['model']}")
        print(f"✅ Tokens: {response['usage']['total_tokens']}")

        return True

    except Exception as e:
        print(f"❌ LLM Provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_langchain_integration():
    """Test LangChain integration for CrewAI"""
    print("\n" + "=" * 60)
    print("Testing LangChain Integration")
    print("=" * 60)

    try:
        from langchain_deepseek import get_langchain_llm
        from langchain_core.messages import HumanMessage, SystemMessage

        current_provider = os.getenv('LLM_PROVIDER', 'openai')
        print(f"📍 Testing with provider: {current_provider}")

        # Get LangChain LLM
        llm = get_langchain_llm()
        print(f"✅ LangChain LLM initialized: {llm.__class__.__name__}")

        # Test simple invocation
        print("\n🧪 Testing LangChain message invocation...")
        messages = [
            SystemMessage(content="You are a brief assistant."),
            HumanMessage(content="What is 2+2? Answer in one word.")
        ]

        result = llm.invoke(messages)
        print(f"✅ Response: {result.content}")

        return True

    except Exception as e:
        print(f"❌ LangChain integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_news_sentiment():
    """Test news sentiment analysis"""
    print("\n" + "=" * 60)
    print("Testing News Sentiment Analysis")
    print("=" * 60)

    try:
        from llm_news_sentiment import LLMNewsSentiment

        current_provider = os.getenv('LLM_PROVIDER', 'openai')
        print(f"📍 Testing with provider: {current_provider}")

        # Initialize analyzer
        analyzer = LLMNewsSentiment()
        print("✅ News sentiment analyzer initialized")

        # Test with sample news
        print("\n🧪 Testing sentiment analysis with sample news...")
        sample_news = [
            "SUI price surges 15% on major partnership announcement",
            "Cryptocurrency market shows strong bullish momentum",
            "DeFi adoption continues to grow across major blockchains"
        ]

        result = analyzer.analyze_sentiment(sample_news)
        print(f"✅ Sentiment: {result['sentiment']}")
        print(f"✅ Score: {result['sentiment_score']:.2f}")
        print(f"✅ Confidence: {result['confidence']}%")
        print(f"✅ Explanation: {result['explanation']}")

        return True

    except Exception as e:
        print(f"❌ News sentiment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test backward compatibility with old OpenAI classes"""
    print("\n" + "=" * 60)
    print("Testing Backward Compatibility")
    print("=" * 60)

    try:
        from openai_news_sentiment import OpenAINewsSentiment

        print("🧪 Testing old OpenAINewsSentiment class...")
        analyzer = OpenAINewsSentiment()
        print("✅ Backward compatibility wrapper works!")

        # Test basic functionality
        sample_news = [
            "Market shows positive trend",
            "Trading volume increases significantly"
        ]

        result = analyzer.analyze_sentiment(sample_news)
        print(f"✅ Sentiment analysis works: {result['sentiment']}")

        return True

    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n🚀 LLM Provider Integration Test Suite")
    print("=" * 60)

    # Check configuration
    current_provider = os.getenv('LLM_PROVIDER', 'openai')
    print(f"\n📋 Configuration:")
    print(f"   LLM_PROVIDER: {current_provider}")

    if current_provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY', '')
        print(f"   OPENAI_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    elif current_provider == 'deepseek':
        api_key = os.getenv('DEEPSEEK_API_KEY', '')
        print(f"   DEEPSEEK_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")

    if not api_key:
        print("\n❌ API key not configured. Please set the appropriate API key in .env")
        return False

    print("\n" + "=" * 60)

    # Run tests
    results = {
        "LLM Provider": test_llm_provider(),
        "LangChain Integration": test_langchain_integration(),
        "News Sentiment": test_news_sentiment(),
        "Backward Compatibility": test_backward_compatibility()
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<40} {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)

    if all_passed:
        print("✅ All tests passed! LLM integration is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")

    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
