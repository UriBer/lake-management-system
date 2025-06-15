# Lake Management System - Column Description Updater

This application connects to Google BigQuery to update column descriptions based on metadata stored in a separate BigQuery table. It reads configuration parameters from a `.env` file to ensure sensitive information and configuration are easily managed.

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

Create a file named `.env` in the `app-cli/` directory with the following content:

```
PROJECT_ID=your-project-id
METADATA_TABLE=governance_metadata.system_metadata
JOB_RUN_TABLE=governance_metadata.job_runs
SLEEP_MSECONDS=1000
```

- `PROJECT_ID`: Your Google Cloud Project ID where your BigQuery datasets are located
- `METADATA_TABLE`: The full path to your metadata table (e.g., `governance_metadata.system_metadata`)
- `JOB_RUN_TABLE`: The full path to the table where job run logs will be stored
- `SLEEP_MSECONDS`: Optional delay in milliseconds between DDL statements (default: 1000ms)

### 3. Create BigQuery Tables

First, create the necessary datasets and tables in BigQuery:

```sql
-- Create the governance metadata dataset
CREATE DATASET IF NOT EXISTS `your-project-id.governance_metadata`;

-- Create the metadata table
CREATE TABLE IF NOT EXISTS `your-project-id.governance_metadata.system_metadata` (
    target_dataset_name STRING,
    table_name STRING,
    column_name STRING,
    column_metadata STRING
);

-- Create the job runs table
CREATE TABLE IF NOT EXISTS `your-project-id.governance_metadata.job_runs` (
    job_run_id STRING,
    timestamp TIMESTAMP,
    status STRING,
    table_name STRING,
    column_name STRING,
    column_metadata STRING,
    target_dataset STRING
);

-- Create sample tables to update
CREATE DATASET IF NOT EXISTS `your-project-id.raw_data`;
CREATE DATASET IF NOT EXISTS `your-project-id.staging`;
CREATE DATASET IF NOT EXISTS `your-project-id.warehouse`;

-- Create raw_data tables
CREATE TABLE IF NOT EXISTS `your-project-id.raw_data.customers` (
    customer_id STRING,
    first_name STRING,
    last_name STRING,
    email STRING,
    phone STRING
);

CREATE TABLE IF NOT EXISTS `your-project-id.raw_data.orders` (
    order_id STRING,
    customer_id STRING,
    order_date DATE,
    total_amount NUMERIC
);

-- Create staging tables
CREATE TABLE IF NOT EXISTS `your-project-id.staging.customers` (
    customer_id STRING,
    full_name STRING,
    email STRING,
    phone STRING
);

CREATE TABLE IF NOT EXISTS `your-project-id.staging.orders` (
    order_id STRING,
    customer_id STRING,
    order_date DATE,
    total_amount NUMERIC
);

-- Create warehouse tables
CREATE TABLE IF NOT EXISTS `your-project-id.warehouse.dim_customers` (
    customer_key INT64,
    customer_id STRING,
    full_name STRING,
    email STRING,
    phone STRING
);

CREATE TABLE IF NOT EXISTS `your-project-id.warehouse.fact_orders` (
    order_key INT64,
    customer_key INT64,
    order_date DATE,
    total_amount NUMERIC
);
```

### 4. Install Dependencies

With your virtual environment activated, navigate to the `app-cli/` directory and install the required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Load Sample Metadata

A sample CSV file (`app-cli/sample_metadata.csv`) is provided with generic example data. Load it into BigQuery:

```bash
bq load --source_format=CSV \
  --skip_leading_rows=1 \
  governance_metadata.system_metadata \
  app-cli/sample_metadata.csv \
  target_dataset_name:STRING,table_name:STRING,column_name:STRING,column_metadata:STRING
```

### 6. Run the Application

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

Example row from the sample file:
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
