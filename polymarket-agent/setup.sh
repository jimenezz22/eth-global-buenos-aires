#!/bin/bash
# Polymarket AI Hedge Agent - Safe Setup Script
# This script installs only verified dependencies needed for the project

set -e  # Exit on error

echo "🚀 Polymarket AI Hedge Agent - Setup"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $PYTHON_VERSION"

REQUIRED_VERSION="3.9"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo -e "${RED}✗ Python 3.9+ required${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python version OK${NC}"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi
echo ""

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies from requirements.txt
echo "📦 Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt -q

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All dependencies installed successfully${NC}"
else
    echo -e "${RED}✗ Some dependencies failed to install${NC}"
    echo "   Try running: source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
echo ""

# Verify key imports
echo "🧪 Verifying installation..."

python3 << EOF
import sys
success = True

# Test our custom modules
try:
    from my_agent import Position, TradingStrategy
    print("   ✓ my_agent modules")
except ImportError as e:
    print(f"   ✗ my_agent modules: {e}")
    success = False

# Test agents framework
try:
    from agents.polymarket.gamma import GammaMarketClient
    print("   ✓ agents.polymarket.gamma")
except ImportError as e:
    print(f"   ✗ agents.polymarket.gamma: {e}")
    success = False

try:
    from agents.polymarket.polymarket import Polymarket
    print("   ✓ agents.polymarket.polymarket")
except ImportError as e:
    print(f"   ✗ agents.polymarket.polymarket: {e}")
    success = False

# Test key libraries
try:
    import httpx
    print("   ✓ httpx")
except ImportError:
    print("   ✗ httpx")
    success = False

try:
    import web3
    print("   ✓ web3")
except ImportError:
    print("   ✗ web3")
    success = False

try:
    from py_clob_client.client import ClobClient
    print("   ✓ py_clob_client")
except ImportError:
    print("   ✗ py_clob_client")
    success = False

sys.exit(0 if success else 1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All imports verified successfully${NC}"
else
    echo -e "${RED}✗ Some imports failed${NC}"
    exit 1
fi
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    echo "   Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo ""
    echo -e "${YELLOW}📝 IMPORTANT: Edit .env file with your credentials:${NC}"
    echo "   - POLYGON_WALLET_PRIVATE_KEY"
    echo "   - MARKET_CONDITION_ID"
    echo "   - OPENAI_API_KEY (optional for AI features)"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi
echo ""

echo "======================================"
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Edit .env with your credentials"
echo "  3. Run agent: python main.py"
echo "  4. Or test: python -c 'from my_agent import *; print(\"Works!\")'"
echo ""
echo "For CLI access:"
echo "  python scripts/python/cli.py --help"
echo ""
