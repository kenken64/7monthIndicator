#!/bin/bash
################################################################################
# Quick Test Runner - Fast validation of core functionality
#
# This script runs only unit tests for quick validation during development.
# Automatically installs missing dependencies.
#
# Usage: ./quick_test.sh
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${BOLD}${CYAN}🚀 Quick Test Runner${NC}\n"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for virtual environment
if [ -d "venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}\n"
elif [ -d "analyze_venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source analyze_venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}\n"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check pip
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip is not installed${NC}"
    exit 1
fi

# Install missing dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

missing_deps=()

# Check each required package
for pkg in pytest pytest_mock pytest_timeout flask; do
    if ! python3 -c "import $pkg" &> /dev/null 2>&1; then
        missing_deps+=("$pkg")
    fi
done

# Install if any are missing
if [ ${#missing_deps[@]} -gt 0 ]; then
    echo -e "${YELLOW}Installing missing dependencies: ${missing_deps[*]}${NC}"

    # Convert to pip package names (underscore to hyphen)
    pip_packages=()
    for pkg in "${missing_deps[@]}"; do
        pip_packages+=("${pkg//_/-}")
    done

    pip install "${pip_packages[@]}"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Dependencies installed${NC}\n"
    else
        echo -e "${RED}✗ Failed to install dependencies${NC}"
        echo -e "${YELLOW}Try manually: pip install ${pip_packages[*]}${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ All dependencies present${NC}\n"
fi

# Verify pytest works
if ! python3 -m pytest --version &> /dev/null; then
    echo -e "${RED}Error: pytest is not working properly${NC}"
    exit 1
fi

echo -e "${CYAN}Running unit tests...${NC}\n"

# Run unit tests only
if pytest tests/unit/test_web_dashboard.py -v --tb=short; then
    echo -e "\n${GREEN}${BOLD}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}${BOLD}✗ Some tests failed${NC}"
    echo -e "${YELLOW}Tip: Run './run_tests.sh --verbose' for detailed output${NC}"
    exit 1
fi
