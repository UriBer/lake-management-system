#!/bin/bash
# Test script for BigQuery Table List Extractor

echo "🧪 Testing BigQuery Table List Extractor"
echo "========================================"

# Check if Python script exists
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found"
    exit 1
fi

# Check if requirements are installed
echo "📦 Checking dependencies..."
python -c "import google.cloud.bigquery, dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing dependencies..."
    pip install -r requirements.txt
fi

# Test with help
echo "📋 Testing help output..."
python main.py --help

echo ""
echo "✅ Test completed!"
echo ""
echo "To use the tool:"
echo "  python main.py --dataset your_dataset_name"
echo "  python main.py --dataset your_dataset_name --project your-project-id"
echo "  python main.py --dataset your_dataset_name --include-views --verbose"
