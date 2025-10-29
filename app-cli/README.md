# Lake Management System - Unified CLI

A unified command-line interface for all BigQuery utilities in the Lake Management System. This CLI provides a single entry point for multiple utilities while maintaining modularity for development.

## 🚀 Quick Start

### Installation

1. **Navigate to the app-cli directory:**
```bash
cd app-cli
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up authentication:**
```bash
gcloud auth application-default login
```

4. **Configure environment (optional):**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Make scripts executable:**
```bash
chmod +x *.sh
chmod +x lake_cli.py
chmod +x lake-cli
chmod +x lc
```

### Basic Usage

```bash
# Run with short alias (recommended)
./lc --help

# Or with full name
./lake-cli --help

# Or run the Python script directly
./lake_cli.py --help
```

## 📋 Available Commands

### 1. Table List (`table-list`)
Extract table information from BigQuery datasets to CSV.

```bash
# Basic usage
./lc table-list --dataset my_dataset

# With specific project and views
./lc table-list --dataset my_dataset --project my-project-id --include-views --verbose

# Custom output file
./lc table-list --dataset my_dataset --output tables.csv
```

**Output columns:**
- `schema` - Dataset name
- `object_type` - BASE TABLE or VIEW
- `name` - Table/view name
- `primary_keys` - Whether table has primary keys
- `row_count` - Number of rows

**Examples:**
```bash
# Extract all tables from a dataset
./lc table-list --dataset governance_metadata

# Include views and save to custom file
./lc table-list --dataset my_dataset --include-views --output all_objects.csv

# Verbose output with specific project
./lc table-list --dataset my_dataset --project my-project-id --verbose
```

### 2. Schema Compare (`schema-compare`)
Compare schemas between two BigQuery tables.

```bash
# Compare tables in same project
./lc schema-compare dataset.table1 dataset.table2

# Compare tables across projects
./lc schema-compare project1.dataset.table1 project2.dataset.table2

# With specific project
./lc schema-compare table1 table2 --project my-project-id
```

**Features:**
- Field-by-field schema comparison
- Row count comparison
- Optional data record comparison
- Heuristic join key detection

**Examples:**
```bash
# Compare two tables
./lc schema-compare raw_data.customers staging.customers

# Compare across projects
./lc schema-compare dev-project.dataset.table prod-project.dataset.table

# Compare with explicit project
./lc schema-compare dataset.table1 dataset.table2 --project my-project-id
```

### 3. Table Compare (`table-compare`)
Compare data between two BigQuery tables.

```bash
# Compare table data
./lc table-compare dataset.table1 dataset.table2

# Compare across projects
./lc table-compare project1.dataset.table1 project2.dataset.table2
```

**Features:**
- Environment comparison (preprod vs prod)
- Detailed reporting (text file + BigQuery audit table)
- Tracks differences over time with timestamps
- Identifies tables missing in specific environments

**Examples:**
```bash
# Compare tables between environments
./lc table-compare preprod.dataset.table1 prod.dataset.table1

# Compare specific tables
./lc table-compare dev-project.dataset.users prod-project.dataset.users
```

### 4. Update Metadata (`update-metadata`)
Update column descriptions from metadata table.

```bash
# Basic usage
./lc update-metadata

# With local logging
./lc update-metadata --log
```

**Features:**
- Updates column descriptions from centralized metadata table
- Supports batch processing with rate limiting
- Comprehensive logging and audit trails
- Parallel processing for performance
- Change detection (only updates when descriptions differ)

### 5. Dataset Hierarchy (`dataset-hierarchy`)
Analyze complete dataset hierarchy with change tracking. Supports JSON output and a human-friendly tree view.

```bash
# Basic analysis (JSON output)
./lc dataset-hierarchy --project my-project-id --format json

# Include views in analysis
./lc dataset-hierarchy --project my-project-id --include-views

# Human tree view (no file needed)
./lc dataset-hierarchy --project my-project-id --format tree

# Limit number of tables shown per dataset in tree
./lc dataset-hierarchy --project my-project-id --format tree --max-tables 20

# Compare with previous analysis (JSON)
./lc dataset-hierarchy --project my-project-id --compare previous_analysis.json --format both

# Custom JSON output file
./lc dataset-hierarchy --project my-project-id --format json --output my_analysis.json
```

**Features:**
- Complete dataset hierarchy analysis
- Table and view counts per dataset
- Row counts from metadata (no query execution)
- Change detection between runs
- Comprehensive JSON output for comparison
- Detailed change summary with additions, removals, and modifications
- **Parallel processing** with configurable workers for faster analysis
- **BigQuery table persistence** with LDTS and batch_id tracking
- **Automatic comparison** with previous runs from BigQuery
- **Batch Management Table** with automatic batch_id generation (DDMMYYYY-NNNN format)
- **Data size tracking** (total bytes/GB)

**Batch Management:**
```bash
# Use batch management table (auto-generates DDMMYYYY-NNNN batch_id like 29102025-0001)
./lc dataset-hierarchy --project my-project-id --batch-mgmt-table dataset.batch_management

# Combine with BigQuery persistence
./lc dataset-hierarchy --project my-project-id --batch-mgmt-table dataset.batch_management --bq-table dataset.hierarchy_analysis

# Custom batch_id (overrides auto-generation)
./lc dataset-hierarchy --project my-project-id --batch-mgmt-table dataset.batch_management --batch-id 29102025-0050
```

**BigQuery Persistence:**
The tool automatically optimizes BigQuery writes based on data size:
- **Small hierarchies (<5MB)**: Uses fast streaming inserts
- **Large hierarchies (>5MB)**: Uses reliable batch load jobs

```bash
# Save to BigQuery table (auto batch_id)
./lc dataset-hierarchy --project my-project-id --bq-table dataset.hierarchy_analysis

# Save with custom batch_id
./lc dataset-hierarchy --project my-project-id --bq-table dataset.hierarchy_analysis --batch-id my_batch_001

# Compare with latest run from BigQuery (automatic when --bq-table is used)
./lc dataset-hierarchy --project my-project-id --bq-table dataset.hierarchy_analysis --compare-latest

# Compare with specific batch_id
./lc dataset-hierarchy --project my-project-id --bq-table dataset.hierarchy_analysis --compare-batch-id batch_20241027_120000

# Compare with specific date
./lc dataset-hierarchy --project my-project-id --bq-table dataset.hierarchy_analysis --compare-date 2024-10-27

# Combine BigQuery with tree view
./lc dataset-hierarchy --project my-project-id --bq-table dataset.hierarchy_analysis --format both --compare-latest
```

### 6. BigQuery Alerts (`bq-alerts`)

Detect significant table size changes by comparing day-over-day data from the batch_management table. Alerts are written to BigQuery and can be monitored via GCP Cloud Monitoring.

```bash
# Basic alert detection
./lc bq-alerts --project my-project-id --batch-mgmt-table dataset.batch_management

# Custom alerts table
./lc bq-alerts --project my-project-id --batch-mgmt-table dataset.batch_management --alerts-table dataset.custom_alerts

# Using environment variables
# Set BATCH_MGMT_TABLE and ALERTS_TABLE in .env, then:
./lc bq-alerts --project my-project-id
```

**Features:**
- Day-over-day comparison of batch_management data
- Configurable alert thresholds (percentage and absolute)
- Severity levels: CRITICAL, HIGH, MEDIUM, LOW
- Multiple metrics: total_bytes, num_tables, num_datasets, total_rows
- BigQuery alerts table with partitioning and clustering
- Integration with GCP Cloud Monitoring (see `alerts/` directory)

**Alert Thresholds:**
- Default: >20% increase OR >10 GB increase
- Customizable via environment variables (see `.env.example`)
- Severity based on thresholds:
  - **CRITICAL**: >100% OR >50 GB
  - **HIGH**: >50% OR >20 GB
  - **MEDIUM**: >20% OR >10 GB
  - **LOW**: <20% AND <10 GB

**Workflow:**
1. Run `dataset-hierarchy` daily to populate `batch_management` table
2. Run `bq-alerts` to detect changes and write alerts
3. Configure Cloud Monitoring policies (see `alerts/README.md`)
4. Receive notifications via email, Slack, or other channels

**Examples:**
```bash
# Complete daily workflow
./lc dataset-hierarchy --project my-project-id --batch-mgmt-table dataset.batch_management --bq-table dataset.hierarchy_analysis
./lc bq-alerts --project my-project-id --batch-mgmt-table dataset.batch_management

# Query alerts
# SELECT * FROM `governance_metadata.size_alerts` WHERE status='PENDING' ORDER BY alert_timestamp DESC;
```

**Examples:**
```bash
# Update metadata with logging
./lc update-metadata --log

# Basic metadata update
./lc update-metadata
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `app-cli` directory:

```bash
# Required
PROJECT_ID=your-project-id                    # Your Google Cloud Project ID
METADATA_TABLE=governance_metadata.system_metadata  # Metadata table path
JOB_RUN_TABLE=governance_metadata.job_runs     # Job logging table path

# Optional
SLEEP_MSECONDS=500                            # Rate limiting delay
MAX_PARALLEL_WORKERS=10                       # Parallel processing limit (for dataset-hierarchy and update-metadata)
BATCH_MGMT_TABLE=governance_metadata.batch_management  # Batch management table (for dataset-hierarchy)
```

### Sample Setup

The `samples/update-metadata/` directory contains scripts to set up the required tables:

1. **Create sample tables:**
```bash
cd samples/update-metadata
chmod +x create_tables.sh
./create_tables.sh
```

2. **Load sample metadata:**
The script automatically loads sample metadata from `sample_metadata.csv`

## 📁 Project Structure

```
app-cli/
├── lake_cli.py                   # Main CLI entry point
├── lake-cli                       # Wrapper script (full name)
├── lc                            # Short alias (recommended)
├── modules/                      # Individual utility modules
│   ├── __init__.py               # Package initialization
│   ├── table_list.py             # Table extraction module
│   ├── schema_compare.py         # Schema comparison module
│   ├── table_compare.py          # Table comparison module
│   ├── update_metadata.py        # Metadata update module
│   ├── dataset_hierarchy.py      # Dataset hierarchy analysis module
│   └── bq_alerts.py              # BigQuery alerts detection module
├── requirements.txt              # Unified dependencies
├── .env.example                  # Environment template
├── install.sh                    # Installation script
├── README.md                     # This file
├── QUICK_REFERENCE.md            # Quick command reference
└── samples/                      # Sample data and setup scripts
    └── update-metadata/           # Sample metadata setup
        ├── create_tables.sh       # Setup script
        ├── create_tables.sql      # SQL for sample tables
        └── sample_metadata.csv    # Sample metadata
```

## 🚀 Advanced Usage

### Batch Operations

```bash
# Extract multiple datasets
for dataset in dataset1 dataset2 dataset3; do
    ./lc table-list --dataset $dataset --output ${dataset}_tables.csv
done

# Compare multiple table pairs
./lc schema-compare prod.dataset.table1 dev.dataset.table1
./lc schema-compare prod.dataset.table2 dev.dataset.table2
```

### Integration with CI/CD

```bash
# In your CI/CD pipeline
./lc table-compare staging.dataset.table1 prod.dataset.table1
if [ $? -ne 0 ]; then
    echo "Environment drift detected!"
    exit 1
fi
```

### Custom Output Formats

```bash
# Generate timestamped output files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
./lc table-list --dataset my_dataset --output tables_${TIMESTAMP}.csv
```

### Performance Optimization

**Parallel Processing for Dataset Hierarchy:**
The `dataset-hierarchy` command uses parallel processing to analyze multiple datasets and tables simultaneously. Configure the number of workers:

```bash
# In .env file
MAX_PARALLEL_WORKERS=20  # Increase for faster analysis (default: 10)

# Recommended values:
# - Small projects (< 10 datasets): 5-10 workers
# - Medium projects (10-50 datasets): 10-20 workers
# - Large projects (50+ datasets): 20-50 workers
```

**Note:** Higher worker counts improve speed but increase BigQuery API usage. Monitor your quota limits.

**BigQuery Write Optimization:**
The tool automatically optimizes BigQuery writes based on data size:
- **Streaming Inserts**: Used for small hierarchies (<5MB) - faster, lower latency
- **Batch Load Jobs**: Used for large hierarchies (>5MB) - more reliable, handles large payloads
- **Automatic Detection**: No configuration needed - the tool automatically chooses the best method

This ensures optimal performance for both small and large projects while respecting BigQuery API limits.

## 🧪 Testing

### Run Tests

```bash
# Test all commands
./test-unified-cli.sh

# Test specific command
./lc table-list --help
./lc schema-compare --help
./lc table-compare --help
./lc update-metadata --help
```

### Sample Data Testing

```bash
# Set up sample data
cd samples/update-metadata
./create_tables.sh

# Test with sample data
cd ../..
./lc update-metadata --log
```

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Error:**
```bash
gcloud auth application-default login
```

2. **Permission Denied:**
```bash
# Check your project permissions
gcloud projects get-iam-policy your-project-id
```

3. **Module Import Error:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

4. **Environment Variables:**
```bash
# Check your .env file
cat .env
```

### Debug Mode

```bash
# Enable verbose logging
./lc table-list --dataset my_dataset --verbose

# Enable local logging
./lc update-metadata --log
```

## 🤝 Development

### Adding New Commands

1. **Create new module:**
```bash
# Create new module in modules/
touch modules/new_command.py
```

2. **Add parser setup in `lake_cli.py`:**
```python
def setup_new_command_parser(subparsers):
    parser = subparsers.add_parser(
        "new-command",
        help="Description of new command"
    )
    parser.add_argument("--option", help="Option description")
    return parser
```

3. **Add command handler:**
```python
elif args.command == "new-command":
    from modules.new_command import main as new_command_main
    return new_command_main(args)
```

### Testing New Commands

```bash
# Test new command
./lc new-command --help
./lc new-command --option value
```

## 📚 Additional Resources

- [Quick Reference Guide](QUICK_REFERENCE.md) - Command reference
- [Main Project README](../README.md) - Overall project documentation
- [Cloud Deployment Guide](../cloud-native/README.md) - Production deployment

## 📄 License

This project is part of the Lake Management System. See individual component licenses for details.