#!/bin/bash
################################################################################
# Automated Test Runner for 7monthIndicator Trading Bot
#
# This script runs all test suites with proper reporting and error handling.
#
# Usage:
#   ./run_tests.sh                    # Run all tests
#   ./run_tests.sh --unit             # Run only unit tests
#   ./run_tests.sh --integration      # Run only integration tests
#   ./run_tests.sh --e2e              # Run only E2E tests
#   ./run_tests.sh --coverage         # Run all tests with coverage report
#   ./run_tests.sh --fast             # Run only fast unit tests
#   ./run_tests.sh --verbose          # Run with verbose output
#   ./run_tests.sh --help             # Show this help message
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default options
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_E2E=false
RUN_ALL=true
WITH_COVERAGE=false
VERBOSE=""
FAST_MODE=false

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BOLD}${CYAN}"
    echo "════════════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BOLD}${BLUE}▶ $1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

show_help() {
    cat << EOF
${BOLD}Automated Test Runner for 7monthIndicator Trading Bot${NC}

${BOLD}USAGE:${NC}
    ./run_tests.sh [OPTIONS]

${BOLD}OPTIONS:${NC}
    --unit              Run only unit tests (fast, isolated)
    --integration       Run only integration tests (component interaction)
    --e2e               Run only end-to-end tests (full system)
    --coverage          Run all tests with coverage report
    --fast              Run only fast unit tests
    --verbose, -v       Run with verbose output
    --help, -h          Show this help message

${BOLD}EXAMPLES:${NC}
    ./run_tests.sh                    # Run all tests
    ./run_tests.sh --unit             # Run only unit tests
    ./run_tests.sh --coverage         # Run all tests with coverage
    ./run_tests.sh --unit --verbose   # Run unit tests with verbose output
    ./run_tests.sh --fast             # Quick validation with unit tests only

${BOLD}TEST CATEGORIES:${NC}
    Unit Tests         - Fast, isolated tests (< 1s per test)
    Integration Tests  - Component interaction tests (1-5s per test)
    E2E Tests          - Full system tests (10-30s per test)

${BOLD}OUTPUT:${NC}
    - Test results are displayed in the console
    - Coverage reports (if enabled) are saved to htmlcov/
    - JUnit XML reports are saved to test-results/

EOF
}

install_dependencies() {
    print_section "Installing/Checking Dependencies"

    local missing_deps=()

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        print_error "Please install Python 3.8+ to continue"
        exit 1
    fi
    print_success "Python 3 is installed: $(python3 --version)"

    # Check pip
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        print_error "pip is not installed"
        print_error "Please install pip to continue"
        exit 1
    fi
    print_success "pip is installed"

    # Core dependencies
    local core_deps=("pytest" "pytest_mock" "pytest_timeout")

    # Coverage dependencies
    if [ "$WITH_COVERAGE" = true ]; then
        core_deps+=("pytest_cov" "coverage")
    fi

    # Flask dependencies
    core_deps+=("flask")

    # Check for pytest-flask (try to import)
    if ! python3 -c "import pytest_flask" &> /dev/null 2>&1; then
        core_deps+=("pytest_flask")
    fi

    # Check each dependency
    print_info "Checking required Python packages..."
    for dep in "${core_deps[@]}"; do
        if ! python3 -c "import $dep" &> /dev/null 2>&1; then
            missing_deps+=("$dep")
        fi
    done

    # Install missing dependencies
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_warning "Missing dependencies detected: ${missing_deps[*]}"
        print_info "Installing missing dependencies..."

        # Convert underscore to hyphen for pip package names
        local pip_packages=()
        for dep in "${missing_deps[@]}"; do
            pip_packages+=("${dep//_/-}")
        done

        pip install -q "${pip_packages[@]}"

        if [ $? -eq 0 ]; then
            print_success "All dependencies installed successfully"
        else
            print_error "Failed to install some dependencies"
            print_info "Please run manually: pip install ${pip_packages[*]}"
            exit 1
        fi
    else
        print_success "All required dependencies are already installed"
    fi

    # Verify pytest installation
    if python3 -m pytest --version &> /dev/null; then
        print_success "pytest is working: $(python3 -m pytest --version | head -n1)"
    else
        print_error "pytest installation verification failed"
        exit 1
    fi
}

create_directories() {
    # Create test results directory
    mkdir -p test-results
    mkdir -p htmlcov
}

run_unit_tests() {
    print_section "Running Unit Tests"

    local coverage_args=""
    if [ "$WITH_COVERAGE" = true ]; then
        coverage_args="--cov=. --cov-append --cov-report=term-missing"
    fi

    if [ -d "tests/unit" ]; then
        pytest tests/unit/ \
            -v $VERBOSE \
            $coverage_args \
            --junitxml=test-results/unit-tests.xml \
            --tb=short \
            -m "unit" \
            || return 1

        print_success "Unit tests completed"
    else
        print_warning "Unit tests directory not found: tests/unit/"
    fi
}

run_integration_tests() {
    print_section "Running Integration Tests"

    local coverage_args=""
    if [ "$WITH_COVERAGE" = true ]; then
        coverage_args="--cov=. --cov-append --cov-report=term-missing"
    fi

    if [ -d "tests/integration" ]; then
        pytest tests/integration/ \
            -v $VERBOSE \
            $coverage_args \
            --junitxml=test-results/integration-tests.xml \
            --tb=short \
            -m "integration" \
            || return 1

        print_success "Integration tests completed"
    else
        print_warning "Integration tests directory not found: tests/integration/"
    fi
}

run_e2e_tests() {
    print_section "Running End-to-End Tests"

    # Check if web dashboard is running
    print_info "Checking if web dashboard is running..."
    if ! curl -s http://localhost:5001 > /dev/null 2>&1; then
        print_warning "Web dashboard is not running on port 5001"
        print_info "E2E tests require the dashboard to be running"
        print_info "Start it with: python web_dashboard.py &"
        print_info "Skipping E2E tests..."
        return 0
    fi

    # Check if playwright is installed
    if ! python3 -c "import playwright" &> /dev/null; then
        print_warning "Playwright is not installed. E2E tests will be skipped."
        print_info "Install with: pip install playwright pytest-playwright && python -m playwright install chromium"
        return 0
    fi

    local coverage_args=""
    if [ "$WITH_COVERAGE" = true ]; then
        coverage_args="--cov=. --cov-append --cov-report=term-missing"
    fi

    if [ -d "tests/e2e" ]; then
        pytest tests/e2e/ \
            -v $VERBOSE \
            $coverage_args \
            --junitxml=test-results/e2e-tests.xml \
            --tb=short \
            -m "e2e" \
            || return 1

        print_success "E2E tests completed"
    else
        print_warning "E2E tests directory not found: tests/e2e/"
    fi
}

generate_coverage_report() {
    if [ "$WITH_COVERAGE" = true ]; then
        print_section "Generating Coverage Report"

        # Generate HTML coverage report
        python3 -m pytest --cov=. --cov-report=html --cov-report=term-missing --collect-only > /dev/null 2>&1 || true

        if [ -f "htmlcov/index.html" ]; then
            print_success "HTML coverage report generated: htmlcov/index.html"

            # Calculate coverage percentage
            coverage_percent=$(python3 -m coverage report | tail -n 1 | awk '{print $NF}')
            echo ""
            print_info "Overall Coverage: ${BOLD}${coverage_percent}${NC}"
            echo ""
        fi
    fi
}

show_summary() {
    print_section "Test Summary"

    local total_tests=0
    local passed_tests=0
    local failed_tests=0

    # Parse JUnit XML files if they exist
    if command -v xmllint &> /dev/null; then
        for xml_file in test-results/*.xml; do
            if [ -f "$xml_file" ]; then
                tests=$(xmllint --xpath "string(//testsuite/@tests)" "$xml_file" 2>/dev/null || echo "0")
                failures=$(xmllint --xpath "string(//testsuite/@failures)" "$xml_file" 2>/dev/null || echo "0")
                errors=$(xmllint --xpath "string(//testsuite/@errors)" "$xml_file" 2>/dev/null || echo "0")

                total_tests=$((total_tests + tests))
                failed_tests=$((failed_tests + failures + errors))
            fi
        done
        passed_tests=$((total_tests - failed_tests))
    fi

    echo -e "${BOLD}Results:${NC}"
    echo -e "  Total Tests:  ${total_tests}"
    echo -e "  ${GREEN}Passed:       ${passed_tests}${NC}"
    if [ $failed_tests -gt 0 ]; then
        echo -e "  ${RED}Failed:       ${failed_tests}${NC}"
    else
        echo -e "  ${GREEN}Failed:       ${failed_tests}${NC}"
    fi
    echo ""

    if [ -d "test-results" ]; then
        print_info "Test results saved to: test-results/"
    fi

    if [ "$WITH_COVERAGE" = true ] && [ -f "htmlcov/index.html" ]; then
        print_info "Coverage report: htmlcov/index.html"
    fi
}

################################################################################
# Parse arguments
################################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        --e2e)
            RUN_E2E=true
            RUN_ALL=false
            shift
            ;;
        --coverage)
            WITH_COVERAGE=true
            shift
            ;;
        --fast)
            RUN_UNIT=true
            RUN_ALL=false
            FAST_MODE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE="-vv"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
done

################################################################################
# Main execution
################################################################################

print_header "7monthIndicator Trading Bot - Test Suite"

# Install/Check dependencies
install_dependencies

# Create necessary directories
create_directories

# Track overall success
OVERALL_SUCCESS=true

# Run tests based on options
if [ "$RUN_ALL" = true ]; then
    # Run all test categories
    run_unit_tests || OVERALL_SUCCESS=false
    run_integration_tests || OVERALL_SUCCESS=false

    if [ "$FAST_MODE" = false ]; then
        run_e2e_tests || OVERALL_SUCCESS=false
    fi
else
    # Run selected test categories
    if [ "$RUN_UNIT" = true ]; then
        run_unit_tests || OVERALL_SUCCESS=false
    fi

    if [ "$RUN_INTEGRATION" = true ]; then
        run_integration_tests || OVERALL_SUCCESS=false
    fi

    if [ "$RUN_E2E" = true ]; then
        run_e2e_tests || OVERALL_SUCCESS=false
    fi
fi

# Generate coverage report if requested
if [ "$WITH_COVERAGE" = true ]; then
    generate_coverage_report
fi

# Show summary
show_summary

# Final status
echo ""
if [ "$OVERALL_SUCCESS" = true ]; then
    print_header "${GREEN}✓ ALL TESTS PASSED${NC}"
    exit 0
else
    print_header "${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
