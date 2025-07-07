# BigQuery Table Schema & Data Comparison Tool

A Python CLI tool for comparing BigQuery table schemas, row counts, and data records between two tables.

## Features

- **Schema Comparison**: Compare field definitions, types, and modes between two BigQuery tables
- **Row Count Analysis**: Get row counts for both tables to understand data volume differences
- **Data Record Comparison**: Heuristic comparison of actual data records using common join keys
- **Detailed Reporting**: Comprehensive report showing differences in field definitions and data

## Prerequisites

- Python 3.7+
- Google Cloud SDK installed and configured
- BigQuery API enabled
- Appropriate permissions to access the BigQuery tables

## Installation

1. Install the required dependencies:
```bash
pip install google-cloud-bigquery
```

2. Ensure you have authenticated with Google Cloud:
```bash
gcloud auth application-default login
```

## Usage

### Basic Usage

```bash
python main.py <table_a> <table_b> [--project <project_id>]
```

### Examples

Compare two tables in the same project:
```bash
python main.py my-project.dataset.table1 my-project.dataset.table2
```

Compare tables across different projects:
```bash
python main.py project-a.dataset.table1 project-b.dataset.table2
```

Specify a project ID explicitly:
```bash
python main.py dataset.table1 dataset.table2 --project my-project
```

## Output

The tool provides a comprehensive report including:

### Schema Analysis
- Fields that exist only in Table A
- Fields that exist only in Table B  
- Fields with different definitions (type/mode differences)

### Row Count Comparison
- Total row counts for both tables
- Visual indicators of data volume differences

### Data Record Comparison (Optional)
When prompted, the tool can perform heuristic data comparison:
- Records that exist only in Table A
- Records that exist only in Table B
- Records with mismatched data (same keys, different values)

## Example Output

```
================================================================================
📊 BigQuery Schema & Row Count Comparison Report
================================================================================
Table A: my-project.dataset.users_v1
Table B: my-project.dataset.users_v2

🧮 Row count:
  - my-project.dataset.users_v1: 1,234 rows
  - my-project.dataset.users_v2: 1,456 rows

🟨 Fields only in Table A:
  - legacy_field: ('STRING', 'NULLABLE')

🟦 Fields only in Table B:
  - new_feature_flag: ('BOOLEAN', 'NULLABLE')

🔁 Fields with different definitions:
  - user_id:
      Table A: ('INTEGER', 'REQUIRED')
      Table B: ('STRING', 'REQUIRED')
================================================================================

Do you want to compare data records? (y/n): y

🔎 Heuristic Data Comparison (Join on: user_id)
  ❗ ONLY_IN_A: user_id=12345
  ❗ MISMATCHED: user_id=67890
```

## Join Key Detection

The tool automatically detects potential join keys by:
1. Finding fields that exist in both tables
2. Ensuring field types match between tables
3. Excluding REPEATED fields (arrays)
4. Using the first valid join key for data comparison

## Error Handling

- Invalid table references will show clear error messages
- Missing permissions will be reported
- Network connectivity issues are handled gracefully

## Limitations

- Data comparison is heuristic and uses the first detected join key
- Large tables may have performance implications for data comparison
- Complex nested schemas may not be fully supported
- The tool samples up to 5 records per category for data comparison

## Contributing

Feel free to submit issues and enhancement requests!

## License

This tool is part of the Lake Management System project. 