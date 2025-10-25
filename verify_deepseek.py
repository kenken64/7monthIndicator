#!/usr/bin/env python3
"""
Quick verification script for DeepSeek integration
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 60)
print("DeepSeek Integration Verification")
print("=" * 60)

# Check configuration
provider = os.getenv('LLM_PROVIDER')
deepseek_key = os.getenv('DEEPSEEK_API_KEY')

print(f"\n✅ LLM_PROVIDER: {provider}")
print(f"✅ DEEPSEEK_API_KEY: {'Set (' + deepseek_key[:10] + '...' + deepseek_key[-4:] + ')' if deepseek_key else 'Not set'}")

if provider != 'deepseek':
    print(f"\n⚠️  Warning: LLM_PROVIDER is set to '{provider}', not 'deepseek'")

if not deepseek_key:
    print("\n❌ DeepSeek API key not found!")
    exit(1)

print("\n" + "=" * 60)
print("Testing DeepSeek API Connection")
print("=" * 60)

try:
    from llm_provider import get_llm_provider

    provider_obj = get_llm_provider()
    print(f"\n✅ Provider initialized: {provider_obj.__class__.__name__}")

    # Test simple query
    print("\n🧪 Testing simple query: 'What is 2+2?'")
    response = provider_obj.chat_completion(
        messages=[
            {"role": "user", "content": "What is 2+2? Answer with just the number."}
        ],
        model=provider_obj.get_model_name("fast"),
        temperature=0.1,
        max_tokens=10
    )

    print(f"✅ Response: {response['content']}")
    print(f"✅ Model: {response['model']}")
    print(f"✅ Tokens used: {response['usage']['total_tokens']}")

    # Test JSON mode
    print("\n🧪 Testing JSON mode")
    response = provider_obj.chat_completion(
        messages=[
            {"role": "user", "content": "Analyze this sentiment: 'Bitcoin price is rising'. Respond with JSON: {\"sentiment\": \"positive/negative/neutral\", \"confidence\": 0-100}"}
        ],
        model=provider_obj.get_model_name("fast"),
        temperature=0.1,
        max_tokens=100,
        response_format={"type": "json_object"}
    )

    import json
    parsed = json.loads(response['content'])
    print(f"✅ JSON Response: {parsed}")

    print("\n" + "=" * 60)
    print("✅ All checks passed! DeepSeek is ready to use!")
    print("=" * 60)

    print("\n📊 Next Steps:")
    print("  1. Your bot is now configured to use DeepSeek")
    print("  2. Run your trading bot normally")
    print("  3. Monitor costs (DeepSeek is ~85% cheaper than OpenAI)")
    print("\n💰 Cost savings example:")
    print("  - OpenAI gpt-4o: $5.00/1M input tokens")
    print("  - DeepSeek: $0.27/1M input tokens")
    print("  - Savings: ~95% on input tokens!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
