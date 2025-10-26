# Lake Management System

A comprehensive solution for managing and maintaining Google BigQuery data lakes, with a focus on **column metadata management**, **environment similarity tracking**, and **table analysis**. This system provides both unified command-line tools for development and cloud-native automation for production environments.

## 🎯 Purpose

The Lake Management System addresses critical challenges in data lake operations:

1. **Column Metadata Management**: Automatically synchronizes column descriptions across BigQuery tables using centralized metadata governance
2. **Environment Similarity**: Tracks and compares table structures between different environments (dev, staging, prod) to ensure consistency
3. **Table Analysis**: Comprehensive tools for extracting table information, comparing schemas, and analyzing data differences
4. **Unified CLI Experience**: Single command-line interface for all utilities with modular architecture

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Google Cloud SDK (`gcloud`) configured
- BigQuery API enabled
- Appropriate IAM permissions in your GCP project

### Installation

1. **Clone and navigate to the app-cli directory:**
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

## 📁 Project Structure

```
lake-management-system/
├── app-cli/                          # Unified CLI tools
│   ├── lake_cli.py                   # Main CLI entry point
│   ├── lake-cli                       # Wrapper script (full name)
│   ├── lc                            # Short alias (recommended)
│   ├── modules/                      # Individual utility modules
│   │   ├── table_list.py             # Table extraction module
│   │   ├── schema_compare.py         # Schema comparison module
│   │   ├── table_compare.py          # Table comparison module
│   │   └── update_metadata.py        # Metadata update module
│   ├── requirements.txt              # Unified dependencies
│   ├── .env.example                  # Environment template
│   ├── install.sh                    # Installation script
│   ├── README.md                     # This file
│   ├── QUICK_REFERENCE.md            # Quick command reference
│   └── samples/                      # Sample data and setup scripts
│       └── update-metadata/           # Sample metadata setup
├── cloud-native/                     # Production-ready cloud automation
│   ├── update_column_descriptions.py # Core column update logic
│   ├── api_server.py                 # FastAPI server for Cloud Run
│   ├── Dockerfile                    # Container configuration
│   ├── requirements.txt              # Python dependencies
│   ├── main.tf                       # Terraform for Cloud Run deployment
│   ├── cloud_scheduler.tf            # Terraform for scheduled execution
│   ├── iam_permissions.tf            # Terraform for IAM setup
│   └── README.md                     # Cloud deployment documentation
└── README.md                         # This file
```

## 🛠️ Components

### 1. Column Metadata Management

**Problem**: Column descriptions in BigQuery tables often become outdated or inconsistent, making data discovery and governance difficult.

**Solution**: Centralized metadata management with automated synchronization.

**Features**:
- Updates column descriptions from a centralized metadata table
- Supports batch processing with rate limiting
- Comprehensive logging and audit trails
- Parallel processing for performance
- Change detection (only updates when descriptions differ)

**Implementation**:
- **CLI Tool** (`./lc update-metadata`): For development and manual runs
- **Cloud Service** (`cloud-native/`): Automated daily execution via Cloud Run and Cloud Scheduler

### 2. Environment Similarity Tracking

**Problem**: Data lake environments (dev, staging, prod) can drift apart, leading to inconsistencies and deployment issues.

**Solution**: Automated comparison and reporting of table structures across environments.

**Features**:
- Compares table existence between BigQuery projects
- Generates detailed reports (text file + BigQuery audit table)
- Tracks differences over time with timestamps
- Identifies tables missing in specific environments

**Implementation**:
- **CLI Tool** (`./lc table-compare`): Manual environment comparison

### 3. Table Analysis and Schema Comparison

**Problem**: Understanding table structures, schemas, and data differences across environments.

**Solution**: Comprehensive analysis tools for table metadata and schema comparison.

**Features**:
- Extract table information to CSV
- Compare schemas between tables
- Analyze data differences
- Heuristic join key detection

**Implementation**:
- **CLI Tools** (`./lc table-list`, `./lc schema-compare`): Table analysis and comparison

## 🔧 Configuration

### Environment Variables

Both CLI and cloud components use environment variables for configuration:

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

## 📊 Use Cases

### Column Metadata Management

- **Data Governance**: Ensure all columns have proper descriptions for data discovery
- **Compliance**: Maintain audit trails of metadata changes
- **Team Collaboration**: Centralized metadata management for large teams
- **Documentation**: Automatically keep BigQuery column descriptions up-to-date

### Environment Similarity

- **Deployment Validation**: Verify that all environments have the same table structure
- **Drift Detection**: Identify when environments become out of sync
- **Audit Compliance**: Track environment differences for compliance reporting
- **Release Management**: Ensure successful deployments across environments

### Table Analysis

- **Data Discovery**: Extract comprehensive table information for documentation
- **Schema Evolution**: Track schema changes over time
- **Data Quality**: Compare data between environments
- **Migration Planning**: Understand table structures before migrations

## 🌐 Cloud Deployment

For production environments, deploy the cloud-native version:

```bash
cd cloud-native

# Build and push Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/bq-column-updater

# Deploy with Terraform
terraform init
terraform apply \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="image_url=gcr.io/YOUR_PROJECT_ID/bq-column-updater" \
  -var="metadata_table=your_dataset.system_metadata" \
  -var="job_run_table=your_dataset.job_runs"
```

## 📈 Monitoring and Logging

- **Job Execution Logs**: All operations are logged to BigQuery for audit trails
- **Local Logging**: CLI tools support local log files for debugging (`--log` flag)
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Performance Metrics**: Execution time and statistics for optimization

## 🔐 Security

- Uses Google Cloud service accounts with minimal required permissions
- Environment variables for sensitive configuration
- Audit logging for all operations
- Rate limiting to prevent API quota exhaustion

## 🚀 Advanced Usage

### Custom Configuration

Create a `.env` file in the `app-cli` directory:

```bash
PROJECT_ID=your-project-id
METADATA_TABLE=governance_metadata.system_metadata
JOB_RUN_TABLE=governance_metadata.job_runs
SLEEP_MSECONDS=500
MAX_PARALLEL_WORKERS=10
```

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

## 🤝 Contributing

1. **Development Setup:**
```bash
cd app-cli
pip install -r requirements.txt
./lc --help  # Test the CLI
```

2. **Adding New Commands:**
   - Create new module in `modules/`
   - Add parser setup in `lake_cli.py`
   - Update documentation

3. **Testing:**
```bash
./test-unified-cli.sh  # Run all tests
```

## 📈 Roadmap

- [ ] Schema comparison enhancements (column types, constraints)
- [ ] Automated drift correction
- [ ] Integration with CI/CD pipelines
- [ ] Web-based dashboard for monitoring
- [ ] Support for additional cloud providers
- [ ] Data quality metrics and reporting
- [ ] Automated table documentation generation

## 📚 Additional Documentation

- [Quick Reference Guide](app-cli/QUICK_REFERENCE.md) - Command reference
- [Cloud Deployment Guide](cloud-native/README.md) - Production deployment
- [Sample Setup Guide](app-cli/samples/update-metadata/) - Getting started with samples

## 📄 License

This project is part of the Lake Management System. See individual component licenses for details.