
# BigQuery Table Comparison Script

This script compares tables between the `preprod` and `prod` GCP BigQuery projects and writes results to a text file and a BigQuery audit table.

## Requirements

- Python 3.7+
- `google-cloud-bigquery`
- `python-dotenv`

## Setup

1. Install required packages:

```bash
pip install google-cloud-bigquery python-dotenv
```

2. Update `.env` with your values.
3. Run the script:

```bash
python compare_tables.py
```

The comparison will be saved to `table_comparison.txt` and uploaded to BigQuery under `audit_dataset.table_between_envs`.
