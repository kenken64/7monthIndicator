# Quick Start: Testing the Web Dashboard

This guide will get you up and running with automated tests for the web dashboard in under 5 minutes.

## 1. Install Testing Dependencies

```bash
cd /root/7monthIndicator

# Install all testing dependencies
pip install pytest pytest-cov pytest-mock pytest-timeout pytest-flask

# Optional: Install for E2E browser tests
pip install playwright pytest-playwright
python -m playwright install chromium
```

## 2. Verify Installation

```bash
pytest --version
# Should show: pytest 8.x.x or higher
```

## 3. Run Your First Tests

### Run Integration Tests (Recommended to start)

```bash
# Run web dashboard integration tests
pytest tests/integration/test_web_dashboard_integration.py -v

# Expected output:
# ✓ Multiple tests should PASS
# ✓ Tests use temporary database (no side effects)
# ✓ External APIs are mocked (no real API calls)
```

### Run with Coverage Report

```bash
# See which parts of web_dashboard.py are tested
pytest tests/integration/test_web_dashboard_integration.py -v \
  --cov=web_dashboard \
  --cov-report=term-missing

# Shows coverage percentage and untested lines
```

### Run Specific Test

```bash
# Run just one test to verify setup
pytest tests/integration/test_web_dashboard_integration.py::TestWebDashboardIntegration::test_dashboard_index_loads -v
```

## 4. Understand Test Output

### Passing Test ✓
```
tests/integration/test_web_dashboard_integration.py::TestWebDashboardIntegration::test_dashboard_index_loads PASSED
```
**Meaning:** The dashboard index page loads successfully.

### Failing Test ✗
```
tests/integration/test_web_dashboard_integration.py::TestWebDashboardIntegration::test_api_data_with_populated_database FAILED

AssertionError: assert 'signals' in data
```
**Meaning:** API response missing 'signals' key - indicates a bug in the endpoint.

## 5. Common Test Commands

```bash
# Run all web dashboard integration tests
pytest tests/integration/test_web_dashboard_integration.py -v

# Run with detailed output on failures
pytest tests/integration/test_web_dashboard_integration.py -vv

# Stop on first failure (useful for debugging)
pytest tests/integration/test_web_dashboard_integration.py -x

# Run only tests matching a pattern
pytest tests/integration/test_web_dashboard_integration.py -k "api_data" -v

# Generate HTML coverage report
pytest tests/integration/test_web_dashboard_integration.py \
  --cov=web_dashboard \
  --cov-report=html
# Then open: htmlcov/index.html

# Run tests and show print statements
pytest tests/integration/test_web_dashboard_integration.py -v -s
```

## 6. Understanding the Test Structure

### What Gets Tested?

**✓ API Endpoints**
- `/api/data/<symbol>` - Trading data
- `/api/chart-data/<symbol>` - Chart data
- `/api/system-stats` - System statistics
- `/api/rl-status` - RL bot status
- `/api/unified-signals/<symbol>` - Unified signal data
- `/api/news` - Market news
- `/api/market-context` - Market context data

**✓ Database Integration**
- Signal storage and retrieval
- Trade tracking
- Performance metrics calculation
- Data consistency

**✓ Security**
- PIN verification for bot control
- Input validation
- Error handling

### What Gets Mocked?

**External services are mocked to keep tests fast and reliable:**
- Binance API (no real trading)
- OpenAI API (no real API costs)
- NewsAPI (no rate limits)
- Network requests

**Database uses temporary files:**
- Each test gets fresh database
- No pollution between tests
- Auto-cleanup after tests

## 7. Troubleshooting

### Issue: Import errors

```bash
# Make sure you're in project root
cd /root/7monthIndicator
pytest tests/integration/test_web_dashboard_integration.py -v
```

### Issue: Database errors

**Solution:** Tests use `temp_database` fixture - no manual setup needed.

### Issue: Module not found

```bash
# Ensure dependencies installed
pip install -r requirements.txt
```

### Issue: Tests pass but coverage is low

**Solution:** This is expected initially. Coverage improves as you add more tests.

## 8. Next Steps

### Add More Tests

Based on the comprehensive guide in `WEB_DASHBOARD_TESTING_GUIDE.md`:

1. **Unit tests** - Test individual functions
2. **E2E tests** - Test full user workflows in browser

### Run Tests Before Commits

```bash
# Quick check before committing
pytest tests/integration/test_web_dashboard_integration.py -v

# Full check with coverage
pytest tests/integration/test_web_dashboard_integration.py -v \
  --cov=web_dashboard \
  --cov-report=term-missing
```

### Set Up CI/CD

Add tests to run automatically on every commit (see `WEB_DASHBOARD_TESTING_GUIDE.md` for GitHub Actions setup).

## 9. Test Development Workflow

### When adding a new feature to web_dashboard.py:

1. **Write test first** (TDD approach):
   ```python
   def test_new_feature(self, client, populated_db):
       """Test my new feature"""
       response = client.get('/api/new-endpoint')
       assert response.status_code == 200
   ```

2. **Run test** (should fail):
   ```bash
   pytest tests/integration/test_web_dashboard_integration.py::TestWebDashboardIntegration::test_new_feature -v
   ```

3. **Implement feature** in `web_dashboard.py`

4. **Run test again** (should pass):
   ```bash
   pytest tests/integration/test_web_dashboard_integration.py::TestWebDashboardIntegration::test_new_feature -v
   ```

5. **Check coverage**:
   ```bash
   pytest tests/integration/test_web_dashboard_integration.py --cov=web_dashboard
   ```

## 10. Useful pytest Options

```bash
# Run tests in parallel (faster)
pip install pytest-xdist
pytest tests/integration/test_web_dashboard_integration.py -n auto

# Run tests with timeout (prevent hanging)
pytest tests/integration/test_web_dashboard_integration.py --timeout=60

# Show slowest tests
pytest tests/integration/test_web_dashboard_integration.py --durations=10

# Generate JUnit XML report (for CI/CD)
pytest tests/integration/test_web_dashboard_integration.py --junitxml=test-results.xml

# Run in verbose mode with color
pytest tests/integration/test_web_dashboard_integration.py -v --color=yes
```

## Summary Cheat Sheet

```bash
# Essential commands
pytest tests/integration/test_web_dashboard_integration.py -v              # Run all tests
pytest tests/integration/test_web_dashboard_integration.py -v --cov        # With coverage
pytest tests/integration/test_web_dashboard_integration.py -v -k "api"     # Run specific tests
pytest tests/integration/test_web_dashboard_integration.py -v -x           # Stop on first failure

# View detailed guide
cat WEB_DASHBOARD_TESTING_GUIDE.md

# View test structure
cat tests/README.md
```

## Help & Resources

- **Comprehensive Guide:** `WEB_DASHBOARD_TESTING_GUIDE.md`
- **Test Suite Docs:** `tests/README.md`
- **pytest docs:** https://docs.pytest.org/
- **pytest-flask docs:** https://pytest-flask.readthedocs.io/

---

**Ready to test!** Run your first test now:

```bash
pytest tests/integration/test_web_dashboard_integration.py::TestWebDashboardIntegration::test_dashboard_index_loads -v
```

If it passes ✓, you're all set!
