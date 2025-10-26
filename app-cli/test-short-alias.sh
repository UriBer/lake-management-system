#!/bin/bash
# Test script for Lake Management System CLI - Short Alias 'lc'

echo "🎉 Lake Management System CLI - Short Alias Test"
echo "================================================"

echo "🔍 Testing all CLI access methods..."

# Test short alias (recommended)
echo "1. Testing short alias 'lc':"
./lc --version && echo "✅ lc works" || echo "❌ lc failed"

# Test full name
echo "2. Testing full name 'lake-cli':"
./lake-cli --version && echo "✅ lake-cli works" || echo "❌ lake-cli failed"

# Test direct Python script
echo "3. Testing direct Python script 'lake_cli.py':"
./lake_cli.py --version && echo "✅ lake_cli.py works" || echo "❌ lake_cli.py failed"

echo ""
echo "🔍 Testing command functionality with short alias..."

# Test table-list command
echo "Testing table-list command:"
./lc table-list --dataset governance_metadata > /dev/null && echo "✅ table-list works" || echo "❌ table-list failed"

echo ""
echo "🎯 All tests completed!"
echo ""
echo "🚀 You can now use the CLI with the short alias:"
echo "  ./lc --help"
echo "  ./lc table-list --dataset my_dataset"
echo "  ./lc schema-compare table1 table2"
echo "  ./lc table-compare table1 table2"
echo "  ./lc update-metadata --log"
echo ""
echo "📚 For more information, see README.md"
