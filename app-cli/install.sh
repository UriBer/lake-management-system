#!/bin/bash
# Installation script for Lake Management System CLI

echo "🚀 Installing Lake Management System CLI"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "lake_cli.py" ]; then
    echo "❌ lake_cli.py not found. Please run from app-cli directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt --break-system-packages

# Make scripts executable
chmod +x lake_cli.py
chmod +x lake-cli
chmod +x lc

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎉 You can now use the CLI with:"
echo "  ./lc --help                    # Short alias (recommended)"
echo "  ./lake-cli --help              # Full name"
echo "  ./lake_cli.py --help           # Direct Python script"
echo ""
echo "📋 Example commands:"
echo "  ./lc table-list --dataset my_dataset"
echo "  ./lc schema-compare table1 table2"
echo "  ./lc table-compare table1 table2"
echo "  ./lc update-metadata --log"
echo ""
echo "🔧 To make it available system-wide, add to your PATH:"
echo "  export PATH=\"\$(pwd):\$PATH\""
echo "  # Add this line to your ~/.bashrc or ~/.zshrc for permanent access"
echo ""
echo "📝 Don't forget to:"
echo "  1. Set up your .env file: cp .env.example .env"
echo "  2. Configure your BigQuery project ID"
echo "  3. Authenticate: gcloud auth application-default login"
echo ""
echo "📚 For more information, see README.md"
