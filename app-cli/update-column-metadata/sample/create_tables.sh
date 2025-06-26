#!/bin/bash

# Exit on error
set -e

# Load environment variables from .env file
if [ -f "../.env" ]; then
    source ../.env
else
    echo "Error: .env file not found in parent directory"
    exit 1
fi

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID not set in .env file"
    exit 1
fi

# Check if bq command is available
if ! command -v bq &> /dev/null; then
    echo "Error: bq command not found. Please install Google Cloud SDK"
    exit 1
fi

# Check if user is authenticated
if ! bq ls &> /dev/null; then
    echo "Error: Not authenticated with Google Cloud. Please run 'gcloud auth login'"
    exit 1
fi

# Replace PROJECT_ID in SQL file and execute
echo "Creating tables in project: $PROJECT_ID"
sed "s/@PROJECT_ID/$PROJECT_ID/g" create_tables.sql | bq query --use_legacy_sql=false || {
    echo "Error: Failed to create tables"
    exit 1
}

# Load sample metadata
echo "Loading sample metadata..."
bq load --source_format=CSV \
    --skip_leading_rows=1 \
    $PROJECT_ID.governance_metadata.system_metadata \
    sample_metadata.csv \
    target_dataset_name:STRING,table_name:STRING,column_name:STRING,column_metadata:STRING || {
    echo "Error: Failed to load sample metadata"
    exit 1
}

echo "✅ Done! All tables created and sample metadata loaded successfully." 