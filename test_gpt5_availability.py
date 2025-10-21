#!/usr/bin/env python3
"""
Test GPT-5 Model Availability in Singapore
Checks which OpenAI models are accessible in your account
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_model_availability():
    """Test which models are available"""
    # Read API key from Docker secrets or environment
    api_key = None
    secrets_path = '/run/secrets/openai_api_key'

    if os.path.exists(secrets_path):
        with open(secrets_path, 'r') as f:
            api_key = f.read().strip()
        print(f"✅ Loaded API key from Docker secrets\n")
    else:
        api_key = os.getenv('OPENAI_API_KEY')
        print(f"✅ Loaded API key from environment\n")

    if not api_key:
        raise ValueError("OpenAI API key not found in secrets or environment")

    client = OpenAI(api_key=api_key)

    print("=" * 60)
    print("TESTING OPENAI MODEL AVAILABILITY (SINGAPORE)")
    print("=" * 60)
    print()

    # Models to test
    models_to_test = [
        # Current models
        ('gpt-4o', 'Current - Chart Analysis'),
        ('gpt-4o-mini', 'Current - CrewAI & News'),

        # GPT-5 series (if available)
        ('gpt-5', 'New - Replacement for gpt-4o'),
        ('gpt-5-mini', 'New - Alternative to gpt-4o-mini'),
        ('gpt-5-nano', 'New - Most cost-effective'),

        # o1 series
        ('o1', 'Reasoning - Expensive'),
        ('o1-mini', 'Reasoning - Budget'),
    ]

    available_models = []

    for model_name, description in models_to_test:
        try:
            print(f"Testing: {model_name:20s} ({description})")

            # Test with a minimal API call
            # Note: o1 and gpt-5 series don't support max_tokens parameter
            params = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": "Hi"}
                ]
            }

            # Only add max_tokens for older models
            if not model_name.startswith(('gpt-5', 'o1')):
                params["max_tokens"] = 5

            response = client.chat.completions.create(**params)

            # Get usage info
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            print(f"  ✅ AVAILABLE - Used {input_tokens} input / {output_tokens} output tokens")
            available_models.append((model_name, description))
            print()

        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg or "model_not_found" in error_msg:
                print(f"  ❌ NOT AVAILABLE - Model not found")
            else:
                print(f"  ⚠️  ERROR - {error_msg[:100]}")
            print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()

    if available_models:
        print("Available Models for Migration:")
        for model_name, description in available_models:
            print(f"  ✅ {model_name:20s} - {description}")
    else:
        print("No new models available yet. Current setup is optimal.")

    print()
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_model_availability()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nNote: Make sure OPENAI_API_KEY is set in your .env file")
