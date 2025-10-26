#!/bin/bash
# Final test script for Lake Management System CLI

echo "🎉 Lake Management System CLI - Final Test"
echo "=========================================="

# Test all commands
echo "🔍 Testing help commands..."
./lake-cli --help > /dev/null && echo "✅ Main help works" || echo "❌ Main help failed"
./lake-cli table-list --help > /dev/null && echo "✅ Table-list help works" || echo "❌ Table-list help failed"
./lake-cli schema-compare --help > /dev/null && echo "✅ Schema-compare help works" || echo "❌ Schema-compare help failed"
./lake-cli table-compare --help > /dev/null && echo "✅ Table-compare help works" || echo "❌ Table-compare help failed"
./lake-cli update-metadata --help > /dev/null && echo "✅ Update-metadata help works" || echo "❌ Update-metadata help failed"

echo ""
echo "🔍 Testing actual functionality..."
echo "Testing table-list command..."
./lake-cli table-list --dataset governance_metadata > /dev/null && echo "✅ Table-list command works" || echo "❌ Table-list command failed"

echo ""
echo "🎯 All tests completed!"
echo ""
echo "🚀 The CLI is ready to use with commands like:"
echo "  ./lake-cli table-list --dataset my_dataset"
echo "  ./lake-cli schema-compare table1 table2"
echo "  ./lake-cli table-compare table1 table2"
echo "  ./lake-cli update-metadata --log"
echo ""
echo "📚 For more information, see README.md"
