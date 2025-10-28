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
Analyze complete dataset hierarchy with change tracking.

```bash
# Basic analysis
./lc dataset-hierarchy --project my-project-id

# Include views in analysis
./lc dataset-hierarchy --project my-project-id --include-views

# Compare with previous analysis
./lc dataset-hierarchy --project my-project-id --compare previous_analysis.json

# Custom output file
./lc dataset-hierarchy --project my-project-id --output my_analysis.json
```

**Features:**
- Complete dataset hierarchy analysis
- Table and view counts per dataset
- Row counts from metadata (no query execution)
- Change detection between runs
- Comprehensive JSON output for comparison
- Detailed change summary with additions, removals, and modifications

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
MAX_PARALLEL_WORKERS=10                       # Parallel processing limit
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
│   └── dataset_hierarchy.py      # Dataset hierarchy analysis module
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