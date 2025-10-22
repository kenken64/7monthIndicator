#!/bin/bash
################################################################################
# Install Test Dependencies
#
# This script installs all dependencies required for running tests.
# Run this once before running any tests.
#
# Usage: ./install_test_deps.sh
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

echo -e "${BOLD}${CYAN}"
echo "════════════════════════════════════════════════════════════════════"
echo "  Installing Test Dependencies"
echo "════════════════════════════════════════════════════════════════════"
echo -e "${NC}\n"

# Check Python
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo -e "${YELLOW}Please install Python 3.8 or higher${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}\n"

# Check pip
echo -e "${BLUE}Checking pip installation...${NC}"
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo -e "${RED}✗ pip is not installed${NC}"
    echo -e "${YELLOW}Please install pip${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip found${NC}\n"

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
python3 -m pip install --upgrade pip -q
echo -e "${GREEN}✓ pip upgraded${NC}\n"

# Core testing packages
echo -e "${BLUE}Installing core testing packages...${NC}"
CORE_PACKAGES=(
    "pytest>=8.0.0"
    "pytest-cov>=4.1.0"
    "pytest-mock>=3.12.0"
    "pytest-timeout>=2.2.0"
    "pytest-flask>=1.3.0"
)

for pkg in "${CORE_PACKAGES[@]}"; do
    echo -e "  Installing ${pkg}..."
    pip install "${pkg}" -q
done
echo -e "${GREEN}✓ Core testing packages installed${NC}\n"

# Optional E2E testing packages
echo -e "${BLUE}Installing optional E2E testing packages...${NC}"
E2E_PACKAGES=(
    "playwright>=1.40.0"
    "pytest-playwright>=0.4.4"
)

for pkg in "${E2E_PACKAGES[@]}"; do
    echo -e "  Installing ${pkg}..."
    pip install "${pkg}" -q 2>/dev/null || {
        echo -e "${YELLOW}  ⚠ Failed to install ${pkg} (optional)${NC}"
    }
done

# Install Playwright browsers if playwright was installed
if python3 -c "import playwright" &> /dev/null; then
    echo -e "\n${BLUE}Installing Playwright browsers...${NC}"
    python3 -m playwright install chromium --with-deps &> /dev/null || {
        echo -e "${YELLOW}  ⚠ Failed to install Playwright browsers (optional)${NC}"
    }
    echo -e "${GREEN}✓ Playwright browsers installed${NC}"
fi
echo ""

# Verify installations
echo -e "${BLUE}Verifying installations...${NC}"

# Check pytest
if python3 -m pytest --version &> /dev/null; then
    PYTEST_VERSION=$(python3 -m pytest --version | head -n1)
    echo -e "${GREEN}✓ pytest: ${PYTEST_VERSION}${NC}"
else
    echo -e "${RED}✗ pytest installation failed${NC}"
    exit 1
fi

# Check pytest-cov
if python3 -c "import pytest_cov" &> /dev/null; then
    echo -e "${GREEN}✓ pytest-cov installed${NC}"
else
    echo -e "${YELLOW}⚠ pytest-cov not installed${NC}"
fi

# Check pytest-flask
if python3 -c "import pytest_flask" &> /dev/null; then
    echo -e "${GREEN}✓ pytest-flask installed${NC}"
else
    echo -e "${YELLOW}⚠ pytest-flask not installed${NC}"
fi

# Check pytest-mock
if python3 -c "import pytest_mock" &> /dev/null; then
    echo -e "${GREEN}✓ pytest-mock installed${NC}"
else
    echo -e "${YELLOW}⚠ pytest-mock not installed${NC}"
fi

# Check playwright (optional)
if python3 -c "import playwright" &> /dev/null; then
    echo -e "${GREEN}✓ playwright installed (optional)${NC}"
else
    echo -e "${CYAN}ℹ playwright not installed (optional, for E2E tests)${NC}"
fi

echo ""
echo -e "${BOLD}${GREEN}"
echo "════════════════════════════════════════════════════════════════════"
echo "  ✓ Installation Complete!"
echo "════════════════════════════════════════════════════════════════════"
echo -e "${NC}\n"

echo -e "${CYAN}Next steps:${NC}"
echo -e "  1. Run quick test:     ${BOLD}./quick_test.sh${NC}"
echo -e "  2. Run all tests:      ${BOLD}./run_tests.sh${NC}"
echo -e "  3. Run with coverage:  ${BOLD}./run_tests.sh --coverage${NC}"
echo -e "  4. View help:          ${BOLD}./run_tests.sh --help${NC}"
echo ""

echo -e "${GREEN}Happy testing! 🧪${NC}"
