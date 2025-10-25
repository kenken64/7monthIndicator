# LLM Provider Integration Guide

## Overview

The trading bot now supports **flexible LLM provider integration**, allowing you to choose between **OpenAI** and **DeepSeek** (or add your own custom providers). This guide explains how to configure and use different LLM providers.

## Supported Providers

1. **OpenAI** - Premium AI models with vision capabilities
2. **DeepSeek** - Cost-effective alternative with OpenAI-compatible API

## Quick Start

### 1. Configure Your Provider

Add these variables to your `.env` file:

```bash
# Choose your LLM provider: "openai" or "deepseek"
LLM_PROVIDER=openai

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key_here

# DeepSeek Configuration (if using DeepSeek)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 2. Get API Keys

#### OpenAI
- Visit: https://platform.openai.com/api-keys
- Create a new API key
- Add to `.env` as `OPENAI_API_KEY`

#### DeepSeek
- Visit: https://platform.deepseek.com/api_keys
- Create a new API key
- Add to `.env` as `DEEPSEEK_API_KEY`

### 3. Switch Providers

Simply change the `LLM_PROVIDER` environment variable:

```bash
# Use OpenAI
LLM_PROVIDER=openai

# Use DeepSeek
LLM_PROVIDER=deepseek
```

No code changes required! All modules will automatically use the selected provider.

## Architecture

### Core Components

#### 1. `llm_provider.py` - Unified LLM Abstraction
The core abstraction layer that provides a consistent interface across different LLM providers.

**Key Classes:**
- `LLMProvider` - Abstract base class
- `OpenAIProvider` - OpenAI implementation
- `DeepSeekProvider` - DeepSeek implementation
- `LLMProviderFactory` - Factory for creating providers

**Usage Example:**
```python
from llm_provider import get_llm_provider

# Get provider based on LLM_PROVIDER env var
provider = get_llm_provider()

# Chat completion
response = provider.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello!"}
    ],
    model=provider.get_model_name("fast"),
    temperature=0.7
)

print(response['content'])
```

#### 2. `langchain_deepseek.py` - LangChain Integration
Provides LangChain-compatible wrapper for DeepSeek, enabling use with CrewAI.

**Key Classes:**
- `ChatDeepSeek` - LangChain-compatible DeepSeek wrapper
- `get_langchain_llm()` - Factory function for LangChain LLMs

**Usage Example:**
```python
from langchain_deepseek import get_langchain_llm

# Get LangChain LLM
llm = get_langchain_llm("deepseek", model="deepseek-chat", temperature=0.7)

# Use with CrewAI agents
from crewai import Agent
agent = Agent(
    role="Market Analyst",
    goal="Analyze market trends",
    llm=llm
)
```

#### 3. `llm_news_sentiment.py` - News Sentiment Analysis
Refactored news sentiment module that supports multiple providers.

**Key Classes:**
- `LLMNewsSentiment` - Main sentiment analyzer (provider-agnostic)
- `OpenAINewsSentiment` - Backward compatibility wrapper

**Migration:**
```python
# Old code (still works via compatibility wrapper)
from openai_news_sentiment import OpenAINewsSentiment
analyzer = OpenAINewsSentiment()

# New code (recommended)
from llm_news_sentiment import LLMNewsSentiment
analyzer = LLMNewsSentiment()  # Uses LLM_PROVIDER env var
```

## Module Updates

### Refactored Modules

All the following modules now support flexible LLM providers:

1. **`openai_news_sentiment.py`** → Backward compatible wrapper
2. **`llm_news_sentiment.py`** → New implementation with LLM provider support
3. **`chart_analysis_bot.py`** → Chart analysis with vision support
4. **`crewai_agents.py`** → CrewAI agents with LangChain integration
5. **`web_dashboard.py`** → Web dashboard sentiment analysis

### Backward Compatibility

All existing code continues to work without modifications:

```python
# This still works!
from openai_news_sentiment import OpenAINewsSentiment
analyzer = OpenAINewsSentiment()
result = analyzer.get_news_and_sentiment()
```

But now respects the `LLM_PROVIDER` environment variable.

## Model Mappings

### OpenAI Models

| Model Type | Model Name | Use Case |
|-----------|-----------|----------|
| `default` | gpt-5-nano | Cost-effective default |
| `fast` | gpt-5-nano | Quick responses |
| `smart` | gpt-4o | Complex reasoning |
| `vision` | gpt-4o | Image analysis |
| `mini` | gpt-4o-mini | Balanced performance |

### DeepSeek Models

| Model Type | Model Name | Use Case |
|-----------|-----------|----------|
| `default` | deepseek-chat | General purpose |
| `fast` | deepseek-chat | Quick responses |
| `smart` | deepseek-chat | Complex reasoning |
| `vision` | deepseek-chat | (Falls back to text-only) |
| `coder` | deepseek-coder | Code generation |

## Feature Comparison

| Feature | OpenAI | DeepSeek |
|---------|--------|----------|
| Chat Completion | ✅ | ✅ |
| JSON Mode | ✅ | ⚠️ (via prompt) |
| Vision API | ✅ | ❌ (text-only fallback) |
| Streaming | ✅ | ✅ |
| Function Calling | ✅ | ⚠️ (limited) |
| Cost | Higher | Lower |

## Configuration Examples

### Basic Configuration

```bash
# .env file
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### Dual Provider Setup

```bash
# Keep both providers configured for easy switching
LLM_PROVIDER=deepseek

# OpenAI (fallback)
OPENAI_API_KEY=sk-...

# DeepSeek (active)
DEEPSEEK_API_KEY=sk-...
```

### CrewAI Configuration

Update `config/crewai_spike_agent.yaml`:

```yaml
llm:
  provider: "deepseek"  # or "openai"
  model: "deepseek-chat"
  temperature: 0.2
  max_tokens: 1000
```

## Usage Patterns

### Pattern 1: Direct Provider Usage

```python
from llm_provider import get_llm_provider

provider = get_llm_provider()  # Uses LLM_PROVIDER env var

# Simple chat
response = provider.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    model=provider.get_model_name("fast")
)
```

### Pattern 2: Vision Analysis (Chart Analysis)

```python
from llm_provider import get_llm_provider
import base64

provider = get_llm_provider()

# Encode image
with open("chart.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Analyze with vision
response = provider.chat_completion_with_vision(
    messages=[{"role": "user", "content": "Analyze this chart"}],
    image_data=image_data,
    model=provider.get_model_name("vision")
)
```

### Pattern 3: CrewAI Integration

```python
from langchain_deepseek import get_langchain_llm
from crewai import Agent, Task, Crew

# Get LangChain-compatible LLM
llm = get_langchain_llm()  # Uses LLM_PROVIDER env var

# Create agent
analyst = Agent(
    role="Market Analyst",
    goal="Analyze cryptocurrency markets",
    backstory="Expert in technical analysis",
    llm=llm
)

# Create task
task = Task(
    description="Analyze current SUI market conditions",
    agent=analyst
)

# Execute
crew = Crew(agents=[analyst], tasks=[task])
result = crew.kickoff()
```

## Cost Optimization

### DeepSeek Advantages

- **Lower API costs** compared to OpenAI
- **OpenAI-compatible API** for easy migration
- **Fast response times**

### Recommended Strategy

1. **Development**: Use DeepSeek for cost savings
2. **Production**: Use OpenAI for vision features, DeepSeek for text-only
3. **Hybrid**: Use DeepSeek for news sentiment, OpenAI for chart analysis

### Example Hybrid Setup

```python
# chart_analysis_bot.py - Requires vision (OpenAI)
os.environ['LLM_PROVIDER'] = 'openai'

# news_sentiment.py - Text-only (DeepSeek)
os.environ['LLM_PROVIDER'] = 'deepseek'
```

## Troubleshooting

### Issue: "DeepSeek API key not found"

**Solution:**
```bash
export DEEPSEEK_API_KEY=your_key_here
# or add to .env file
```

### Issue: "Vision not supported with DeepSeek"

**Expected behavior**: DeepSeek doesn't support vision yet. The system will:
1. Log a warning
2. Fall back to text-only analysis
3. Extract text from image description

**Solution:** Use OpenAI for vision tasks:
```bash
LLM_PROVIDER=openai
```

### Issue: "JSON parsing failed"

**Cause**: DeepSeek doesn't support `response_format={"type": "json_object"}`

**Solution**: The system automatically adds JSON instructions to the prompt for DeepSeek.

## Testing

### Test LLM Provider

```bash
# Test OpenAI
LLM_PROVIDER=openai python llm_provider.py

# Test DeepSeek
LLM_PROVIDER=deepseek python llm_provider.py
```

### Test News Sentiment

```bash
# Test with current provider
python llm_news_sentiment.py

# Test specific provider
LLM_PROVIDER=deepseek python llm_news_sentiment.py
```

### Test LangChain Integration

```bash
# Test DeepSeek LangChain wrapper
python langchain_deepseek.py
```

## Migration Checklist

- [ ] Add `LLM_PROVIDER` to `.env` file
- [ ] Add provider API key (OPENAI_API_KEY or DEEPSEEK_API_KEY)
- [ ] Update `config/crewai_spike_agent.yaml` if using CrewAI
- [ ] Test all modules with new provider
- [ ] Monitor API costs and adjust provider as needed
- [ ] Update documentation for your team

## Advanced: Adding Custom Providers

To add a new LLM provider (e.g., Anthropic, Cohere):

1. **Create Provider Class** in `llm_provider.py`:

```python
class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        # ... initialization

    def chat_completion(self, messages, model, ...):
        # Implement Anthropic API call
        pass

    def get_model_name(self, model_type: str = "default") -> str:
        # Return Anthropic model names
        pass
```

2. **Update Factory** in `llm_provider.py`:

```python
def create_provider(provider_name: Optional[str] = None) -> LLMProvider:
    if provider_name == "anthropic":
        return AnthropicProvider()
    # ... existing providers
```

3. **Add LangChain Wrapper** (optional for CrewAI):

```python
# In langchain_anthropic.py
class ChatAnthropic(BaseChatModel):
    # Implement LangChain interface
    pass
```

## Best Practices

1. **Environment Variables**: Always use environment variables for API keys
2. **Provider Selection**: Choose based on your use case:
   - Vision tasks → OpenAI
   - Text-only → DeepSeek (cost-effective)
   - Complex reasoning → OpenAI gpt-4o
3. **Error Handling**: All modules have fallback mechanisms
4. **Testing**: Test thoroughly when switching providers
5. **Monitoring**: Track API costs for each provider

## Support

For issues or questions:
- Check environment variables are set correctly
- Review logs for specific error messages
- Test with simple examples first
- Ensure API keys have proper permissions

## Resources

- **OpenAI API Docs**: https://platform.openai.com/docs
- **DeepSeek API Docs**: https://platform.deepseek.com/docs
- **LangChain Docs**: https://python.langchain.com/docs
- **CrewAI Docs**: https://docs.crewai.com

---

**Note**: This integration maintains full backward compatibility. All existing code continues to work without modifications while gaining the flexibility to switch providers via environment variables.
