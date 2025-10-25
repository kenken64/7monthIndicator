# 🤖 Flexible LLM Provider Integration

Your trading bot now supports **multiple LLM providers** - easily switch between **OpenAI** and **DeepSeek** (or add your own) without changing a single line of code!

## 🚀 Quick Start (2 Minutes)

### Step 1: Choose Your Provider

Edit your `.env` file:

```bash
# Option A: Use OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here

# Option B: Use DeepSeek (cost-effective)
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
```

### Step 2: That's It!

Run your bot as usual:
```bash
python trading_bot.py
```

All AI features now use your chosen provider automatically! ✨

## 💰 Cost Comparison

| Provider | Text Tasks | Vision Tasks | Savings |
|----------|-----------|--------------|---------|
| OpenAI | $2-15/1M tokens | ✅ Supported | Baseline |
| DeepSeek | $0.27-1.10/1M tokens | ❌ Not yet | **~85% cheaper** |

**Recommendation**: Use DeepSeek for text (news sentiment, CrewAI) and OpenAI for vision (chart analysis).

## 📚 Documentation

- **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - What changed and why
- **[LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md)** - Complete usage guide
- **[test_llm_integration.py](test_llm_integration.py)** - Test suite

## ✅ What Works

All your existing features work with both providers:

- ✅ **News Sentiment Analysis** - AI-powered market sentiment
- ✅ **Chart Analysis** - Vision-based chart pattern recognition (OpenAI only)
- ✅ **CrewAI Agents** - Multi-agent trading system
- ✅ **Web Dashboard** - Real-time sentiment display
- ✅ **Backward Compatibility** - Zero code changes needed

## 🧪 Testing

Verify everything works:

```bash
# Test with your current provider
python test_llm_integration.py

# Test with OpenAI
LLM_PROVIDER=openai python test_llm_integration.py

# Test with DeepSeek
LLM_PROVIDER=deepseek python test_llm_integration.py
```

## 🔑 Get API Keys

### OpenAI
1. Visit https://platform.openai.com/api-keys
2. Create new API key
3. Add to `.env` as `OPENAI_API_KEY=sk-...`

### DeepSeek
1. Visit https://platform.deepseek.com/api_keys
2. Create new API key
3. Add to `.env` as `DEEPSEEK_API_KEY=sk-...`

## 🎯 Use Cases

### Scenario 1: Cost Optimization
```bash
# Use DeepSeek for everything (85% cost savings)
LLM_PROVIDER=deepseek
```
**Note**: Chart analysis will fall back to text-only mode.

### Scenario 2: Full Features
```bash
# Use OpenAI for all features including vision
LLM_PROVIDER=openai
```

### Scenario 3: Hybrid (Best Value)
```bash
# Use DeepSeek by default
LLM_PROVIDER=deepseek

# Override for specific modules that need vision:
# - chart_analysis_bot.py will detect and warn about vision limitations
# - You can manually switch for those tasks
```

## 🛠️ Technical Details

### Architecture
```
Your Code
    ↓
llm_provider.py (Abstraction Layer)
    ↓
┌─────────┴──────────┐
OpenAI         DeepSeek
Provider       Provider
```

### New Files
- `llm_provider.py` - Core abstraction
- `langchain_deepseek.py` - CrewAI integration
- `llm_news_sentiment.py` - Refactored sentiment module

### Modified Files
- `openai_news_sentiment.py` - Now a compatibility wrapper
- `chart_analysis_bot.py` - Uses LLM provider
- `crewai_agents.py` - LangChain integration
- `web_dashboard.py` - Provider-agnostic sentiment
- `.env.example` - Added provider config
- `requirements.txt` - Added dependencies

## ❓ FAQ

**Q: Do I need to change my code?**
A: No! All existing code works without changes.

**Q: Can I switch providers anytime?**
A: Yes, just change `LLM_PROVIDER` in `.env` and restart.

**Q: Does DeepSeek support chart analysis?**
A: Not yet (no vision API). It will fall back to text-only analysis.

**Q: Which is better?**
A: OpenAI for vision tasks, DeepSeek for text (85% cheaper).

**Q: Can I use both?**
A: Yes! Set one as default, override per module if needed.

## 🐛 Troubleshooting

### "API key not found"
```bash
# Check your .env file has:
OPENAI_API_KEY=sk-...  # for OpenAI
# or
DEEPSEEK_API_KEY=sk-... # for DeepSeek
```

### "Vision not supported"
```bash
# This is expected with DeepSeek
# Solution: Use OpenAI for chart analysis
LLM_PROVIDER=openai
```

### Test Connection
```bash
python test_llm_integration.py
```

## 📈 Next Steps

1. ✅ Set `LLM_PROVIDER` in `.env`
2. ✅ Add your API key
3. ✅ Run tests: `python test_llm_integration.py`
4. ✅ Start trading bot as usual
5. 📊 Monitor costs and adjust provider

## 🎉 Benefits

- ✅ **Zero Code Changes** - Everything works as before
- 💰 **Cost Savings** - Up to 85% with DeepSeek
- 🔧 **Easy Switching** - Change provider in seconds
- 🚀 **Future Proof** - Easy to add more providers
- 📚 **Well Documented** - Complete guides included
- 🧪 **Fully Tested** - Comprehensive test suite

---

**Happy Trading!** 🚀📈

For detailed information, see [LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md)
