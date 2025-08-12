# Lake Management System - Column Description Updater

This application connects to Google BigQuery to update column descriptions based on metadata stored in a separate BigQuery table. It reads configuration parameters from a `.env` file to ensure sensitive information and configuration are easily managed.

## Prerequisites

Before you begin, ensure you have:

1. Python 3.6+ installed
2. Google Cloud CLI (gcloud) installed and configured:
   ```bash
   # Install gcloud (if not already installed)
   # On macOS:
   brew install google-cloud-sdk
   # On Linux:
   sudo apt-get install google-cloud-sdk
   # On Windows:
   # Download from https://cloud.google.com/sdk/docs/install

   # Initialize gcloud
   gcloud init

   # Set up application default credentials
   gcloud auth application-default login
   ```
3. BigQuery API enabled in your Google Cloud project
4. Sufficient permissions to:
   - Create datasets and tables
   - Update column descriptions
   - Run BigQuery queries

## Features

- Updates BigQuery column descriptions from a metadata table
- Handles rate limiting with configurable delays
- Supports local logging for debugging
- Graceful error handling and keyboard interrupts
- Detailed job run logging in BigQuery
- Case-insensitive column name matching

## Setup Instructions

### 1. Set Up Virtual Environment

It's recommended to use a virtual environment to isolate the project dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Your prompt should now show (venv) at the beginning
```

To deactivate the virtual environment when you're done:
```bash
deactivate
```

### 2. Create and Configure `.env` File

Create a file named `.env` in the `app-cli/update-column-metadata` directory with the following content:

```
PROJECT_ID=your-project-id
METADATA_TABLE=governance_metadata.system_metadata
JOB_RUN_TABLE=governance_metadata.job_runs
SLEEP_MSECONDS=500
MAX_PARALLEL_WORKERS=10
```

- `PROJECT_ID`: Your Google Cloud Project ID where your BigQuery datasets are located
- `METADATA_TABLE`: The full path to your metadata table (e.g., `governance_metadata.system_metadata`)
- `JOB_RUN_TABLE`: The full path to the table where job run logs will be stored
- `SLEEP_MSECONDS`: Optional delay in milliseconds between DDL statements (default: 1000ms)

### 3. Create BigQuery Tables

The `app-cli/update-column-metadata/sample` directory contains scripts to set up the required tables:

1. Make sure your `.env` file is properly configured
2. Navigate to the sample directory:
```bash
cd app-cli/update-column-metadata/sample
```
3. Make the setup script executable:
```bash
chmod +x create_tables.sh
```
4. Run the setup script:
```bash
./create_tables.sh
```

This script will:
- Create all necessary datasets and tables
- Load the sample metadata from `sample_metadata.csv`
- Use your project ID from the `.env` file

The sample setup creates:
- Governance metadata tables for storing column descriptions
- Sample data tables in three layers (raw, staging, warehouse)
- Example metadata entries in the system_metadata table

### 4. Install Dependencies

With your virtual environment activated, navigate to the `app-cli/` directory and install the required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Run the Application

Basic usage:
```bash
python main.py
```

With local logging enabled:
```bash
python main.py --log
```

The `--log` option creates a local log file with timestamps for detailed debugging.

## Metadata Table Structure

The metadata table should have the following columns:
- `target_dataset_name`: The dataset name (without project ID)
- `table_name`: The table name
- `column_name`: The column name
- `column_metadata`: The description to set

A sample metadata file (`app-cli/update-column-metadata/sample/sample_metadata.csv`) is provided with generic example data. Example row:
```csv
target_dataset_name,table_name,column_name,column_metadata
raw_data,customers,customer_id,"Unique identifier for each customer"
```

## Output

The application provides real-time feedback about:
- Successfully updated columns
- Skipped columns (no change needed)
- Unmatched columns (not found in target tables)
- Errors encountered

A summary is displayed at the end of the run, and all actions are logged to the specified BigQuery job run table.

## Error Handling

- Graceful handling of keyboard interrupts (Ctrl+C)
- Detailed error messages for common issues
- Automatic retry with backoff for rate limits
- Comprehensive logging of all operations

## Requirements

- Python 3.6+
- Google Cloud credentials configured
- BigQuery API enabled
- Required Python packages (see requirements.txt)

## Development

When working on the project:

1. Always activate the virtual environment first:
```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

2. Install new dependencies with:
```bash
pip install package_name
pip freeze > requirements.txt  # Update requirements.txt
```

3. Deactivate when done:
```bash
deactivate
```
4. Run using

python ./app-cli/update-column-metadata/main.py -log