# BigQuery Table List Extractor

A Python CLI tool that extracts table information from a specific BigQuery dataset and exports it to CSV format. The tool provides comprehensive table metadata including schema, object type, primary key status, and row counts.

## Features

- **Table Information Extraction**: Extracts detailed metadata for all tables in a dataset
- **Primary Key Detection**: Identifies tables with primary key constraints
- **Row Count Statistics**: Includes row count information for each table
- **View Support**: Optional inclusion of views alongside tables
- **CSV Export**: Exports results to CSV format with customizable filenames
- **Flexible Configuration**: Supports both environment variables and command-line arguments

## Extracted Columns

The tool extracts the following information for each table:

| Column | Description |
|--------|-------------|
| `schema` | Table schema (dataset name) |
| `object_type` | Type of object (BASE TABLE or VIEW) |
| `name` | Table/view name |
| `primary_keys` | Whether the table has primary keys (Yes/No) |
| `row_count` | Number of rows in the table |

## Prerequisites

- Python 3.7+
- Google Cloud SDK installed and configured
- BigQuery API enabled
- Appropriate permissions to access the BigQuery dataset

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up authentication:
```bash
gcloud auth application-default login
```

3. Configure environment variables (optional):
```bash
cp .env.example .env
# Edit .env with your project settings
```

## Usage

### Basic Usage

```bash
python main.py --dataset <dataset_name>
```

### Command Line Options

| Option | Description | Required |
|--------|-------------|----------|
| `--dataset` | BigQuery dataset name to extract tables from | Yes |
| `--project` | BigQuery project ID (defaults to PROJECT_ID from .env) | No |
| `--output`, `-o` | Output CSV file path | No |
| `--include-views` | Include views in addition to tables | No |
| `--verbose`, `-v` | Enable verbose output | No |

### Examples

Extract tables from a dataset in the default project:
```bash
python main.py --dataset my_dataset
```

Extract tables from a specific project:
```bash
python main.py --dataset my_dataset --project my-project-id
```

Include views and specify output file:
```bash
python main.py --dataset my_dataset --include-views --output tables.csv
```

Enable verbose output:
```bash
python main.py --dataset my_dataset --verbose
```

## Output

### Console Output

The tool provides real-time feedback including:
- Connection status
- Extraction progress
- Summary statistics
- File export confirmation

Example output:
```
🚀 Extracting table information from my-project.my_dataset
📄 Output file: my_dataset_tables_20241226_143022.csv
ℹ️  Connected to BigQuery project: my-project
ℹ️  Executing query on dataset: my-project.my_dataset
ℹ️  Extracting table information...
ℹ️  Writing to CSV...
✅ Successfully exported 15 tables to my_dataset_tables_20241226_143022.csv

📊 Dataset Summary: my_dataset
  Tables: 12
  Views: 3
  With Primary Keys: 8
  Total Rows: 1,234,567

🏁 Extraction complete!
```

### CSV Output

The generated CSV file contains the following columns:

```csv
schema,object_type,name,primary_keys,row_count
my_dataset,BASE TABLE,users,Yes,50000
my_dataset,BASE TABLE,orders,No,125000
my_dataset,VIEW,user_summary,No,50000
```

## Configuration

### Environment Variables

Create a `.env` file in the project directory:

```bash
# Default BigQuery Project ID
PROJECT_ID=your-project-id

# Optional: Set default dataset
DEFAULT_DATASET=your-default-dataset
```

### Authentication

The tool uses Google Cloud Application Default Credentials. Ensure you're authenticated:

```bash
gcloud auth application-default login
```

## BigQuery Query

The tool uses the following BigQuery query to extract table information:

```sql
SELECT
  t.table_schema AS schema,
  t.table_type AS object_type,
  t.table_name AS name,
  CASE
    WHEN pk.table_name IS NOT NULL THEN 'Yes'
    ELSE 'No'
  END AS primary_keys,
  s.row_count
FROM `{project_id}.{dataset}.INFORMATION_SCHEMA.TABLES` t
LEFT JOIN (
  SELECT 
    table_name,
    COUNT(*) as pk_count
  FROM `{project_id}.{dataset}.INFORMATION_SCHEMA.KEY_COLUMN_USAGE`
  WHERE constraint_name = 'PRIMARY'
  GROUP BY table_name
) pk ON t.table_name = pk.table_name
LEFT JOIN (
  SELECT 
    table_name,
    row_count
  FROM `{project_id}.{dataset}.__TABLES__`
) s ON t.table_name = s.table_name
WHERE t.table_type IN ('BASE TABLE', 'VIEW')
ORDER BY t.table_name
```

## Error Handling

The tool handles various error scenarios:

- **Dataset Not Found**: Clear error message if the specified dataset doesn't exist
- **Permission Issues**: Authentication and authorization error handling
- **Network Issues**: Connection timeout and retry logic
- **Invalid Queries**: BigQuery syntax and permission error handling

## Limitations

- Requires appropriate BigQuery permissions to access INFORMATION_SCHEMA
- Row counts may not be available for external tables
- Large datasets may take longer to process
- Primary key detection relies on INFORMATION_SCHEMA.KEY_COLUMN_USAGE

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure you have `bigquery.tables.get` and `bigquery.tables.list` permissions
2. **Dataset Not Found**: Verify the dataset name and project ID are correct
3. **Authentication Issues**: Run `gcloud auth application-default login`

### Debug Mode

Use the `--verbose` flag to see detailed execution information:

```bash
python main.py --dataset my_dataset --verbose
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This tool is part of the Lake Management System project.
