# Lake Management System CLI - Quick Reference

## 🚀 Installation
```bash
cd app-cli
pip install -r requirements.txt
cp .env.example .env
gcloud auth application-default login
```

## 📋 Commands

### Table List
```bash
./lc table-list --dataset <dataset> [--project <project>] [--include-views] [--verbose] [--output <file>]
```

### Schema Compare
```bash
./lc schema-compare <table_a> <table_b> [--project <project>]
```

### Table Compare
```bash
./lc table-compare <table_a> <table_b> [--project <project>]
```

### Update Metadata
```bash
./lc update-metadata [--log]
```

### Dataset Hierarchy
```bash
./lc dataset-hierarchy --project <project> [--include-views] [--compare <file>] [--output <file>] [--format json|tree|both] [--max-tables N] [--bq-table <table>] [--batch-mgmt-table <table>] [--batch-id <id>] [--compare-latest] [--compare-batch-id <id>] [--compare-date <YYYY-MM-DD>]
```

## 🔧 Configuration (.env)
```bash
PROJECT_ID=your-project-id
METADATA_TABLE=governance_metadata.project_metadata
JOB_RUN_TABLE=governance_metadata.job_runs
SLEEP_MSECONDS=500
MAX_PARALLEL_WORKERS=10
```

## 📊 Examples
```bash
# List all tables in a dataset
./lc table-list --dataset my_dataset --include-views --verbose

# Compare schemas
./lc schema-compare dataset.table1 dataset.table2

# Compare data
./lc table-compare dataset.table1 dataset.table2

# Update column descriptions
./lc update-metadata --log

# Analyze dataset hierarchy (tree view)
./lc dataset-hierarchy --project my-project-id --format tree --max-tables 20

# Use batch management table (auto-generates batch_id like 29102025-0001)
./lc dataset-hierarchy --project my-project-id --batch-mgmt-table dataset.batch_management

# Save to BigQuery and compare with latest
./lc dataset-hierarchy --project my-project-id --bq-table dataset.hierarchy_analysis --compare-latest

# Compare with specific batch_id
./lc dataset-hierarchy --project my-project-id --bq-table dataset.hierarchy_analysis --compare-batch-id batch_20241027_120000

# Combined: batch management + BigQuery persistence
./lc dataset-hierarchy --project my-project-id --batch-mgmt-table dataset.batch_management --bq-table dataset.hierarchy_analysis
```

## 🆘 Help
```bash
./lc --help
./lc <command> --help
```
