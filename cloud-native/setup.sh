#!/bin/bash
# Setup script for cloud-native deployment
# Copies CLI modules from app-cli to cloud-native

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_CLI_DIR="$PROJECT_ROOT/app-cli"
CLOUD_NATIVE_DIR="$SCRIPT_DIR"

echo "📦 Setting up cloud-native deployment..."

# Check if app-cli directory exists
if [ ! -d "$APP_CLI_DIR" ]; then
    echo "❌ Error: app-cli directory not found at $APP_CLI_DIR"
    exit 1
fi

# Check if modules directory exists in app-cli
if [ ! -d "$APP_CLI_DIR/modules" ]; then
    echo "❌ Error: app-cli/modules directory not found"
    exit 1
fi

# Create modules directory in cloud-native
echo "📁 Creating modules directory..."
mkdir -p "$CLOUD_NATIVE_DIR/modules"

# Copy modules
echo "📋 Copying CLI modules..."
cp -r "$APP_CLI_DIR/modules/"* "$CLOUD_NATIVE_DIR/modules/"

# Ensure __init__.py exists
if [ ! -f "$CLOUD_NATIVE_DIR/modules/__init__.py" ]; then
    touch "$CLOUD_NATIVE_DIR/modules/__init__.py"
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Build Docker image:"
echo "     gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/lake-management-api"
echo ""
echo "  2. Configure Terraform:"
echo "     cp terraform.tfvars.example terraform.tfvars"
echo "     # Edit terraform.tfvars with your configuration"
echo ""
echo "  3. Deploy:"
echo "     terraform init"
echo "     terraform apply"

