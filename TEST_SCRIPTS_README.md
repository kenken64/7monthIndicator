# Test Execution Scripts

This directory contains automated test execution scripts for the 7monthIndicator Trading Bot.

## Available Scripts

### 1. `run_tests.sh` - Full Test Suite Runner

**Comprehensive test runner with multiple options and detailed reporting.**

#### Basic Usage

```bash
# Run all tests
./run_tests.sh

# Run with coverage report
./run_tests.sh --coverage

# Run only unit tests (fast)
./run_tests.sh --unit

# Run only integration tests
./run_tests.sh --integration

# Run with verbose output
./run_tests.sh --verbose
```

#### All Options

```bash
./run_tests.sh [OPTIONS]

OPTIONS:
  --unit              Run only unit tests (fast, isolated)
  --integration       Run only integration tests (component interaction)
  --e2e               Run only end-to-end tests (full system)
  --coverage          Run all tests with coverage report
  --fast              Run only fast unit tests
  --verbose, -v       Run with verbose output
  --help, -h          Show help message
```

#### Examples

```bash
# Quick validation with unit tests only
./run_tests.sh --fast

# Full test suite with coverage
./run_tests.sh --coverage

# Integration tests only with verbose output
./run_tests.sh --integration --verbose

# Run all tests categories
./run_tests.sh --unit --integration
```

#### Output

- **Console**: Colored output with test results
- **Coverage Report**: `htmlcov/index.html` (if `--coverage` used)
- **JUnit XML**: `test-results/*.xml` (for CI/CD integration)

---

### 2. `quick_test.sh` - Fast Validation

**Simple script for quick validation during development.**

#### Usage

```bash
./quick_test.sh
```

#### What It Does

- Runs only unit tests (fastest tests)
- Minimal output, focused on pass/fail
- Auto-installs pytest if missing
- Perfect for pre-commit validation

#### When to Use

- ✅ Before committing changes
- ✅ During active development
- ✅ Quick sanity check
- ✅ When you want fast feedback

---

## Test Categories Explained

### Unit Tests
- **Speed**: < 1 second per test
- **Scope**: Individual functions/routes
- **Dependencies**: All mocked
- **Location**: `tests/unit/`

### Integration Tests
- **Speed**: 1-5 seconds per test
- **Scope**: Component interaction
- **Dependencies**: Temporary database, mocked APIs
- **Location**: `tests/integration/`

### E2E Tests
- **Speed**: 10-30 seconds per test
- **Scope**: Full system workflows
- **Dependencies**: Running web server, real browser
- **Location**: `tests/e2e/`

---

## Common Workflows

### Pre-Commit Validation (Fast)

```bash
# Quick check before committing
./quick_test.sh
```

**Time**: ~5 seconds
**Coverage**: Unit tests only

### Full Validation (Before Push)

```bash
# Comprehensive check before pushing
./run_tests.sh --coverage
```

**Time**: ~30 seconds
**Coverage**: Unit + Integration tests

### Development Cycle

```bash
# While developing new features
./run_tests.sh --fast

# When ready to commit
./run_tests.sh --unit --integration

# Before creating PR
./run_tests.sh --coverage
```

### Debugging Failed Tests

```bash
# Run with verbose output
./run_tests.sh --unit --verbose

# Run specific test file
pytest tests/unit/test_web_dashboard.py::TestDashboardRoutes::test_index_page_loads -vv

# Run with detailed traceback
./run_tests.sh --verbose
```

---

## Understanding Test Results

### Success ✓

```
════════════════════════════════════════════════════════════════════
  ✓ ALL TESTS PASSED
════════════════════════════════════════════════════════════════════

Results:
  Total Tests:  35
  Passed:       35
  Failed:       0
```

**Action**: Commit your changes with confidence!

### Failure ✗

```
test_api_data_structure FAILED

AssertionError: assert 'signals' in data
E   Expected 'signals' key in API response
```

**Action**:
1. Review the failed test output
2. Check the assertion that failed
3. Fix the code or test as needed
4. Re-run tests

### Coverage Report

```
Overall Coverage: 78%

web_dashboard.py    245     45    82%    45-67, 123-145
```

**Interpretation**:
- **82% covered** - Good coverage
- **Lines 45-67, 123-145** - Not covered by tests
- **Action**: Consider adding tests for uncovered lines

---

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request

### Manual Trigger in CI

```yaml
# In .github/workflows/tests.yml
- name: Run tests
  run: |
    chmod +x run_tests.sh
    ./run_tests.sh --coverage
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
./quick_test.sh
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Troubleshooting

### Issue: "pytest not found"

**Solution:**
```bash
pip install pytest pytest-cov pytest-flask pytest-mock
```

### Issue: "Permission denied"

**Solution:**
```bash
chmod +x run_tests.sh quick_test.sh
```

### Issue: "Module not found"

**Solution:**
```bash
# Make sure you're in project root
cd /root/7monthIndicator

# Install dependencies
pip install -r requirements.txt
```

### Issue: Tests fail with database errors

**Solution:**
- Tests use temporary databases automatically
- No manual setup needed
- Check that `conftest.py` is present

### Issue: E2E tests skipped

**Reason**: Web dashboard not running

**Solution:**
```bash
# Start dashboard in background
python web_dashboard.py &

# Run E2E tests
./run_tests.sh --e2e

# Stop dashboard when done
pkill -f web_dashboard.py
```

### Issue: Slow tests

**Solution:**
```bash
# Run only fast unit tests
./run_tests.sh --fast

# Or use quick test script
./quick_test.sh
```

---

## Advanced Usage

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/ -n auto
```

### Watch Mode (Auto-rerun on changes)

```bash
# Install pytest-watch
pip install pytest-watch

# Auto-run tests on file changes
pytest-watch tests/unit/ -v
```

### Generate Different Report Formats

```bash
# HTML report
./run_tests.sh --coverage
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=. --cov-report=term

# XML report (for CI)
pytest tests/ --junitxml=junit.xml
```

### Debug Mode

```bash
# Drop into debugger on failure
pytest tests/unit/test_web_dashboard.py --pdb

# Show print statements
pytest tests/unit/test_web_dashboard.py -s

# Very verbose output
pytest tests/unit/test_web_dashboard.py -vv
```

---

## Performance Benchmarks

### Expected Test Times

| Test Suite | Tests | Duration | Use Case |
|-----------|-------|----------|----------|
| `quick_test.sh` | ~20 | ~5s | Pre-commit check |
| `--unit` | ~20 | ~10s | Fast validation |
| `--integration` | ~15 | ~20s | Component testing |
| `--unit --integration` | ~35 | ~30s | Full backend |
| `--coverage` | ~35 | ~35s | Coverage analysis |
| All (with E2E) | ~50 | ~60s | Complete suite |

---

## Best Practices

### ✅ Do

- Run `quick_test.sh` before every commit
- Run full suite (`./run_tests.sh`) before pushing
- Check coverage reports regularly
- Add tests for new features
- Fix failing tests immediately

### ❌ Don't

- Skip tests when in a hurry (they catch bugs!)
- Ignore failing tests
- Commit code that breaks tests
- Remove tests to make them "pass"
- Run E2E tests without starting the server

---

## Getting Help

### Documentation

- **Quick Start**: `QUICK_START_TESTING.md`
- **Comprehensive Guide**: `WEB_DASHBOARD_TESTING_GUIDE.md`
- **Test Suite Docs**: `tests/README.md`

### Command Help

```bash
# Show help for main script
./run_tests.sh --help

# Show pytest help
pytest --help

# Show available pytest markers
pytest --markers
```

### Support

- Check documentation in `WEB_DASHBOARD_TESTING_GUIDE.md`
- Review test examples in `tests/` directory
- See `conftest.py` for available fixtures

---

## Summary

### Quick Reference

```bash
# Fast check (5s)
./quick_test.sh

# Full check (30s)
./run_tests.sh

# With coverage (35s)
./run_tests.sh --coverage

# Specific category
./run_tests.sh --unit
./run_tests.sh --integration

# Verbose output
./run_tests.sh --verbose

# Help
./run_tests.sh --help
```

---

**Happy Testing! 🚀**

*For detailed testing guide, see `WEB_DASHBOARD_TESTING_GUIDE.md`*
