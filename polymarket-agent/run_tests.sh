#!/bin/bash
# Run all tests with proper PYTHONPATH

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "🧪 Running Polymarket Agent Tests"
echo "=================================="
echo ""

# Test 1: Quick tests
echo "📋 Running quick tests..."
python3 test_quick.py
if [ $? -ne 0 ]; then
    echo "❌ Quick tests failed"
    exit 1
fi

echo ""
echo "=================================="
echo ""

# Test 2: Strategy tests
echo "📋 Running strategy tests..."
python3 tests/test_strategy.py
if [ $? -ne 0 ]; then
    echo "❌ Strategy tests failed"
    exit 1
fi

echo ""
echo "=================================="
echo ""

# Test 3: Position tests
echo "📋 Running position tests..."
python3 tests/test_position.py
if [ $? -ne 0 ]; then
    echo "❌ Position tests failed"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ ALL TESTS PASSED!"
echo "=================================="
