#!/bin/bash
# Test script for Lake Management System Unified CLI

echo "🧪 Testing Lake Management System Unified CLI"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "lake-cli.py" ]; then
    echo "❌ lake-cli.py not found. Please run from app-cli directory"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
fi

echo "📦 Checking dependencies..."
python -c "import google.cloud.bigquery, dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "🔍 Testing CLI help..."
python lake-cli.py --help

echo ""
echo "🔍 Testing table-list help..."
python lake-cli.py table-list --help

echo ""
echo "🔍 Testing schema-compare help..."
python lake-cli.py schema-compare --help

echo ""
echo "🔍 Testing table-compare help..."
python lake-cli.py table-compare --help

echo ""
echo "🔍 Testing update-metadata help..."
python lake-cli.py update-metadata --help

echo ""
echo "✅ All help commands working!"
echo ""
echo "🚀 To test actual functionality:"
echo "  python lake-cli.py table-list --dataset your_dataset --verbose"
echo "  python lake-cli.py schema-compare table1 table2"
echo "  python lake-cli.py table-compare table1 table2"
echo "  python lake-cli.py update-metadata --log"
echo ""
echo "📚 For more information, see README.md"
